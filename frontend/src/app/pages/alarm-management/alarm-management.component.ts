import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-alarm-management',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './alarm-management.component.html',
  styleUrl: './alarm-management.component.scss'
})
export class AlarmManagementComponent implements OnInit {

  currentView: 'live' | 'database' = 'live';
  showAlarmForm = false;
  isEditMode = false;

  newAlarm = { id: null, name: '', model: 'Intelbras AMT 8000', ip: '', mac: '', port: '9009', password: '', zonesCount: 16 };

  // Centrais Simuladas
  alarms = [
    { id: 1, name: 'Central Matriz', status: 'ARMED', ip: '192.168.1.150', zonesOnline: 16 },
    { id: 2, name: 'Central Galpão', status: 'DISARMED', ip: '192.168.1.151', zonesOnline: 8 }
  ];

  // Zonas (Sensores) Simuladas para a Vista Live
  zones = [
    { id: 1, name: 'Recepção (Infra)', status: 'NORMAL', bypassed: false },
    { id: 2, name: 'Porta Entrada (Magnético)', status: 'OPEN', bypassed: false },
    { id: 3, name: 'Cofre (Vibração)', status: 'NORMAL', bypassed: true }
  ];

  // Feed de Eventos
  liveLogs = [
    { id: 1, time: '15:10:22', type: 'alert', action: 'Disparo de Alarme!', zone: 'Porta Entrada', device: 'Central Matriz' },
    { id: 2, time: '15:05:00', type: 'arm', action: 'Sistema Armado', zone: 'Todas as Zonas', device: 'Central Matriz' },
    { id: 3, time: '08:30:15', type: 'disarm', action: 'Sistema Desarmado (Usuário: 01)', zone: '-', device: 'Central Galpão' }
  ];

  constructor() {}
  ngOnInit(): void {}

  switchView(view: 'live' | 'database') { this.currentView = view; }

  // Ações de Alarme
  armSystem(id: number) { alert('A enviar comando de ARME para a central...'); }
  disarmSystem(id: number) { alert('A enviar comando de DESARME...'); }
  bypassZone(zone: any) { alert(`A isolar zona: ${zone.name}`); zone.bypassed = !zone.bypassed; }

  // Formulários
  openAlarmForm() { this.isEditMode = false; this.showAlarmForm = true; }
  editAlarm(alarm: any) { this.isEditMode = true; this.showAlarmForm = true; }
  closeAlarmForm() { this.showAlarmForm = false; }
  saveAlarm() { alert('Central guardada com sucesso!'); this.closeAlarmForm(); }
}