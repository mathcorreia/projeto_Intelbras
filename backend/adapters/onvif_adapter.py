from .base_adapter import CameraAdapter
from onvif import ONVIFCamera
from datetime import datetime
import random

class OnvifAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        self.cam = None
        try:
            # Tenta conectar na porta 80, a mais comum para ONVIF
            self.cam = ONVIFCamera(ip, 80, user, password)
            print(f"Sucesso ao conectar via ONVIF em {ip}")
        except Exception as e:
            print(f"ERRO ONVIF em {ip}: {e}")

    def get_events(self):
        if not self.cam:
            return []

        # SIMULAÇÃO: No mundo real, você usaria o serviço de eventos do ONVIF.
        # Por simplicidade, vamos simular um evento aleatório.
        if random.random() > 0.5:
            print(f"ONVIF Adapter: Evento simulado para {self.ip}")
            return [{'type': 'Motion_ONVIF', 'timestamp': datetime.now().isoformat()}]
        return []