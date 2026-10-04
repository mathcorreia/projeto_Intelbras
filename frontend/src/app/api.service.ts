import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  // ── Câmeras ──────────────────────────────────────────────────────────────────

  getCameras(): Observable<any[]>               { return this.http.get<any[]>(`${this.api}/cameras/`); }
  getCamera(id: number): Observable<any>         { return this.http.get(`${this.api}/cameras/${id}`); }
  readCamera(id: number): Observable<any>        { return this.getCamera(id); }
  createCamera(data: any): Observable<any>       { return this.http.post(`${this.api}/cameras/`, data); }
  updateCamera(id: number, data: any)            { return this.http.put(`${this.api}/cameras/${id}`, data); }
  deleteCamera(id: number): Observable<any>      { return this.http.delete(`${this.api}/cameras/${id}`); }
  getVideoFeedUrl(id: number): string            { return `${this.api}/video_feed/${id}`; }
  controlPTZ(id: number, direction: string, action: string) {
    return this.http.post(`${this.api}/cameras/${id}/ptz`, { direction, action });
  }
  getAudioConfig(id: number)                     { return this.http.get(`${this.api}/cameras/${id}/mibo/audio`); }
  setAudioVolume(id: number, volume: number)     { return this.http.post(`${this.api}/cameras/${id}/mibo/audio/volume`, { volume }); }
  toggleAudio(id: number, enable: boolean)       { return this.http.post(`${this.api}/cameras/${id}/mibo/audio/toggle`, { enable }); }
  getCameraLogs(id: number)                      { return this.http.get(`${this.api}/cameras/${id}/system-logs`); }

  // ── Eventos ───────────────────────────────────────────────────────────────────

  getAllEvents(skip = 0, limit = 50): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/events/`, { params: { skip, limit } });
  }
  getEventsForCamera(id: number): Observable<any[]> { return this.http.get<any[]>(`${this.api}/events/${id}`); }

  // ── Alarmes ───────────────────────────────────────────────────────────────────

  getAlarmCentrals(): Observable<any[]>                   { return this.http.get<any[]>(`${this.api}/alarms/centrals`); }
  getAlarmCentral(id: number): Observable<any>            { return this.http.get(`${this.api}/alarms/centrals/${id}`); }
  createAlarmCentral(data: any): Observable<any>          { return this.http.post(`${this.api}/alarms/centrals`, data); }
  updateAlarmCentral(id: number, data: any)               { return this.http.put(`${this.api}/alarms/centrals/${id}`, data); }
  deleteAlarmCentral(id: number)                          { return this.http.delete(`${this.api}/alarms/centrals/${id}`); }
  armCentral(id: number, partition = 1)                   { return this.http.post(`${this.api}/alarms/centrals/${id}/arm`, null, { params: { partition } }); }
  disarmCentral(id: number, partition = 1)                { return this.http.post(`${this.api}/alarms/centrals/${id}/disarm`, null, { params: { partition } }); }
  armStayCentral(id: number, partition = 1)               { return this.http.post(`${this.api}/alarms/centrals/${id}/arm-stay`, null, { params: { partition } }); }
  getCentralStatus(id: number)                            { return this.http.get(`${this.api}/alarms/centrals/${id}/status`); }
  getZones(centralId: number): Observable<any[]>          { return this.http.get<any[]>(`${this.api}/alarms/centrals/${centralId}/zones`); }
  createZone(data: any): Observable<any>                  { return this.http.post(`${this.api}/alarms/zones`, data); }
  updateZone(id: number, data: any)                       { return this.http.put(`${this.api}/alarms/zones/${id}`, data); }
  toggleBypass(zoneId: number)                            { return this.http.patch(`${this.api}/alarms/zones/${zoneId}/bypass`, {}); }
  getAlarmEvents(centralId?: number, limit = 100): Observable<any[]> {
    let params: any = { limit };
    if (centralId) params['central_id'] = centralId;
    return this.http.get<any[]>(`${this.api}/alarms/events`, { params });
  }

  // ── Portões ───────────────────────────────────────────────────────────────────

  getGates(): Observable<any[]>                   { return this.http.get<any[]>(`${this.api}/gates/`); }
  getGate(id: number): Observable<any>            { return this.http.get(`${this.api}/gates/${id}`); }
  createGate(data: any): Observable<any>          { return this.http.post(`${this.api}/gates/`, data); }
  updateGate(id: number, data: any)               { return this.http.put(`${this.api}/gates/${id}`, data); }
  deleteGate(id: number)                          { return this.http.delete(`${this.api}/gates/${id}`); }
  triggerGate(id: number)                         { return this.http.post(`${this.api}/gates/${id}/trigger`, {}); }
  getGateStatus(id: number)                       { return this.http.get(`${this.api}/gates/${id}/status`); }

  // ── Controle de Acesso ────────────────────────────────────────────────────────

  getAccessDevices(): Observable<any[]>                   { return this.http.get<any[]>(`${this.api}/access/devices`); }
  createAccessDevice(data: any): Observable<any>          { return this.http.post(`${this.api}/access/devices`, data); }
  updateAccessDevice(id: number, data: any)               { return this.http.put(`${this.api}/access/devices/${id}`, data); }
  deleteAccessDevice(id: number)                          { return this.http.delete(`${this.api}/access/devices/${id}`); }
  manualOpenDevice(id: number, notes?: string)            { return this.http.post(`${this.api}/access/devices/${id}/manual-open`, { notes }); }
  getAccessLogs(personId?: number, deviceId?: number, limit = 100): Observable<any[]> {
    let params: any = { limit };
    if (personId) params['person_id'] = personId;
    if (deviceId) params['device_id'] = deviceId;
    return this.http.get<any[]>(`${this.api}/access/logs`, { params });
  }

  // ── Pessoas ───────────────────────────────────────────────────────────────────

  getPersons(activeOnly = false): Observable<any[]>       { return this.http.get<any[]>(`${this.api}/persons/`, { params: { active_only: activeOnly } }); }
  getPerson(id: number): Observable<any>                  { return this.http.get(`${this.api}/persons/${id}`); }
  createPerson(data: any): Observable<any>                { return this.http.post(`${this.api}/persons/`, data); }
  updatePerson(id: number, data: any)                     { return this.http.put(`${this.api}/persons/${id}`, data); }
  deletePerson(id: number)                                { return this.http.delete(`${this.api}/persons/${id}`); }
  enrollFace(personId: number, imageBase64: string)       { return this.http.post(`${this.api}/persons/${personId}/enroll-face`, { image_base64: imageBase64 }); }

  // ── Visitantes ────────────────────────────────────────────────────────────────

  getVisitors(): Observable<any[]>                        { return this.http.get<any[]>(`${this.api}/visitors/`); }
  getActiveVisitors(): Observable<any[]>                  { return this.http.get<any[]>(`${this.api}/visitors/active`); }
  createVisitor(data: any): Observable<any>               { return this.http.post(`${this.api}/visitors/`, data); }
  updateVisitorStatus(id: number, status: string)         { return this.http.patch(`${this.api}/visitors/${id}/status`, { status }); }

  // ── Guarita ───────────────────────────────────────────────────────────────────

  getGuaritaQueue(): Observable<any[]>                    { return this.http.get<any[]>(`${this.api}/guarita/queue`); }
  approveUnknownFace(eventId: number, deviceId?: number, notes?: string) {
    return this.http.post(`${this.api}/guarita/approve/${eventId}`, { device_id: deviceId, notes });
  }
  denyUnknownFace(eventId: number, notes?: string) {
    return this.http.post(`${this.api}/guarita/deny/${eventId}`, { notes });
  }
  getGuaritaVisitors(): Observable<any[]>                 { return this.http.get<any[]>(`${this.api}/guarita/visitors`); }
  preRegisterVisitor(data: any): Observable<any>          { return this.http.post(`${this.api}/guarita/visitors`, data); }
  approveVisitor(id: number)                              { return this.http.patch(`${this.api}/guarita/visitors/${id}/approve`, {}); }
  denyVisitor(id: number)                                 { return this.http.patch(`${this.api}/guarita/visitors/${id}/deny`, {}); }
  getGuaritaAlertsUrl(): string                           { return `${this.api}/guarita/alerts/stream`; }

  // ── Face image URL ────────────────────────────────────────────────────────────

  getFaceImageUrl(filename: string): string               { return `${this.api}/faces/${filename}`; }
}
