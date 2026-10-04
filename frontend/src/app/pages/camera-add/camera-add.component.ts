import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms'; 
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-camera-add',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule], 
  templateUrl: './camera-add.component.html',
  styleUrls: ['./camera-add.component.scss']
})
export class CameraAddComponent implements OnInit {
  
  // Objeto mantido exatamente como o teu
  cameraModel: any = {
    name: '',
    ip_address: '',
    username: 'admin',
    password: '',
    camera_type: 'onvif' // Alterado o padrão inicial
  };

  isEditMode = false;           
  cameraId: number | null = null; 

  // --- NOVA LISTA DE ADAPTADORES ---
  adapters = [
    { id: 'onvif', name: 'ONVIF Padrão', icon: '🌐', desc: 'Descoberta automática' },
    { id: 'intelbras', name: 'Intelbras Pro', icon: '🏢', desc: 'Série 3000, 5000, etc.' },
    { id: 'mibo', name: 'Intelbras Mibo', icon: '📷', desc: 'Linha iM3, iM4, iM5...' },
    { id: 'bronze', name: 'Bronze (Ping)', icon: '📡', desc: 'Apenas status de rede' }
  ];

  constructor(
    private apiService: ApiService, 
    private router: Router,
    private route: ActivatedRoute 
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    
    if (id) {
      this.isEditMode = true;
      this.cameraId = +id; 
      this.loadCameraData(this.cameraId);
    }
  }

  // --- NOVA LÓGICA DE SELEÇÃO DE ADAPTADOR ---
  onAdapterChange(adapterId: string) {
    this.cameraModel.camera_type = adapterId;
    
    // Regra de negócio da MIBO
    if (adapterId === 'mibo') {
      this.cameraModel.username = 'admin'; // Força o admin
    } else if (adapterId === 'bronze') {
      this.cameraModel.username = '';
      this.cameraModel.password = '';
    }
  }

  loadCameraData(id: number) {
    this.apiService.getCamera(id).subscribe({
      next: (data) => {
        this.cameraModel = data;
      },
      error: (err) => {
        alert('Erro ao carregar dados da câmara.');
        this.router.navigate(['/dashboard']);
      }
    });
  }

  onSubmit() {
    if (this.isEditMode && this.cameraId) {
      console.log('A atualizar câmara:', this.cameraModel);
      this.apiService.updateCamera(this.cameraId, this.cameraModel).subscribe({
        next: () => {
          alert('Câmara atualizada com sucesso!');
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          console.error('Erro ao atualizar', err);
          alert('Erro ao atualizar a câmara.');
        }
      });
    } else {
      console.log('A criar nova câmara:', this.cameraModel);
      this.apiService.createCamera(this.cameraModel).subscribe({ 
        next: (response) => {
          console.log('Câmara criada com sucesso!', response);
          alert('Câmara adicionada com sucesso!');
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          console.error('Erro ao criar câmara', err);
          alert('Ocorreu um erro ao adicionar a câmara. Verifique a consola.');
        }
      });
    }
  }
}