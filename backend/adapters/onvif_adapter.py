from .base_adapter import CameraAdapter
from datetime import datetime
from onvif import ONVIFCamera # type: ignore
import json
import base64
import os
import random

# Cria uma pasta na raiz do backend para salvar as imagens das faces
FACE_IMAGE_DIR = "face_images"
os.makedirs(FACE_IMAGE_DIR, exist_ok=True)

class OnvifAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        self.cam = None
        try:
            # Em um ambiente de produção, você pode precisar especificar o diretório WSDL
            # wsdl_dir='/path/to/your/onvif/wsdl'
            self.cam = ONVIFCamera(ip, 80, user, password)
            self.event_service = self.cam.create_events_service()
            print(f"ONVIF: Conectado e serviço de eventos criado para {ip}")
        except Exception as e:
            print(f"ERRO ONVIF em {ip}: {e}")

    def get_events(self):
        if not self.cam:
            return []

        # ======================================================================
        # NOTA: A lógica abaixo é uma SIMULAÇÃO.
        # Você precisará substituí-la pela chamada ONVIF real para sua câmera,
        # que geralmente envolve `PullMessages` ou um listener de eventos.
        # Consulte a documentação da sua câmera e da biblioteca `onvif-zeep`.
        # ======================================================================

        # Simula a recepção de um evento de reconhecimento facial aleatoriamente
        if random.random() > 0.7: # Acontece em 30% das vezes
            print("Simulando evento de reconhecimento facial...")
            # Imagem de 1x1 pixel em Base64 para teste
            fake_image_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            
            simulated_onvif_event = {
                'topic': 'tns1:RuleEngine/MyFaceRecognitionRule/FaceDetected',
                'data': {
                    'Name': 'Usuario Exemplo',
                    'CPF': '111.222.333-44',
                    'ImageBase64': fake_image_b64
                }
            }
            return self.parse_onvif_event(simulated_onvif_event)
        
        return []

    def parse_onvif_event(self, event):
        topic = event.get('topic', '')
        data = event.get('data', {})
        
        # Processa eventos de Reconhecimento Facial
        if 'FaceRecognition' in topic or 'FaceDetected' in topic:
            person_name = data.get("Name", "Desconhecido")
            metadata = {
                "nome": person_name,
                "cpf": data.get("CPF", "N/A"),
            }
            
            face_path = None
            if data.get('ImageBase64'):
                face_path = self.save_face_image(data['ImageBase64'], person_name)

            return [{
                'type': 'Reconhecimento Facial',
                'event_data': json.dumps(metadata), # Salva como texto JSON
                'face_image_path': face_path
            }]

        return []

    def save_face_image(self, b64_string, person_name):
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            # Limpa o nome para usar em um nome de arquivo seguro
            safe_name = "".join(c for c in person_name if c.isalnum() or c in (' ',)).rstrip()
            filename = f"{timestamp}-{safe_name.replace(' ', '_')}.jpg"
            filepath = os.path.join(FACE_IMAGE_DIR, filename)
            
            image_data = base64.b64decode(b64_string)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"Imagem da face salva em: {filepath}")
            return filename
        except Exception as e:
            print(f"Erro ao salvar imagem da face: {e}")
            return None