import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-gate-management',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './gate-management.component.html',
  styleUrl: './gate-management.component.scss'
})
export class GateManagementComponent implements OnInit {

  currentView: 'live' | 'database' = 'live';
  showGateForm = false;
  isEditMode = false;
  loading = false;

  gates: any[] = [];
  liveLogs: any[] = [];

  defaultGate = { name: '', brand: 'ppa', ip: '', port: 80, pulse_time: 1, location: '', username: '', password: '' };
  newGate: any = { ...this.defaultGate };

  constructor(private api: ApiService) {}

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading = true;
    this.api.getGates().subscribe({
      next: g => { this.gates = g; this.loading = false; },
      error: () => this.loading = false
    });
    this.api.getAccessLogs(undefined, undefined, 30).subscribe({
      next: logs => this.liveLogs = logs
    });
  }

  switchView(view: 'live' | 'database'): void { this.currentView = view; }

  triggerGate(gate: any): void {
    this.api.triggerGate(gate.id).subscribe({
      next: (r: any) => {
        alert(r.message);
        if (r.success) gate.status = 'moving';
      },
      error: () => alert('Falha ao acionar portão')
    });
  }

  refreshStatus(gate: any): void {
    this.api.getGateStatus(gate.id).subscribe({
      next: (r: any) => gate.status = r.status
    });
  }

  openGateForm(): void {
    this.isEditMode = false;
    this.newGate = { ...this.defaultGate };
    this.showGateForm = true;
  }

  editGate(gate: any): void {
    this.isEditMode = true;
    this.newGate = { ...gate };
    this.showGateForm = true;
  }

  closeGateForm(): void { this.showGateForm = false; }

  saveGate(): void {
    const obs = this.isEditMode
      ? this.api.updateGate(this.newGate.id, this.newGate)
      : this.api.createGate(this.newGate);

    obs.subscribe({
      next: () => { this.closeGateForm(); this.load(); },
      error: () => alert('Erro ao salvar portão')
    });
  }

  deleteGate(gate: any): void {
    if (!confirm(`Remover ${gate.name}?`)) return;
    this.api.deleteGate(gate.id).subscribe({ next: () => this.load() });
  }
}
