from .base_adapter import CameraAdapter
from onvif import ONVIFCamera
from datetime import datetime
import json
import base64
import os
import zeep # Mantemos para ajudar a depurar se necessário

FACE_IMAGE_DIR = "face_images"
os.makedirs(FACE_IMAGE_DIR, exist_ok=True)

class OnvifAdapter(CameraAdapter):
    def __init__(self, ip, user, password):
        super().__init__(ip, user, password)
        self.cam = None
        self.pull_point = None
        try:
            self.cam = ONVIFCamera(ip, 80, user, password)
            self.event_service = self.cam.create_events_service()
            subscription = self.event_service.CreatePullPointSubscription()
            self.pull_point = subscription.SubscriptionReference.Address
            print(f"ONVIF: Subscrição de eventos reais criada com sucesso para a câmara em {ip}")
        except Exception as e:
            print(f"ERRO ONVIF na inicialização em {ip}: {e}")

    def get_events(self):
        if not self.pull_point:
            return []

        try:
            # 1. Pede os eventos reais à câmara
            print("A aguardar por eventos reais da câmara...")
            messages = self.event_service.PullMessages({
                'Timeout': 'PT10S', # Espera até 10 segundos
                'MessageLimit': 10
            })

            all_parsed_events = []
            if messages and hasattr(messages, 'NotificationMessage'):
                for event in messages.NotificationMessage:
                    # 2. Envia cada evento real para ser processado
                    parsed_event = self.parse_real_onvif_event(event)
                    if parsed_event:
                        all_parsed_events.extend(parsed_event)

            # 3. Retorna os eventos processados para o main.py
            return all_parsed_events

        except Exception as e:
            print(f"ERRO ao puxar mensagens ONVIF: {e}")
            return []

    def parse_real_onvif_event(self, event):
        # ======================================================================
        # ESTA É A FUNÇÃO DE TRADUÇÃO - PODE PRECISAR DE AJUSTES
        # Com base nos dados reais que a sua câmara enviar, talvez seja
        # preciso alterar os nomes dos campos (ex: 'Name' para 'PersonName').
        # ======================================================================
        try:
            topic = event.Topic._value_1
            data_items = event.Message.Message.Data.SimpleItem

            # --- Lógica para Contagem de Pessoas ---
            if 'PeopleCounter' in topic or 'CrowdDetection' in topic:
                for item in data_items:
                    if item.Name == 'PersonCount' or item.Name == 'Number':
                        count_data = {'total': int(item.Value)}
                        return [{'type': 'Contagem de Pessoas', 'event_data': json.dumps(count_data)}]

            # --- Lógica para Reconhecimento/Deteção Facial ---
            elif 'FaceRecognition' in topic or 'FaceDetection' in topic:
                event_type = 'Reconhecimento Facial'
                person_name, cpf, feicao, image_b64 = "Desconhecido", None, {}, None

                for item in data_items:
                    if item.Name in ['Name', 'PersonName']: person_name = item.Value
                    if item.Name in ['CPF', 'RegistryID']: cpf = item.Value
                    if item.Name == 'Gender': feicao['genero'] = item.Value
                    if item.Name == 'Age': feicao['idade_aparente'] = item.Value
                    if item.Name == 'FaceImage': image_b64 = item.Value

                if person_name == "Desconhecido":
                    event_type = 'Pessoa Desconhecida'

                event_metadata = {"nome": person_name, "cpf": cpf, "feicao": feicao}
                face_path = self.save_face_image(image_b64, person_name) if image_b64 else None

                return [{'type': event_type, 'event_data': json.dumps(event_metadata), 'face_image_path': face_path}]

        except Exception:
            print("\n--- ERRO AO PROCESSAR EVENTO ---")
            print("Não foi possível processar o evento com a lógica atual.")
            print("DADOS BRUTOS RECEBIDOS DA CÂMARA:")
            print(zeep.helpers.serialize_object(event))
            print("--- FIM DO ERRO ---\n")

        return None

    def save_face_image(self, b64_string, person_name):
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            safe_name = "".join(c for c in person_name if c.isalnum()).rstrip()
            filename = f"{timestamp}-{safe_name}.jpg"
            filepath = os.path.join(FACE_IMAGE_DIR, filename)
            image_data = base64.b64decode(b64_string)
            with open(filepath, 'wb') as f: f.write(image_data)
            return filename
        except Exception as e:
            print(f"Erro ao salvar imagem da face: {e}")
            return None