import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

// 1. IMPORTE O ApiService E O timer AQUI
import { ApiService } from './api.service';
import { timer } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, 
    // RouterOutlet foi removido daqui para corrigir o aviso
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  cameras: any[] = [];
  selectedCamera: any = null;
  events: any[] = [];
  videoFeedUrl: string | null = null;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    // 2. Erro de 'any' corrigido adicionando o tipo para 'data'
    this.apiService.getCameras().subscribe((data: any[]) => {
      this.cameras = data;
      if (data.length > 0) {
        this.selectCamera(data[0]);
      }
    });

    timer(0, 5000).subscribe(() => {
      if (this.selectedCamera) {
        // 3. Erro de 'any' corrigido adicionando o tipo para 'eventsData'
        this.apiService.getEventsForCamera(this.selectedCamera.id)
          .subscribe((eventsData: any[]) => {
            this.events = eventsData.reverse(); // Mostra os eventos mais recentes primeiro
          });
      }
    });
  }

  selectCamera(camera: any): void {
    this.selectedCamera = camera;
    this.videoFeedUrl = this.apiService.getVideoFeedUrl(camera.id);
  }
}