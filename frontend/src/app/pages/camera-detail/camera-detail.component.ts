import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../api.service';
import { timer } from 'rxjs';

@Component({
  selector: 'app-camera-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './camera-detail.component.html',
  styleUrls: ['./camera-detail.component.scss']
})
export class CameraDetailComponent implements OnInit {
  camera: any = null;
  events: any[] = [];
  videoFeedUrl: string | null = null;
  peopleCount: number = 0; // Variável para a contagem

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) { }

  ngOnInit(): void {
    const cameraId = this.route.snapshot.paramMap.get('id');
    if (!cameraId) return;

    const id = parseInt(cameraId, 10);
    this.apiService.readCamera(id).subscribe(data => {
      this.camera = data;
    });
    this.videoFeedUrl = this.apiService.getVideoFeedUrl(id);

    // Busca os eventos a cada 5 segundos
    timer(0, 5000).subscribe(() => {
      this.apiService.getEventsForCamera(id).subscribe((eventsData: any[]) => {
        
        eventsData.forEach(event => {
          // Se for um evento de contagem, atualiza a variável de contagem
          if (event.event_type === 'Contagem de Pessoas') {
            const data = JSON.parse(event.event_data);
            this.peopleCount = data.total;
          } 
          // Se for outro tipo de evento, adiciona à lista para ser exibido
          else {
            if (event.event_data) {
              event.parsed_data = JSON.parse(event.event_data);
            }
            this.events.unshift(event); // Adiciona o novo evento no início da lista
          }
        });

        // Limita a lista de eventos para não ficar muito grande
        if (this.events.length > 20) {
          this.events.length = 20;
        }
      });
    });
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}