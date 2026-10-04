import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-guarita',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './guarita.component.html',
  styleUrl: './guarita.component.scss'
})
export class GuaritaComponent implements OnInit, OnDestroy {

  currentView: 'queue' | 'visitors' = 'queue';

  alertQueue: any[] = [];
  visitors: any[] = [];
  devices: any[] = [];
  selectedAlert: any = null;
  selectedDeviceId: number | undefined = undefined;
  showVisitorForm = false;
  loading = false;

  newVisitor = {
    name: '', cpf: '', host: '', destination: '',
    valid_until: '', status: 'approved', notes: ''
  };

  private eventSource: EventSource | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadQueue();
    this.loadVisitors();
    this.api.getAccessDevices().subscribe({ next: d => this.devices = d });
    this.connectSSE();
  }

  ngOnDestroy(): void {
    this.eventSource?.close();
  }

  connectSSE(): void {
    this.eventSource = new EventSource(this.api.getGuaritaAlertsUrl());
    this.eventSource.onmessage = (event) => {
      try {
        const alertItem = JSON.parse(event.data);
        if (!this.alertQueue.find(a => a.event_id === alertItem.event_id)) {
          this.alertQueue.unshift(alertItem);
        }
      } catch { /* ignora frames malformados */ }
    };
  }

  loadQueue(): void {
    this.loading = true;
    this.api.getGuaritaQueue().subscribe({
      next: q => { this.alertQueue = q; this.loading = false; },
      error: () => this.loading = false
    });
  }

  loadVisitors(): void {
    this.api.getGuaritaVisitors().subscribe({ next: v => this.visitors = v });
  }

  switchView(view: 'queue' | 'visitors'): void { this.currentView = view; }

  selectAlert(alertItem: any): void { this.selectedAlert = alertItem; this.selectedDeviceId = undefined; }
  clearSelected(): void { this.selectedAlert = null; this.selectedDeviceId = undefined; }

  getFaceUrl(path: string | null): string | null {
    return path ? this.api.getFaceImageUrl(path) : null;
  }

  approve(alertItem: any, deviceId?: number): void {
    this.api.approveUnknownFace(alertItem.event_id, deviceId, 'Aprovado pelo operador').subscribe({
      next: (r: any) => {
        const msg = r.gate_triggered ? 'Entrada aprovada — portão acionado' : 'Entrada aprovada';
        window.alert(msg);
        this.removeFromQueue(alertItem.event_id);
        this.clearSelected();
      },
      error: () => window.alert('Erro ao aprovar')
    });
  }

  deny(alertItem: any): void {
    this.api.denyUnknownFace(alertItem.event_id, 'Negado pelo operador').subscribe({
      next: () => {
        this.removeFromQueue(alertItem.event_id);
        this.clearSelected();
      },
      error: () => window.alert('Erro ao negar')
    });
  }

  private removeFromQueue(eventId: number): void {
    this.alertQueue = this.alertQueue.filter(a => a.event_id !== eventId);
  }

  openVisitorForm(): void {
    this.newVisitor = { name: '', cpf: '', host: '', destination: '', valid_until: '', status: 'approved', notes: '' };
    this.showVisitorForm = true;
  }

  closeVisitorForm(): void { this.showVisitorForm = false; }

  saveVisitor(): void {
    this.api.preRegisterVisitor(this.newVisitor).subscribe({
      next: () => { this.closeVisitorForm(); this.loadVisitors(); },
      error: () => window.alert('Erro ao cadastrar visitante')
    });
  }

  approveVisitor(v: any): void {
    this.api.approveVisitor(v.id).subscribe({ next: () => this.loadVisitors() });
  }

  denyVisitor(v: any): void {
    this.api.denyVisitor(v.id).subscribe({ next: () => this.loadVisitors() });
  }
}
