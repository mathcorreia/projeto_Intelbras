from .base_adapter import CameraAdapter
import os

class BronzeCameraAdapter(CameraAdapter):
    def get_events(self):
        # Simula um "ping"
        response = os.system(f"ping -c 1 {self.ip}") # -n 1 no Windows
        if response == 0:
            return [] # Sem eventos, mas está online
        return [{'type': 'Offline'}]