from .base_adapter import CameraAdapter
# IMPORTANTE: Quando tiver o SDK real, troque o 'mock_intelbras_sdk' pelo nome do pacote real.
import adapters.mock_intelbras_sdk as intelbras_sdk

class SilverCameraAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        print("Adaptador SILVER em uso.")
        self.sdk_client = intelbras_sdk.connect(ip, user, password)

    def get_events(self):
        # Chama a função do SDK para obter eventos de IA
        events = intelbras_sdk.get_ia_events()
        # No SDK real, talvez você precise formatar os dados para o padrão do nosso sistema
        return events