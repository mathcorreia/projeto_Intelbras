"""
Servidor TCP para recepção de eventos de centrais de alarme.

Suporta qualquer central que reporte via Contact ID over IP:
  - Intelbras AMT 2018 EG, AMT 2108 EG, AMT 4010 Smart, AMT 8000 Top
  - DSC PowerSeries, Neo, Impassa
  - Paradox Spectra, SP, EVO, MAGELLAN
  - JFL Aliança IP, Génesis IP
  - IRS / Bosch / Honeywell / Ademco

Uma única porta TCP (padrão 9009) atende múltiplas centrais simultaneamente.
Cada conexão roda em sua própria thread.
A central é identificada por IP de origem; como fallback, usa account number do Contact ID.
"""

import socket
import threading
import binascii
import logging
from datetime import datetime

from database.core import SessionLocal
import crud
import schemas
from .contact_id_decoder import parse_contact_id_frame

logger = logging.getLogger("alarm.tcp")

# Bytes de ACK por protocolo
_ACK_CONTACT_ID = b"\xFE"
_ACK_SIA        = b"\x06"   # ACK genérico SIA


class AlarmTCPReceiver:
    """
    Servidor TCP multi-cliente para recepção de eventos de alarme.

    Uso:
        receiver = AlarmTCPReceiver(port=9009)
        thread = threading.Thread(target=receiver.start, daemon=True)
        thread.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9009):
        self.host = host
        self.port = port
        self._running = False
        self._server_socket: socket.socket | None = None
        self._clients: dict[str, threading.Thread] = {}

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(1.0)  # Permite verificar _running a cada segundo
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(20)

        logger.info(f"[ALARME] Servidor TCP ouvindo em {self.host}:{self.port}")
        print(f"[ALARME] Servidor TCP ouvindo em {self.host}:{self.port}")

        while self._running:
            try:
                conn, addr = self._server_socket.accept()
                t = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True,
                    name=f"alarm-client-{addr[0]}",
                )
                t.start()
                self._clients[addr[0]] = t
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                if self._running:
                    logger.error(f"[ALARME] Erro no accept: {e}")

        if self._server_socket:
            self._server_socket.close()
        logger.info("[ALARME] Servidor encerrado.")

    def stop(self):
        self._running = False

    # ── Handler por cliente (por central) ────────────────────────────────────

    def _handle_client(self, conn: socket.socket, addr: tuple):
        remote_ip, remote_port = addr
        ts = lambda: datetime.now().strftime("%H:%M:%S")

        print(f"[{ts()}] [ALARME] Central conectada: {remote_ip}:{remote_port}")

        with conn:
            conn.settimeout(120)  # 2 min de inatividade → desconecta
            buffer = b""

            while True:
                try:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break

                    buffer += chunk
                    raw_hex = binascii.hexlify(buffer).decode().upper()
                    print(f"[{ts()}] [ALARME] {remote_ip} → {raw_hex}")

                    # Detecta protocolo e envia ACK adequado
                    ack = self._detect_ack(buffer)
                    conn.sendall(ack)

                    # Tenta parsear e persistir o evento
                    parsed = parse_contact_id_frame(buffer, raw_hex=raw_hex)
                    if parsed:
                        self._persist_event(parsed, remote_ip, raw_hex)
                    else:
                        # Frame incompleto ou keepalive — aguarda mais dados
                        # Se o buffer crescer muito sem parse, limpa
                        if len(buffer) > 4096:
                            buffer = b""
                        continue

                    buffer = b""  # Limpa após parse bem-sucedido

                except socket.timeout:
                    # Envia keepalive para manter a central conectada
                    try:
                        conn.sendall(b"\xFE")
                    except Exception:
                        break
                except ConnectionResetError:
                    break
                except Exception as e:
                    logger.warning(f"[ALARME] Erro com {remote_ip}: {e}")
                    break

        print(f"[{ts()}] [ALARME] Central desconectada: {remote_ip}")

    # ── Detecção de protocolo / ACK ───────────────────────────────────────────

    def _detect_ack(self, data: bytes) -> bytes:
        """
        Detecta o protocolo pelo primeiro byte e retorna o ACK correto.
        Contact ID over IP (Intelbras/DSC/Paradox): ACK = 0xFE
        SIA DC-09: ACK = 0x06
        """
        if not data:
            return _ACK_CONTACT_ID
        # SIA DC-09 começa com 0x0A (LF) ou tem a string "SIA" nos primeiros bytes
        if data[0] == 0x0A or b"SIA" in data[:20]:
            return _ACK_SIA
        return _ACK_CONTACT_ID

    # ── Persistência no banco ─────────────────────────────────────────────────

    def _persist_event(self, parsed: dict, remote_ip: str, raw_hex: str):
        db = SessionLocal()
        try:
            central = self._find_central(db, remote_ip, parsed.get("account"))
            if not central:
                print(
                    f"[ALARME] Central não cadastrada — IP: {remote_ip}, "
                    f"Account: {parsed.get('account')}. Cadastre em /alarms/centrals."
                )
                return

            # Resolve zona (0 = sem zona específica)
            zone_id = self._resolve_zone(db, central.id, parsed.get("zone", 0))

            # Persiste evento
            event_schema = schemas.AlarmEventCreate(
                central_id=central.id,
                zone_id=zone_id,
                event_type=parsed["event_description"],
                qualifier=parsed["qualifier_label"],
                raw_data=raw_hex,
            )
            crud.create_alarm_event(db, event_schema)

            # Atualiza status da zona
            if zone_id:
                self._update_zone_status(db, zone_id, parsed)

            print(
                f"[ALARME] ✓ {central.name} | {parsed['qualifier_label']} | "
                f"{parsed['event_description']} | Zona {parsed.get('zone')}"
            )

        except Exception as e:
            logger.error(f"[ALARME] Erro ao persistir evento: {e}")
        finally:
            db.close()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_central(self, db, remote_ip: str, account: str | None):
        """
        Estratégia de identificação (ordem de prioridade):
        1. IP exato da central
        2. Account number igual ao campo 'password' (convenção de cadastro)
        3. Única central ativa (ambientes simples com 1 central)
        """
        centrals = crud.get_alarm_centrals(db)

        # 1 — Por IP
        for c in centrals:
            if c.ip and c.ip.strip() == remote_ip:
                return c

        # 2 — Por account number (usuário pode cadastrar no campo password)
        if account:
            for c in centrals:
                if c.password and c.password.upper() == account.upper():
                    return c

        # 3 — Fallback: única central ativa
        active = [c for c in centrals if c.is_active]
        if len(active) == 1:
            return active[0]

        return None

    def _resolve_zone(self, db, central_id: int, zone_num: int) -> int | None:
        if zone_num <= 0:
            return None
        zones = crud.get_alarm_zones(db, central_id)
        zone = next((z for z in zones if z.zone_number == zone_num), None)
        return zone.id if zone else None

    def _update_zone_status(self, db, zone_id: int, parsed: dict):
        qualifier   = parsed.get("qualifier")
        category    = parsed.get("event_category", "")
        alarm_cats  = {"alarm", "fire", "panic", "medical", "tamper"}

        if qualifier == "1":   # novo evento
            status = "alarm" if category in alarm_cats else "open"
        elif qualifier == "3": # restore
            status = "normal"
        else:
            return  # status não muda para repetições

        crud.update_alarm_zone(db, zone_id, schemas.AlarmZoneUpdate(status=status))
