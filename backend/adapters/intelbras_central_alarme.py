import socket
import binascii
import time

# Configurações do teu Servidor (Mac)
HOST = '0.0.0.0'  # Escuta em todas as redes do teu Mac
PORT = 9009       # A porta que configuraste no AMT Remoto

def start_receiver():
    print("==================================================")
    print(f"🛡️  Servidor KOREON TECH - Receptor Intelbras")
    print(f"📡  Escutando na porta TCP: {PORT}")
    print("==================================================")
    print("A aguardar conexão da central AMT 2018 EG (esperado de 192.168.15.8)...\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Evita o erro "Address already in use" ao reiniciar o script
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        while True:
            try:
                conn, addr = s.accept()
                print(f"[{time.strftime('%H:%M:%S')}] ✅ [CONECTADO] Central ligada a partir de: {addr[0]}:{addr[1]}")
                
                with conn:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            print(f"[{time.strftime('%H:%M:%S')}] ❌ [DESCONECTADO] A central fechou a conexão.\n")
                            break
                        
                        # Formata os dados puros recebidos para Hexadecimal legível
                        hex_data = binascii.hexlify(data).decode('utf-8').upper()
                        print(f"[{time.strftime('%H:%M:%S')}] 📥 [RECEBIDO] Raw Hex: {hex_data}")
                        
                        # Envia o ACK (0xFE) para a Intelbras saber que o nosso software está online
                        conn.sendall(b'\xFE')
                        print(f"[{time.strftime('%H:%M:%S')}] 📤 [ACK ENVIADO] Resposta de confirmação (FE) enviada.")
                        print("-" * 50)
                        
            except ConnectionResetError:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ [ERRO] Conexão reiniciada pela central.\n")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] 🚨 [ERRO INESPERADO] {e}\n")

if __name__ == "__main__":
    try:
        start_receiver()
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado manualmente.")