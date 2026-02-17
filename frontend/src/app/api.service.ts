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

  // Enviar a atualização
  updateCamera(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/cameras/${id}`, data);
  }
}