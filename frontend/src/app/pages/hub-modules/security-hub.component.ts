import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../api.service'; // Use seu serviço para chamar o Python

@Component({
  selector: 'app-security-hub',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './security-hub.component.html',
  styleUrls: ['./security-hub.component.scss']
})
export class SecurityHubComponent implements OnInit {
  
  // Módulo Control iD (Acessos)
  idDevices = [
    { id: 'door1', name: 'Recepção Principal', status: 'LOCKED', ip: '192.168.1.50' },
    { id: 'door2', name: 'Almoxarifado', status: 'LOCKED', ip: '192.168.1.51' }
  ];

  // Módulo PPA (Portões)
  ppaGates = [
    { id: 'gate1', name: 'Garagem Subsolo', status: 'CLOSED', mode: 'Automatic' }
  ];

  // Módulo Intelbras (Alarme)
  alarmCentrals = [
    { id: 'central1', name: 'Central Industrial', status: 'DISARMED', zones: 12 }
  ];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    // Aqui você chamaria seu backend Python para pegar os status iniciais
  }

  // Integração com Python para Control iD
  unlockDoor(deviceId: string) {
    console.log(`Solicitando abertura da porta ${deviceId} ao backend Python...`);
    // Ex: this.api.post('http://localhost:5000/api/controlid/unlock', { id: deviceId }).subscribe();
  }

  // Integração com Python para PPA
  toggleGate(gateId: string) {
    console.log(`Acionando portão PPA ${gateId} via Python...`);
  }

  // Integração com Python para Intelbras
  armAlarm(centralId: string) {
    console.log(`Armando central Intelbras ${centralId}...`);
  }
}