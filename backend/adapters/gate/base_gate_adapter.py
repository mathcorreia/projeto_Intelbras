from abc import ABC, abstractmethod


class GateAdapter(ABC):
    """Interface comum para qualquer tipo de portão/cancela."""

    def __init__(self, ip: str, port: int = 80, username: str = None,
                 password: str = None, pulse_time: int = 1):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.pulse_time = pulse_time

    @abstractmethod
    def trigger(self) -> bool:
        """Envia o pulso de abertura/fechamento. Retorna True se bem-sucedido."""
        ...

    @abstractmethod
    def get_status(self) -> str:
        """Retorna o status atual: 'open', 'closed', 'moving', 'unknown'."""
        ...
