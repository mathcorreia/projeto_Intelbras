import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../api.service';
import { timer } from 'rxjs';

// 1. Importe o CommonModule
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-camera-detail',
  standalone: true,
  // 2. Adicione o CommonModule aqui
  imports: [CommonModule],
  templateUrl: './camera-detail.component.html',
  styleUrls: ['./camera-detail.component.scss']
})
export class CameraDetailComponent implements OnInit {
  camera: any = null;
  events: any[] = [];
  videoFeedUrl: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) { }

  ngOnInit(): void {
    const cameraId = this.route.snapshot.paramMap.get('id');

    if (cameraId) {
      const id = parseInt(cameraId, 10);

      // O erro "readCamera does not exist" desaparecerá agora
      this.apiService.readCamera(id).subscribe((data: any) => { // <-- tipo adicionado
        this.camera = data;
      });

      this.videoFeedUrl = this.apiService.getVideoFeedUrl(id);

      timer(0, 5000).subscribe(() => {
        this.apiService.getEventsForCamera(id).subscribe((eventsData: any[]) => { // <-- tipo adicionado
          this.events = eventsData.map(event => {
            if (event.event_data) {
              event.parsed_data = JSON.parse(event.event_data);
            }
            return event;
          });
        });
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}