from .silver_adapter import SilverCameraAdapter
# IMPORTANTE: Quando tiver o SDK real, troque o 'mock_intelbras_sdk' pelo nome do pacote real.
import adapters.mock_intelbras_sdk as intelbras_sdk

class GoldCameraAdapter(SilverCameraAdapter):
    def __init__(self, ip, user, password):
        # Inicializa a classe pai (Silver), que já conecta ao SDK
        super().__init__(ip, user, password)
        print("Adaptador GOLD em uso.")

    def get_events(self):
        # Pega os eventos básicos (linha/cerca) da classe pai
        events = super().get_events()
        
        # Pega os eventos de reconhecimento facial
        face_events = intelbras_sdk.get_face_recognition_events()
        
        for event in face_events:
            # Para cada evento facial, busca os atributos
            attributes = intelbras_sdk.get_attributes_from_snapshot(event["snapshot"])
            event["attributes"] = attributes
        
        # Combina todos os eventos
        all_events = events + face_events
        return all_events