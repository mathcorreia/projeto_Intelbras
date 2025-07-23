from abc import ABC, abstractmethod

class CameraAdapter(ABC):
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    @abstractmethod
    def get_events(self):
        pass