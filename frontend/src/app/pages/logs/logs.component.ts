import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../api.service';
import { RouterModule } from '@angular/router';
import { interval, Subscription, forkJoin } from 'rxjs';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './logs.component.html',
  styleUrls: ['./logs.component.scss']
})
export class LogsComponent implements OnInit, OnDestroy {
  events: any[] = [];
  camerasMap: { [key: number]: string } = {}; // Mapa para converter ID -> Nome
  pollingSub!: Subscription;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    // 1. Primeiro carregamos as câmaras para ter os nomes
    this.apiService.getCameras().subscribe(cams => {
      cams.forEach(cam => this.camerasMap[cam.id] = cam.name);
      
      // 2. Carrega eventos imediatamente
      this.loadEvents();

      // 3. Inicia o polling a cada 5 segundos
      this.pollingSub = interval(5000).subscribe(() => this.loadEvents());
    });
  }

  loadEvents() {
    this.apiService.getAllEvents().subscribe(data => {
      this.events = data.map(event => {
        // Tenta fazer parse do JSON se for string
        let parsed = {};
        try {
          if (typeof event.event_data === 'string') {
            parsed = JSON.parse(event.event_data);
          } else {
            parsed = event.event_data;
          }
        } catch (e) { console.error('Erro parse JSON', e); }

        return {
          ...event,
          camera_name: this.camerasMap[event.camera_id] || 'Câmara Removida',
          parsed_data: parsed
        };
      });
    });
  }

  ngOnDestroy() {
    if (this.pollingSub) this.pollingSub.unsubscribe();
  }
}