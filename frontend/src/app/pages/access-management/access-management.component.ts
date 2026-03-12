import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-access-management',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './access-management.component.html',
  styleUrl: './access-management.component.scss'
})
export class AccessManagementComponent implements OnInit {

  // Alternador de Ecrã Principal
  currentView: 'live' | 'users' = 'live';

  // Controlos de Modais
  selectedLog: any = null;
  showUserForm = false;
  showDeviceForm = false;
  isEditMode = false; // Define se estamos a criar ou a editar

  // Formulário de Utilizador (Estrutura base)
  defaultUser = { id: null, name: '', department: '', cpf: '', accessType: 'Reconhecimento Facial', rfidCode: '', permissionLevel: 'Acesso Total (24h)', validity: '' };
  newUser: any = { ...this.defaultUser };
  
  newDevice = { name: '', type: 'Control iD (Catraca)', location: '', ip: '', port: '80', username: 'admin', password: '' };

  // Feed Simulado (Eventos)
  liveLogs = [
    { id: 1, time: '14:32:05', type: 'in', action: 'Entrada Autorizada', name: 'Matheus Correia', device: 'Catraca Principal', photo: 'https://i.pravatar.cc/600?img=11', method: 'Reconhecimento Facial', confidence: '98.5%', cpf: '123.456.789-00' },
    { id: 2, time: '14:30:12', type: 'block', action: 'Acesso Negado', name: 'Desconhecido', device: 'Porta Servidores', photo: null, method: 'Tentativa Não Cadastrada', confidence: 'N/A', cpf: 'N/A' },
    { id: 3, time: '14:15:40', type: 'out', action: 'Saída Autorizada', name: 'Carlos Almeida', device: 'Catraca Principal', photo: 'https://i.pravatar.cc/600?img=33', method: 'Tag RFID', confidence: '100%', cpf: '987.654.321-11' }
  ];

  // Banco de Dados Simulado (Utilizadores Cadastrados)
  registeredUsers = [
    { id: 101, name: 'Matheus Correia', department: 'Diretoria', cpf: '123.456.789-00', accessType: 'Reconhecimento Facial', permissionLevel: 'Acesso Total (24h)', validity: '-', photo: 'https://i.pravatar.cc/150?img=11' },
    { id: 102, name: 'Carlos Almeida', department: 'Suporte', cpf: '987.654.321-11', accessType: 'Cartão RFID', permissionLevel: 'Horário Comercial', validity: '-', photo: 'https://i.pravatar.cc/150?img=33' },
    { id: 103, name: 'Ana Oliveira', department: 'Manutenção (Terceirizada)', cpf: '444.555.666-77', accessType: 'Reconhecimento Facial', permissionLevel: 'Visitante (Temporário)', validity: '25/02/2026', photo: 'https://i.pravatar.cc/150?img=47' }
  ];

  constructor() {}
  ngOnInit(): void {}

  // Alternar entre Live Feed e Banco de Utilizadores
  switchView(view: 'live' | 'users') {
    this.currentView = view;
  }

  // Novo Utilizador
  openUserForm() { 
    this.isEditMode = false;
    this.newUser = { ...this.defaultUser }; // Limpa o form
    this.showUserForm = true; 
  }

  // Editar Utilizador (Preenche o Modal com os dados existentes)
  editUser(user: any) {
    this.isEditMode = true;
    this.newUser = { ...user }; // Copia os dados do utilizador clicado para o formulário
    this.showUserForm = true;
  }

  closeUserForm() { this.showUserForm = false; }
  
  saveUser() { 
    if(this.isEditMode) alert(`Dados de ${this.newUser.name} atualizados com sucesso!`);
    else alert('Novo usuário cadastrado com sucesso!');
    this.closeUserForm(); 
  }

  // Dispositivos e Logs
  openDeviceForm() { this.showDeviceForm = true; }
  closeDeviceForm() { this.showDeviceForm = false; }
  saveDevice() { alert('Dispositivo adicionado!'); this.closeDeviceForm(); }
  openLogDetails(log: any) { this.selectedLog = log; }
  closeLogDetails() { this.selectedLog = null; }
  quickOpen(door: string) { alert(`A abrir: ${door}`); }
}