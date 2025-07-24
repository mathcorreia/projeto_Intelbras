from .base_adapter import CameraAdapter
from onvif import ONVIFCamera
import zeep # Usado para inspecionar os dados recebidos da câmara
import os

# Cria a pasta se ela não existir
FACE_IMAGE_DIR = "face_images"
os.makedirs(FACE_IMAGE_DIR, exist_ok=True)

class OnvifAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        self.cam = None
        self.pull_point = None
        try:
            # Ligação real à sua câmara
            self.cam = ONVIFCamera(ip, 80, user, password)
            self.event_service = self.cam.create_events_service()
            
            # Cria uma "assinatura" para receber os eventos da câmara
            subscription = self.event_service.CreatePullPointSubscription()
            # Guarda o endereço para "puxar" as mensagens
            self.pull_point = subscription.SubscriptionReference.Address
            
            print(f"ONVIF: Subscrição de eventos criada com sucesso para a câmara em {ip}")
        except Exception as e:
            print(f"ERRO ONVIF na inicialização em {ip}: {e}")

    def get_events(self):
        # Esta função será chamada em loop pelo seu main.py
        if not self.pull_point:
            return []
        
        try:
            # Esta é a chamada REAL que pede os eventos à câmara
            print("A aguardar por eventos da câmara...")
            messages = self.event_service.PullMessages({
                'Timeout': 'PT20S',  # Espera até 20 segundos por um evento
                'MessageLimit': 10   # Pega no máximo 10 eventos de uma vez
            })

            # Se a câmara enviou alguma mensagem, vamos imprimi-la
            if messages and hasattr(messages, 'NotificationMessage'):
                print("\n" + "="*20 + " EVENTO REAL RECEBIDO DA CÂMARA " + "="*20)
                for event in messages.NotificationMessage:
                    # Imprime o evento completo para podermos analisá-lo
                    print(zeep.helpers.serialize_object(event))
                print("="*64 + "\n")

            # Por agora, não vamos enviar nada para o frontend, apenas investigar
            return []

        except Exception as e:
            print(f"ERRO ao puxar mensagens ONVIF: {e}")
            # Em caso de erro, pode ser necessário recriar a subscrição
            self.pull_point = None 
            return []