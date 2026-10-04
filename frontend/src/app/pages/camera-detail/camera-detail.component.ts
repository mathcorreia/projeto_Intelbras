import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../api.service';
import { timer } from 'rxjs';

@Component({
  selector: 'app-camera-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './camera-detail.component.html',
  styleUrls: ['./camera-detail.component.scss']
})
export class CameraDetailComponent implements OnInit {
  camera: any = null;
  events: any[] = [];
  videoFeedUrl: string | null = null;
  peopleCount: number = 0; 
  speakerVolume: number = 50;
  isSavingVolume: boolean = false;
  audioEnabled: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) { }

  ngOnInit(): void {
    const cameraId = this.route.snapshot.paramMap.get('id');
    if (!cameraId) return;

    const id = parseInt(cameraId, 10);
    
    // 1. Carrega dados da câmara
    this.apiService.readCamera(id).subscribe((data: any) => {
      this.camera = data;
      
      // Se for NVR, Intelbras ou Mibo, carrega definições de áudio
      if (this.camera.camera_type === 'mibo' || this.camera.camera_type === 'intelbras') {
         this.loadDeviceSettings(id);
      }
    });
    
    // 2. Feed de Vídeo
    this.videoFeedUrl = this.apiService.getVideoFeedUrl(id);

    // 3. Atualiza Eventos
    timer(0, 5000).subscribe(() => {
      this.apiService.getEventsForCamera(id).subscribe((eventsData: any[]) => {
        
        const processedEvents: any[] = []; 

        eventsData.forEach(event => {
          if (event.event_type === 'Contagem de Pessoas') {
            try {
              const data = JSON.parse(event.event_data);
              this.peopleCount = data.total; 
            } catch(e) {}
          } 
          else {
            if (event.event_data) {
              try {
                event.parsed_data = JSON.parse(event.event_data);
              } catch (e) { event.parsed_data = {}; }
            }
            processedEvents.push(event); 
          }
        });

        this.events = processedEvents; 
      });
    });
  }

  // ==========================================
  // HARDWARE (ÁUDIO E PTZ)
  // ==========================================

  loadDeviceSettings(id: number) {
    this.apiService.getAudioConfig(id).subscribe({
      next: (res: any) => console.log('Configs de Áudio Recebidas:', res),
      error: (err: any) => console.error("Erro ao carregar áudio", err)
    });
  }
onVolumeInput(event: any) {
    this.speakerVolume = event.target.value;
  }

  // Envia para a câmara APENAS quando largas a barra
  onVolumeChange(event: any) {
    this.speakerVolume = event.target.value;
    if (!this.camera) return;
    
    // Envia o volume para o backend
    this.apiService.setAudioVolume(this.camera.id, this.speakerVolume).subscribe({
      next: () => console.log(`Volume atualizado: ${this.speakerVolume}%`),
      error: (err: any) => console.error('Erro ao ajustar volume:', err)
    });
  }

  // Lógica do botão Liga/Desliga
  toggleAudioAction() {
    this.audioEnabled = !this.audioEnabled; 
    if (!this.camera) return;

    this.apiService.toggleAudio(this.camera.id, this.audioEnabled).subscribe({
      next: (res: any) => {
        // Verifica se a câmara aceitou o comando ou se bloqueou (Mibo)
        if (res.success === false) {
           alert("Aviso: Esta câmara Mibo não permite que o áudio seja controlado por fora da app oficial.");
           this.audioEnabled = !this.audioEnabled; // Reverte visualmente o switch
        } else {
           console.log(`Áudio ${this.audioEnabled ? 'Ligado' : 'Desligado'}`);
        }
      },
      error: (err: any) => {
        console.error('Erro de conexão:', err);
        this.audioEnabled = !this.audioEnabled; 
      }
    });
  }

  

  onPtzAction(direction: string, action: 'start' | 'stop', event: Event) {
    event.preventDefault(); 
    if (!this.camera) return;
    
    this.apiService.controlPTZ(this.camera.id, direction, action).subscribe({
      next: (res: any) => console.log(`Comando PTZ ${direction} enviado.`),
      error: (err: any) => console.error('Erro ao enviar PTZ:', err)
    });
  }

  // ==========================================
  // NAVEGAÇÃO
  // ==========================================

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}