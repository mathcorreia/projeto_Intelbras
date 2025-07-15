import random
import datetime

def connect(ip, user, password):
    print(f"[SDK MOCK] Conectando a {ip} com usuário {user}...")
    return True

def get_ia_events():
    """Simula eventos de IA Básica (Nível Prata)"""
    if random.random() > 0.8: # 20% de chance de gerar um evento
        return [{
            "type": "line_crossing",
            "timestamp": datetime.datetime.now().isoformat(),
            "snapshot": "path/to/snapshot_intrusion.jpg"
        }]
    return []

def get_face_recognition_events():
    """Simula eventos de Reconhecimento Facial (Nível Ouro)"""
    if random.random() > 0.7: # 30% de chance de gerar um evento
        person_id = random.choice([1, 2, 3])
        names = {1: "Alice", 2: "Beto", 3: "Carla"}
        return [{
            "type": "face_recognition",
            "person_id": person_id,
            "name": names[person_id],
            "timestamp": datetime.datetime.now().isoformat(),
            "snapshot": f"path/to/face_{names[person_id]}.jpg"
        }]
    return []

def get_attributes_from_snapshot(snapshot):
    """Simula a extração de atributos de um snapshot (Nível Ouro)"""
    return {
        "gender": random.choice(["Masculino", "Feminino"]),
        "age_range": random.choice(["20-30", "30-40", "40-50"]),
        "expression": random.choice(["Neutra", "Feliz", "Surpresa"])
    }