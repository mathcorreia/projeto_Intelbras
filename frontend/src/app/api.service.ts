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

  getVideoFeedUrl(cameraId: number): string {
    return `${this.apiUrl}/video_feed/${cameraId}`;
  }
  readCamera(cameraId: number): Observable<any> {
  return this.http.get<any>(`${this.apiUrl}/cameras/${cameraId}`);
}
createCamera(cameraData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/cameras/`, cameraData);
  }
}