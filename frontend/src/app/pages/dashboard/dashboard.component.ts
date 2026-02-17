import { Component, OnInit, OnDestroy, HostListener, Inject } from '@angular/core';
import { DOCUMENT, CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../api.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  fullscreenCameraId: number | null = null;
  cameras: any[] = [];
  isFullscreen = false;
  pollingSub!: Subscription;

  constructor(
    private apiService: ApiService, 
    private router: Router,
    @Inject(DOCUMENT) private document: Document
  ) { }

  ngOnInit(): void {
    this.loadCameras();
    this.pollingSub = interval(2000).subscribe(() => this.updateCameraStatus());
  }

  // --- LÓGICA DE TOGGLE (ALTERNAR) ---
  toggleSingleCameraFullscreen(cameraId: number) {
    const elementId = `camera-card-${cameraId}`;
    const elem = this.document.getElementById(elementId);

    // Se esta câmara JÁ está em fullscreen, SAIMOS.
    if (this.fullscreenCameraId === cameraId) {
      this.document.exitFullscreen();
    } 
    // Senão, ENTRAMOS em fullscreen.
    else if (elem) {
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      }
    }
  }

  // (Apaguei a função openSingleCameraFullscreen pois já não é usada)

  // --- DETETA MUDANÇAS NO ECRÃ ---
  @HostListener('document:fullscreenchange', ['$event'])
  onFullScreenChange() {
    const fsElem = this.document.fullscreenElement;

    if (fsElem && fsElem.id.startsWith('camera-card-')) {
      const idPart = fsElem.id.split('-')[2]; 
      this.fullscreenCameraId = +idPart;
      this.isFullscreen = false; 
    } 
    else if (fsElem && fsElem.classList.contains('dashboard-container')) {
      this.isFullscreen = true;
      this.fullscreenCameraId = null;
    } 
    else {
      this.isFullscreen = false;
      this.fullscreenCameraId = null;
    }
  }

  loadCameras() {
    this.apiService.getCameras().subscribe((data: any[]) => {
      this.cameras = data.map(cam => ({
        ...cam,
        hasAlert: false,
        peopleCount: 0,
        lastEvent: null
      }));
      this.updateCameraStatus();
    });
  }

  updateCameraStatus() {
    this.apiService.getAllEvents().subscribe(events => {
      const now = new Date();
      this.cameras.forEach(cam => {
        const camEvents = events.filter((e: any) => e.camera_id === cam.id);
        if (camEvents.length > 0) {
          const last = camEvents[0];
          const diffSeconds = (now.getTime() - new Date(last.timestamp).getTime()) / 1000;
          cam.hasAlert = diffSeconds < 10;
          if (diffSeconds < 30) cam.lastEvent = last;
          
          try {
            if (last.event_type === 'Contagem de Pessoas') {
               const data = JSON.parse(last.event_data);
               if (data.total) cam.peopleCount = data.total;
            }
          } catch(e) {}
        }
      });
    });
  }

  getVideoUrl(id: number) {
    return this.apiService.getVideoFeedUrl(id);
  }

  // --- [CORREÇÃO] EDITA COM SEGURANÇA ---
  async editCamera(id: number, event: Event) {
    event.stopPropagation();
    
    // Se estiver em fullscreen, SAI PRIMEIRO
    if (this.document.fullscreenElement) {
      await this.document.exitFullscreen();
    }
    
    this.router.navigate(['/camera-edit', id]);
  }

  goToDetail(id: number) {
    if (!this.document.fullscreenElement) {
        this.router.navigate(['/camera', id]);
    }
  }

  // --- [CORREÇÃO] APAGA COM SEGURANÇA ---
  async deleteCamera(id: number, event: Event) {
    event.stopPropagation();

    // Se estiver em fullscreen, SAI PRIMEIRO
    if (this.document.fullscreenElement) {
      await this.document.exitFullscreen();
    }

    if(confirm('Tem a certeza?')) {
      this.apiService.deleteCamera(id).subscribe(() => {
        this.cameras = this.cameras.filter(c => c.id !== id);
      });
    }
  }

  toggleFullscreen() {
    const elem = this.document.documentElement;
    if (!this.document.fullscreenElement) {
      elem.requestFullscreen().catch(err => {
        console.error(`Erro ao ativar tela cheia: ${err.message}`);
      });
    } else {
      this.document.exitFullscreen();
    }
  }

  formatEventLabel(event: any): string {
    if (!event) return '';
    if (event.event_type === 'Reconhecimento Facial') {
        try {
            const data = JSON.parse(event.event_data);
            return data.nome || 'Face';
        } catch(e) { return 'Face'; }
    }
    return event.event_type;
  }

  ngOnDestroy() {
    if (this.pollingSub) this.pollingSub.unsubscribe();
  }
}