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
    // Busca os eventos a cada 5 segundos
    timer(0, 5000).subscribe(() => {
      this.apiService.getEventsForCamera(id).subscribe((eventsData: any[]) => {
        
        const processedEvents: any[] = []; // Array temporário

        eventsData.forEach(event => {
          if (event.event_type === 'Contagem de Pessoas') {
            try {
              const data = JSON.parse(event.event_data);
              this.peopleCount = data.total; // Atualiza contador
            } catch(e) {}
          } 
          else {
            if (event.event_data) {
              try {
                event.parsed_data = JSON.parse(event.event_data);
              } catch (e) { event.parsed_data = {}; }
            }
            processedEvents.push(event); // Adiciona ao temporário
          }
        });

        // ATENÇÃO: Substitui o array antigo pelo novo, em vez de fazer unshift/push
        this.events = processedEvents; 
      });
    });

        // Limita a lista de eventos para não ficar muito grande
     
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}