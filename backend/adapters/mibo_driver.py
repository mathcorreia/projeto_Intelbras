import requests
from requests.auth import HTTPDigestAuth
import time

class MiboDriver:
    def __init__(self, ip, username, password):
        """
        Inicializa a conexão com a Mibo.
        O password é SEMPRE o Código de Segurança (8 letras) da etiqueta.
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{self.ip}/cgi-bin"
        self.auth = HTTPDigestAuth(self.username, self.password)

    def _send_command(self, endpoint, params=None):
        """Função auxiliar para enviar os comandos CGI"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, auth=self.auth, params=params, timeout=3)
            if response.status_code == 200 and "OK" in response.text:
                return True
            else:
                print(f"Erro da câmara: {response.text}")
                return False
        except Exception as e:
            print(f"Falha de conexão com a Mibo {self.ip}: {e}")
            return False

    # ==========================================
    # 1. CONTROLO DE MOVIMENTO (PTZ) - Para Mibo iM4, iM5, etc.
    # ==========================================
    def move_ptz(self, direction, action="start", speed=5):
        """
        Move a câmara.
        direction: Up, Down, Left, Right
        action: start (começa a mover), stop (para)
        """
        params = {
            "action": action,
            "code": direction,
            "arg1": speed, # Velocidade Pan
            "arg2": speed, # Velocidade Tilt
            "arg3": 0,
            "channel": 1
        }
        print(f"Mibo PTZ: {action} {direction}")
        return self._send_command("ptz.cgi", params)

    # ==========================================
    # 2. CONTROLO DE IMAGEM / VISÃO NOTURNA
    # ==========================================
    def set_night_vision(self, mode):
        """
        mode: 
          0 = Dia (Cores, Infravermelho desligado)
          1 = Noite (Preto/Branco, Infravermelho ligado)
          2 = Automático
        """
        params = {
            "action": "set",
            "VideoInMode[0].Config[0]": mode
        }
        return self._send_command("configManager.cgi", params)

    # ==========================================
    # 3. FALAR NA CÂMARA (ÁUDIO BIDIRECIONAL)
    # ==========================================
    def send_audio_chunk(self, audio_bytes):
        """
        Envia um pacote de áudio do microfone do teu PC/Angular para o altifalante da câmara.
        A câmara Intelbras espera formato G.711u, 8000Hz, 8bit, Mono.
        """
        url = f"{self.base_url}/audio.cgi?action=postAudio&httptype=singlepart&channel=1"
        headers = {
            'Content-Type': 'application/audio',
            'Content-Length': str(len(audio_bytes))
        }
        
        try:
            # Atenção: Esta requisição é um POST com os bytes do áudio
            response = requests.post(
                url, 
                auth=self.auth, 
                headers=headers, 
                data=audio_bytes, 
                timeout=1
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar áudio: {e}")
            return False
# ==========================================
    # CONFIGURAÇÕES DE ÁUDIO (Microfone e Altifalante)
    # ==========================================
    def get_audio_config(self):
        """Busca as configurações atuais de áudio da câmara"""
        try:
            # Busca configs de entrada (Microfone) e saída (Altifalante)
            url = f"{self.base_url}/configManager.cgi?action=getConfig&name=AudioIn"
            response = requests.get(url, auth=self.auth, timeout=3)
            return response.text if response.status_code == 200 else "Erro ao buscar áudio"
        except Exception as e:
            return str(e)

    def set_audio_volume(self, volume_level):
        """Ajusta o volume do altifalante da câmara (0 a 100)"""
        # Algumas Mibos usam AudioOut, outras Speaker. Tentamos AudioOut primeiro.
        params = {
            "action": "setConfig",
            "AudioOut[0].Volume": int(volume_level)
        }
        return self._send_command("configManager.cgi", params)

    def toggle_microphone(self, enable=True):
        """Ligar ou desligar a saída de áudio (Altifalante)"""
        state = "true" if enable else "false"
        params = {
            "action": "setConfig",
            "AudioOut[0].Enable": state # Alterado para AudioOut para controlar o som que SAI da câmara
        }
        return self._send_command("configManager.cgi", params)
    
    def get_system_logs(self, start_time, end_time, count=50):
        """
        Puxa os logs internos de erro/sistema da própria câmara.
        Formato da data: "YYYY-MM-DD hh:mm:ss"
        """
        params = {
            "action": "getLog",
            "startTime": start_time,
            "endTime": end_time,
            "count": count
        }
        try:
            url = f"{self.base_url}/logManager.cgi"
            response = requests.get(url, auth=self.auth, params=params, timeout=5)
            if response.status_code == 200:
                # O retorno vem em texto plano, linha a linha.
                return response.text.split('\r\n')
            return []
        except Exception as e:
            print(f"Erro ao buscar logs da Mibo: {e}")
            return []
    def get_events(self):
        """
        Previne o crash da polling_thread no main.py.
        As câmaras Mibo não enviam eventos locais (motion) nativamente da mesma forma 
        que as Intelbras NVR, pelo que devolvemos uma lista vazia.
        """
        return []