import requests
from requests.auth import HTTPDigestAuth
import datetime
import time
import json
from .base_adapter import CameraAdapter

class IntelbrasAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        # URL base para API da Intelbras/Dahua
        self.base_url = f"http://{self.ip}/cgi-bin"
        self.auth = HTTPDigestAuth(self.user, self.password)
        # Começa a procurar logs de 5 minutos atrás na primeira vez
        self.last_check_time = int(time.time()) - 300 

    def _get_time_str(self, timestamp):
        # Formato exato que a Intelbras exige: YYYY-M-D H:m:s
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%-m-%-d %H:%M:%S")

    def get_events(self):
        current_time = int(time.time())
        start_time_str = self._get_time_str(self.last_check_time)
        end_time_str = self._get_time_str(current_time)
        
        events_found = []
        print(f"[{self.ip}] A buscar logs Intelbras de {start_time_str} até {end_time_str}...")

        try:
            # 1. Iniciar a busca de logs (startFind)
            start_url = f"{self.base_url}/log.cgi?action=startFind&condition.StartTime={start_time_str}&condition.EndTime={end_time_str}&condition.LogType=Event"
            resp = requests.get(start_url, auth=self.auth, timeout=5)
            
            if "OK" in resp.text:
                # 2. Pede os resultados
                find_url = f"{self.base_url}/log.cgi?action=doFind&count=100&index=0"
                resp_logs = requests.get(find_url, auth=self.auth, timeout=5)
                
                raw_logs = resp_logs.text.split('\n')
                
                for line in raw_logs:
                    # Formato típico: "Index Time Type Data..."
                    # Ex: "1 2023-10-27 10:00:01 Event Motion Detection..."
                    parts = line.split(' ')
                    
                    if len(parts) > 4 and "Check Time" not in line:
                        # Reconstrói a data e hora (partes 1 e 2)
                        log_time_str = f"{parts[1]} {parts[2]}"
                        # O resto da linha é o tipo de evento
                        log_raw_type = " ".join(parts[4:]).strip()
                        
                        event_type = "Evento Genérico"
                        event_data = {}

                        # --- TRADUÇÃO DOS LOGS (Baseado no teu Print) ---
                        if "Motion Detection" in log_raw_type:
                            event_type = "Movimento"
                        elif "FaceDetection" in log_raw_type:
                            event_type = "Reconhecimento Facial"
                            event_data = {"nome": "Face Detetada", "nota": "Ver imagem"}
                        elif "CrossLine" in log_raw_type or "PeopleCounting" in log_raw_type:
                            event_type = "Contagem de Pessoas"
                            # Tenta simular um contador incremental
                            event_data = {"total": 1} 
                        elif "Alarm" in log_raw_type:
                            event_type = "Alarme"

                        # Cria o objeto do evento se for relevante
                        if event_type != "Evento Genérico":
                            events_found.append({
                                "event_type": event_type,
                                "event_data": json.dumps(event_data),
                                "timestamp": datetime.datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                            })

                # 3. Fecha a busca para limpar a memória da câmara
                requests.get(f"{self.base_url}/log.cgi?action=closeFind", auth=self.auth, timeout=2)

        except Exception as e:
            print(f"ERRO Intelbras ({self.ip}): {e}")

        # Atualiza o tempo para a próxima busca
        self.last_check_time = current_time
        return events_found