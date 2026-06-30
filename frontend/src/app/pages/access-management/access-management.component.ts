import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-access-management',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './access-management.component.html',
  styleUrl: './access-management.component.scss'
})
export class AccessManagementComponent implements OnInit, OnDestroy {

  currentView: 'live' | 'users' = 'live';
  selectedLog: any = null;
  showUserForm = false;
  showDeviceForm = false;
  isEditMode = false;
  loading = false;

  liveLogs: any[] = [];
  registeredUsers: any[] = [];
  devices: any[] = [];

  defaultUser = { name: '', cpf: '', department: '', access_level: 'standard', is_active: true };
  newUser: any = { ...this.defaultUser };

  defaultDevice = { name: '', device_type: 'catraca', ip: '', port: 80, location: '', username: '', password: '' };
  newDevice: any = { ...this.defaultDevice };

  private pollInterval: any;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
    this.pollInterval = setInterval(() => this.loadLogs(), 8000);
  }

  ngOnDestroy(): void { clearInterval(this.pollInterval); }

  load(): void {
    this.loadLogs();
    this.api.getPersons().subscribe({ next: p => this.registeredUsers = p });
    this.api.getAccessDevices().subscribe({ next: d => this.devices = d });
  }

  loadLogs(): void {
    this.api.getAccessLogs(undefined, undefined, 50).subscribe({ next: l => this.liveLogs = l });
  }

  switchView(view: 'live' | 'users'): void { this.currentView = view; }

  openLogDetails(log: any): void { this.selectedLog = log; }
  closeLogDetails(): void { this.selectedLog = null; }

  openUserForm(): void {
    this.isEditMode = false;
    this.newUser = { ...this.defaultUser };
    this.showUserForm = true;
  }

  editUser(user: any): void {
    this.isEditMode = true;
    this.newUser = { ...user };
    this.showUserForm = true;
  }

  closeUserForm(): void { this.showUserForm = false; }

  saveUser(): void {
    const obs = this.isEditMode
      ? this.api.updatePerson(this.newUser.id, this.newUser)
      : this.api.createPerson(this.newUser);
    obs.subscribe({
      next: () => { this.closeUserForm(); this.api.getPersons().subscribe(p => this.registeredUsers = p); },
      error: (e: any) => alert(e?.error?.detail || 'Erro ao salvar pessoa')
    });
  }

  deleteUser(user: any): void {
    if (!confirm(`Desativar ${user.name}?`)) return;
    this.api.deletePerson(user.id).subscribe({ next: () => this.api.getPersons().subscribe(p => this.registeredUsers = p) });
  }

  openDeviceForm(): void {
    this.newDevice = { ...this.defaultDevice };
    this.showDeviceForm = true;
  }

  closeDeviceForm(): void { this.showDeviceForm = false; }

  saveDevice(): void {
    this.api.createAccessDevice(this.newDevice).subscribe({
      next: () => { this.closeDeviceForm(); this.api.getAccessDevices().subscribe(d => this.devices = d); },
      error: () => alert('Erro ao salvar dispositivo')
    });
  }

  quickOpen(device: any): void {
    this.api.manualOpenDevice(device.id, 'Abertura rápida pelo operador').subscribe({
      next: (r: any) => alert(r.gate_triggered ? `Portão aberto via ${device.name}` : 'Nenhum portão vinculado a este dispositivo'),
      error: () => alert('Falha ao abrir')
    });
  }
}
