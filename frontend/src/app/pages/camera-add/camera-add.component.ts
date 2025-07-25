import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms'; 
import { ApiService } from '../../api.service';

@Component({
  selector: 'app-camera-add',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule], 
  templateUrl: './camera-add.component.html',
  styleUrls: ['./camera-add.component.scss']
})
export class CameraAddComponent {
  // Objeto para guardar os dados do formulário
  cameraModel: any = {
    name: '',
    ip_address: '',
    username: 'admin',
    password: '',
    camera_type: 'onvif'
  };

  constructor(private apiService: ApiService, private router: Router) {}

  // Função chamada quando o formulário é submetido
  onSubmit() {
    console.log('A enviar dados da câmara:', this.cameraModel);
    this.apiService.createCamera(this.cameraModel).subscribe({
      next: (response) => {
        console.log('Câmara criada com sucesso!', response);
        alert('Câmara adicionada com sucesso!');
        // Navega de volta para a lista de câmaras
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        console.error('Erro ao criar câmara', err);
        alert('Ocorreu um erro ao adicionar a câmara. Verifique a consola.');
      }
    });
  }
}