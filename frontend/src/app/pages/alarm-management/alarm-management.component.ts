import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-alarm-management',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './alarm-management.component.html',
  styleUrl: './alarm-management.component.scss'
})
export class AlarmManagementComponent implements OnInit, OnDestroy {

  currentView: 'live' | 'database' = 'live';
  showAlarmForm = false;
  isEditMode = false;
  loading = false;
  error = '';

  alarms: any[] = [];
  zones: any[] = [];
  liveLogs: any[] = [];
  selectedCentralId: number | null = null;

  newAlarm: any = { name: '', model: '', ip: '', port: 9009, password: '' };

  private pollInterval: any;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
    this.pollInterval = setInterval(() => this.loadEvents(), 10000);
  }

  ngOnDestroy(): void {
    clearInterval(this.pollInterval);
  }

  load(): void {
    this.loading = true;
    this.api.getAlarmCentrals().subscribe({
      next: centrals => {
        this.alarms = centrals;
        if (centrals.length > 0) this.selectCentral(centrals[0].id);
        this.loading = false;
      },
      error: () => { this.error = 'Erro ao carregar centrais'; this.loading = false; }
    });
    this.loadEvents();
  }

  selectCentral(id: number): void {
    this.selectedCentralId = id;
    this.api.getZones(id).subscribe({ next: z => this.zones = z });
  }

  loadEvents(): void {
    const centralId = this.selectedCentralId ?? undefined;
    this.api.getAlarmEvents(centralId, 50).subscribe({ next: ev => this.liveLogs = ev });
  }

  switchView(view: 'live' | 'database'): void { this.currentView = view; }

  armSystem(alarm: any): void {
    this.api.armCentral(alarm.id).subscribe({
      next: (r: any) => alert(r.message || 'Arme enviado'),
      error: () => alert('Falha ao armar')
    });
  }

  disarmSystem(alarm: any): void {
    this.api.disarmCentral(alarm.id).subscribe({
      next: (r: any) => alert(r.message || 'Desarme enviado'),
      error: () => alert('Falha ao desarmar')
    });
  }

  bypassZone(zone: any): void {
    this.api.toggleBypass(zone.id).subscribe({
      next: (r: any) => zone.is_bypassed = r.is_bypassed,
      error: () => alert('Falha ao isolar zona')
    });
  }

  openAlarmForm(): void {
    this.isEditMode = false;
    this.newAlarm = { name: '', model: '', ip: '', port: 9009, password: '' };
    this.showAlarmForm = true;
  }

  editAlarm(alarm: any): void {
    this.isEditMode = true;
    this.newAlarm = { ...alarm };
    this.showAlarmForm = true;
  }

  closeAlarmForm(): void { this.showAlarmForm = false; }

  saveAlarm(): void {
    const obs = this.isEditMode
      ? this.api.updateAlarmCentral(this.newAlarm.id, this.newAlarm)
      : this.api.createAlarmCentral(this.newAlarm);

    obs.subscribe({
      next: () => { this.closeAlarmForm(); this.load(); },
      error: () => alert('Erro ao salvar central')
    });
  }

  deleteAlarm(alarm: any): void {
    if (!confirm(`Remover ${alarm.name}?`)) return;
    this.api.deleteAlarmCentral(alarm.id).subscribe({ next: () => this.load() });
  }
}
