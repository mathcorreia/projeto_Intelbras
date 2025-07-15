from .base_adapter import CameraAdapter

class BronzeCameraAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        print("Adaptador BRONZE em uso.")

    # Não faz nada, pois câmeras bronze não geram eventos de IA.
    def get_events(self):
        return super().get_events()