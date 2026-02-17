import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router'; // Adicionei ActivatedRoute
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
  // Objeto para guardar os dados do formulário
  cameraModel: any = {
    name: '',
    ip_address: '',
    username: 'admin',
    password: '',
    camera_type: 'intelbras' // Sugiro mudar o padrão para intelbras, já que usas mais
  };

  isEditMode = false;           // Variável para saber se estamos a editar
  cameraId: number | null = null; // Guarda o ID da câmara se for edição

  constructor(
    private apiService: ApiService, 
    private router: Router,
    private route: ActivatedRoute // Injeção necessária para ler a URL
  ) {}

  ngOnInit() {
    // Verifica se existe um ID na URL (ex: /camera-edit/1)
    const id = this.route.snapshot.paramMap.get('id');
    
    if (id) {
      // Se tem ID, estamos no modo de EDIÇÃO
      this.isEditMode = true;
      this.cameraId = +id; // O '+' converte string para número
      this.loadCameraData(this.cameraId);
    }
  }

  // Busca os dados da câmara antiga para preencher o formulário
  loadCameraData(id: number) {
    this.apiService.getCamera(id).subscribe({
      next: (data) => {
        this.cameraModel = data;
        // O campo password pode vir vazio por segurança, o utilizador preenche se quiser mudar
      },
      error: (err) => {
        alert('Erro ao carregar dados da câmara.');
        this.router.navigate(['/dashboard']);
      }
    });
  }

  // Função chamada quando o formulário é submetido
  onSubmit() {
    if (this.isEditMode && this.cameraId) {
      // --- LÓGICA DE ATUALIZAÇÃO (PUT) ---
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
      // --- LÓGICA DE CRIAÇÃO (POST) ---
      console.log('A criar nova câmara:', this.cameraModel);
      this.apiService.createCamera(this.cameraModel).subscribe({ // Confirma se no serviço é createCamera ou addCamera
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