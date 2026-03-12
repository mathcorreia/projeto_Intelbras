  import { Injectable } from '@angular/core';
  import { HttpClient } from '@angular/common/http';
  
  import { Observable } from 'rxjs';

  @Injectable({
    providedIn: 'root'
  })
  export class ApiService {
    private apiUrl = 'http://localhost:8000';

    constructor(private http: HttpClient) { }

    getCameras(): Observable<any[]> {
      return this.http.get<any[]>(`${this.apiUrl}/cameras/`);
    }

    getEventsForCamera(cameraId: number): Observable<any[]> {
      return this.http.get<any[]>(`${this.apiUrl}/events/${cameraId}`);
    }

    getAllEvents(): Observable<any[]> {
      return this.http.get<any[]>(`${this.apiUrl}/events/`);
    }

    getVideoFeedUrl(cameraId: number): string {
      return `${this.apiUrl}/video_feed/${cameraId}`;
    }

    readCamera(cameraId: number): Observable<any> {
      return this.http.get<any>(`${this.apiUrl}/cameras/${cameraId}`);
    }

    createCamera(cameraData: any): Observable<any> {
      return this.http.post(`${this.apiUrl}/cameras/`, cameraData);
    }

    deleteCamera(cameraId: number): Observable<any> {
      return this.http.delete(`${this.apiUrl}/cameras/${cameraId}`);
    }

    getCamera(id: number): Observable<any> {
      return this.http.get(`${this.apiUrl}/cameras/${id}`);
    }

    // --- FUNÇÕES PTZ E MIBO ---

    controlPTZ(cameraId: number, direction: string, action: string) {
      const payload = { direction, action };
      return this.http.post(`${this.apiUrl}/cameras/${cameraId}/ptz`, payload);
    }

    updateCamera(id: number, data: any): Observable<any> {
      return this.http.put(`${this.apiUrl}/cameras/${id}`, data);
    }

    // --- ESTAS SÃO AS FUNÇÕES QUE FALTAVAM ---

    getAudioConfig(cameraId: number): Observable<any> {
      return this.http.get(`${this.apiUrl}/cameras/${cameraId}/mibo/audio`);
    }

    setAudioVolume(cameraId: number, volume: number): Observable<any> {
      return this.http.post(`${this.apiUrl}/cameras/${cameraId}/mibo/audio/volume`, { volume });
    }

    // --- NOVA FUNÇÃO DE LIGA/DESLIGA ---
    toggleAudio(cameraId: number, enable: boolean): Observable<any> {
      return this.http.post(`${this.apiUrl}/cameras/${cameraId}/mibo/audio/toggle`, { enable });
    }
    

    getCameraLogs(cameraId: number): Observable<any> {
      return this.http.get(`${this.apiUrl}/cameras/${cameraId}/mibo/logs`);
    }
    
  }