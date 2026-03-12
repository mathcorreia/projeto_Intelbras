import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

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

  // Formulário para configurar o Módulo IoT do Portão
  defaultGate = { id: null, name: '', brand: 'PPA Contatto Wi-Fi', ip: '', pulseTime: '1', sensorEnabled: true, location: '' };
  newGate: any = { ...this.defaultGate };

  // Portões Reais Simulados
  gates = [
    { id: 1, name: 'Portão Principal (Entrada)', brand: 'PPA', status: 'CLOSED', lastAction: 'Fechou há 5 min', ip: '192.168.1.110' },
    { id: 2, name: 'Portão Carga e Descarga', brand: 'Intelbras', status: 'OPEN', lastAction: 'Aberto por João Silva', ip: '192.168.1.111' },
    { id: 3, name: 'Cancela Subsolo', brand: 'PPA', status: 'MOVING', lastAction: 'A Abrir...', ip: '192.168.1.112' }
  ];

  // Feed de Logs de Garagem
  liveLogs = [
    { id: 1, time: '14:45:10', type: 'trigger', action: 'Acionamento Manual', user: 'Operador Admin', device: 'Portão Principal' },
    { id: 2, time: '14:20:05', type: 'lpr', action: 'Abertura via LPR', user: 'Placa: ABC-1234', device: 'Cancela Subsolo' },
    { id: 3, time: '13:10:00', type: 'alert', action: 'Alarme: Portão Aberto > 5min', user: 'Sistema', device: 'Portão Carga e Descarga' }
  ];

  constructor() {}
  ngOnInit(): void {}

  switchView(view: 'live' | 'database') { this.currentView = view; }

  // Gestão do Formulário
  openGateForm() { this.isEditMode = false; this.newGate = { ...this.defaultGate }; this.showGateForm = true; }
  editGate(gate: any) { this.isEditMode = true; this.newGate = { ...gate }; this.showGateForm = true; }
  closeGateForm() { this.showGateForm = false; }
  
  saveGate() { 
    alert(this.isEditMode ? 'Configurações do portão atualizadas!' : 'Novo Módulo IOT adicionado à rede!');
    this.closeGateForm(); 
  }

  // Comando IoT Real
  triggerGate(gate: any) {
    alert(`A enviar pulso para ${gate.name} (${gate.ip})...`);
    // Aqui entra o this.apiService.toggleGate(gate.id).subscribe(...)
  }
}