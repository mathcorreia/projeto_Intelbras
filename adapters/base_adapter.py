class CameraAdapter:
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password
        print(f"Adaptador base inicializado para {self.ip}")

    def get_events(self):
        return []