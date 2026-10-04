import { Component, OnInit, OnDestroy, HostListener, Inject } from '@angular/core';
import { CommonModule, DOCUMENT } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms'; // IMPORTANTE: Necessário para o [(ngModel)] da busca
import { ApiService } from '../../api.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule], // Adicionado FormsModule
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  // --- ESTADOS ---
  cameras: any[] = [];
  displaySlots: any[] = [];
  fullscreenCameraId: number | null = null;
  isFullscreen = false;
  searchTerm: string = ''; // Variável para a busca
  
  // Subs
  pollingSub!: Subscription;
  clockSub!: Subscription;

  // --- DADOS DO FOOTER ---
  systemTime = new Date();
  serverLatency = '12ms'; 
  systemVersion = 'v3.5.2 Enterprise';

  // --- CONFIGURAÇÃO DA GRELHA ---
  gridOptions = [1, 4, 9, 16, 25, 36, 49, 64]; 
  selectedGridSize = 4; // Padrão inicial para fullscreen

  constructor(
    public apiService: ApiService, 
    private router: Router,
    @Inject(DOCUMENT) private document: Document
  ) { }

  ngOnInit(): void {
    this.updateGrid();
    this.loadCameras();
    
    // Atualiza status das câmaras a cada 2s
    this.pollingSub = interval(2000).subscribe(() => this.updateCameraStatus());
    
    // Atualiza o relógio do Footer a cada 1s
    this.clockSub = interval(1000).subscribe(() => {
        this.systemTime = new Date();
        this.serverLatency = Math.floor(Math.random() * (20 - 5) + 5) + 'ms';
    });
  }

  loadCameras() {
    this.apiService.getCameras().subscribe((data: any[]) => {
      this.cameras = data.map(cam => ({
        ...cam,
        hasAlert: false,
        peopleCount: 0,
        lastEvent: null
      }));
      this.updateGrid();
    });
  }

  // --- LÓGICA PRINCIPAL DE VISUALIZAÇÃO ---
  updateGrid() {
    this.displaySlots = [];

    // 1. Filtra as câmaras (Busca por nome ou IP)
    let filteredCameras = this.cameras;
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase();
      filteredCameras = this.cameras.filter(cam => 
        cam.name.toLowerCase().includes(term) || 
        (cam.ip_address && cam.ip_address.includes(term))
      );
    }

    // 2. Define o limite de exibição
    let limit: number;

    if (this.isFullscreen) {
      // MODO TELA CHEIA (VMS):
      // Respeita estritamente o botão selecionado (ex: 4, 16, 64)
      limit = this.selectedGridSize;
    } else {
      // MODO DASHBOARD (NORMAL):
      // Mostra TODAS as câmaras disponíveis (sem limite artificial)
      limit = filteredCameras.length;
    }

    // 3. Monta os Slots
    for (let i = 0; i < limit; i++) {
      if (i < filteredCameras.length) {
        // Slot com Câmara Real
        this.displaySlots.push({ type: 'camera', data: filteredCameras[i] });
      } else {
        // Slot Vazio (Cinza)
        // Só adicionamos slots vazios se estivermos em TELA CHEIA para manter a matriz quadrada perfeita.
        if (this.isFullscreen) {
           this.displaySlots.push({ type: 'empty', id: i });
        }
      }
    }
  }

  // Chamado quando o usuário digita na busca
  onSearch(term: string) {
    this.searchTerm = term;
    this.updateGrid();
  }

  setGridSize(size: number) {
    this.selectedGridSize = size;
    this.updateGrid();
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
          if (diffSeconds < 60) cam.lastEvent = last;
          
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
onPtzAction(cameraId: number, direction: string, action: 'start' | 'stop', event: Event) {
    event.stopPropagation(); // Impede que o clique abra a câmara em ecrã inteiro
    
    this.apiService.controlPTZ(cameraId, direction, action).subscribe({
      next: () => console.log(`PTZ: ${direction} -> ${action}`),
      error: (err) => console.error('Erro ao mover câmara:', err)
    });
  }
 // --- FULLSCREEN INDIVIDUAL ---
  // --- DETEÇÃO DE MUDANÇA DE TELA (CORRIGIDO) ---
  @HostListener('document:fullscreenchange', ['$event'])
  onFullScreenChange() {
    const fsElem = this.document.fullscreenElement;
    
    // CASO 1: É uma câmara individual
    if (fsElem && fsElem.id.startsWith('camera-card-')) {
      const idPart = fsElem.id.split('-')[2]; 
      this.fullscreenCameraId = +idPart;
      
      // IMPORTANTE: NÃO chamamos updateGrid() aqui.
      // Se chamarmos, o Angular destroi o card e a tela cheia fecha sozinha.
      // Mantemos o isFullscreen false porque não é o modo VMS/Matrix.
      this.isFullscreen = false; 
    } 
    
    // CASO 2: É o modo VMS (Hub/Geral)
    else if (fsElem) {
      this.isFullscreen = true; 
      this.fullscreenCameraId = null;
      this.updateGrid(); // Aqui sim, recalculamos para mostrar a matriz
    } 
    
    // CASO 3: Saiu da tela cheia (Voltou ao normal)
    else {
      this.isFullscreen = false;
      this.fullscreenCameraId = null;
      this.updateGrid(); // Recalculamos para voltar à galeria responsiva
    }
  }

  // --- ATIVAR TELA CHEIA INDIVIDUAL (SIMPLIFICADO) ---
  toggleSingleCameraFullscreen(cameraId: number) {
    const elementId = `camera-card-${cameraId}`;
    const elem = this.document.getElementById(elementId);
    
    if (elem) {
      // Se já estiver em fullscreen neste elemento, sai.
      if (this.document.fullscreenElement === elem) {
        this.document.exitFullscreen();
      } else {
        // Tenta entrar em fullscreen
        elem.requestFullscreen().catch(err => {
          console.error("Erro ao entrar em tela cheia:", err);
        });
      }
    }
  }

  // Modo VMS (Monitorização Geral)
  toggleFullscreen() {
    const elem = this.document.documentElement;
    if (!this.document.fullscreenElement) {
      elem.requestFullscreen().catch(err => console.error(err));
    } else {
      this.document.exitFullscreen();
    }
  }

 

  // --- AÇÕES ---
  async editCamera(id: number, event: Event) {
    event.stopPropagation();
    if (this.document.fullscreenElement) await this.document.exitFullscreen();
    this.router.navigate(['/camera-edit', id]);
  }

  async deleteCamera(id: number, event: Event) {
    event.stopPropagation();
    if(confirm('Tem a certeza que deseja remover esta câmara?')) {
      if (this.document.fullscreenElement) await this.document.exitFullscreen();
      this.apiService.deleteCamera(id).subscribe(() => {
        this.cameras = this.cameras.filter(c => c.id !== id);
        this.updateGrid();
      });
    }
  }

  goToDetail(id: number) {
    if (!this.fullscreenCameraId) {
        this.router.navigate(['/camera', id]);
    }
  }

  formatEventLabel(event: any): string {
    if (!event) return '';
    if (event.event_type === 'Reconhecimento Facial') {
        try { return JSON.parse(event.event_data).nome || 'Face'; } catch(e) { return 'Face'; }
    }
    return event.event_type;
  }

 resetView() {
    // 1. Se estiver em Fullscreen (qualquer tipo), SAI.
    if (this.document.fullscreenElement) {
      this.document.exitFullscreen().catch(err => console.error(err));
    }

    // 2. Opcional: Limpa a busca e volta ao padrão
    this.searchTerm = '';
    this.selectedGridSize = 4;
    
    // 3. Atualiza a grelha para o estado inicial
    this.updateGrid();
  }

  // --- CICLO DE VIDA ---
  ngOnDestroy() {
    // Garante que sai do fullscreen se o componente for destruído (mudar de rota)
    if (this.document.fullscreenElement) {
       this.document.exitFullscreen().catch(() => {});
    }

    if (this.pollingSub) this.pollingSub.unsubscribe();
    if (this.clockSub) this.clockSub.unsubscribe();
  }
}
