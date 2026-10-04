"""
Adaptador HTTP para Intelbras AMT com interface de rede.

Modelos suportados:
  - AMT 8000 Top / AMT 8000 IP
  - AMT 4010 Smart / AMT 4010 IP
  - AMT 2018 EG (com módulo Ethernet XEG 4000 Smart)
  - Qualquer AMT com acesso via painel web HTTP

Para centrais sem interface IP (apenas discagem), use o tcp_receiver.py.
"""

import requests
import re
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger("alarm.intelbras_http")

# Mapeamento de códigos de status da tela principal do AMT
_STATUS_LABELS = {
    "armed":    "Armado",
    "disarmed": "Desarmado",
    "alarm":    "Em Alarme",
    "partial":  "Armado Parcial",
    "fault":    "Falha",
}


class IntelbrasHTTPAdapter:
    """
    Adaptador para controle e monitoramento de centrais Intelbras via HTTP.
    Usa a API CGI exposta pelo firmware AMT.
    """

    def __init__(self, ip: str, username: str = "admin", password: str = "admin", port: int = 80):
        self.ip = ip
        self.port = port
        self.base_url = f"http://{ip}:{port}"
        self.auth = HTTPDigestAuth(username, password)

    # ── Status geral ─────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """
        Retorna o status atual da central: partições armadas, zonas abertas, falhas.
        """
        try:
            resp = self._get("/cgi-bin/alarmManager.cgi?action=getStatus")
            if resp:
                return self._parse_status(resp)
        except Exception as e:
            logger.warning(f"[AMT HTTP] Erro ao buscar status de {self.ip}: {e}")
        return {"online": False}

    def get_zones(self) -> list[dict]:
        """
        Lista todas as zonas da central com nome e status.
        """
        try:
            resp = self._get("/cgi-bin/alarmManager.cgi?action=getZoneStatus")
            if resp:
                return self._parse_zones(resp)
        except Exception as e:
            logger.warning(f"[AMT HTTP] Erro ao buscar zonas de {self.ip}: {e}")
        return []

    def get_events(self, count: int = 50) -> list[dict]:
        """
        Busca os últimos N eventos do log interno da central.
        """
        try:
            resp = self._get(
                f"/cgi-bin/alarmManager.cgi?action=getAlarmLog&count={count}"
            )
            if resp:
                return self._parse_events(resp)
        except Exception as e:
            logger.warning(f"[AMT HTTP] Erro ao buscar eventos de {self.ip}: {e}")
        return []

    # ── Comandos de controle ──────────────────────────────────────────────────

    def arm(self, partition: int = 1) -> bool:
        """Arma a partição especificada."""
        return self._command(f"arm&partition={partition}")

    def disarm(self, partition: int = 1) -> bool:
        """Desarma a partição especificada."""
        return self._command(f"disarm&partition={partition}")

    def arm_stay(self, partition: int = 1) -> bool:
        """Arma em modo presente (Stay)."""
        return self._command(f"armstay&partition={partition}")

    def bypass_zone(self, zone_number: int) -> bool:
        """Isola (bypass) a zona especificada."""
        return self._command(f"bypass&zone={zone_number}")

    def unbypass_zone(self, zone_number: int) -> bool:
        """Remove o isolamento da zona."""
        return self._command(f"unbypass&zone={zone_number}")

    def silence_alarm(self) -> bool:
        """Silencia o alarme (sem desarmar)."""
        return self._command("silence")

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str) -> str | None:
        try:
            resp = requests.get(
                f"{self.base_url}{path}",
                auth=self.auth,
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.text
            logger.debug(f"[AMT HTTP] {self.ip} → HTTP {resp.status_code} em {path}")
        except requests.exceptions.Timeout:
            logger.warning(f"[AMT HTTP] Timeout ao conectar em {self.ip}")
        except Exception as e:
            logger.warning(f"[AMT HTTP] {self.ip}: {e}")
        return None

    def _command(self, action: str) -> bool:
        resp = self._get(f"/cgi-bin/alarmManager.cgi?action={action}")
        success = resp is not None and "OK" in resp
        logger.info(f"[AMT HTTP] {self.ip} → {action} → {'OK' if success else 'FALHOU'}")
        return success

    # ── Parsers de resposta ───────────────────────────────────────────────────

    def _parse_status(self, text: str) -> dict:
        """
        Resposta típica do AMT:
          status=armed
          fault=0
          alarm=0
          partition[0].status=armed
        """
        result: dict = {"online": True, "partitions": [], "fault": False, "alarm": False}

        for line in text.splitlines():
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip()

            if key == "fault":
                result["fault"] = value != "0"
            elif key == "alarm":
                result["alarm"] = value != "0"
            elif "partition" in key and "status" in key:
                idx_match = re.search(r"\[(\d+)\]", key)
                idx = int(idx_match.group(1)) if idx_match else 0
                result["partitions"].append({
                    "index": idx,
                    "status": value,
                    "label": _STATUS_LABELS.get(value.lower(), value),
                })

        if not result["partitions"]:
            # Resposta simples sem partições
            for line in text.splitlines():
                key, _, value = line.partition("=")
                if key.strip().lower() == "status":
                    result["status"] = _STATUS_LABELS.get(value.strip().lower(), value.strip())
                    break

        return result

    def _parse_zones(self, text: str) -> list[dict]:
        """
        Resposta típica:
          zone[0].name=Sala
          zone[0].status=normal
          zone[1].name=Garagem
          zone[1].status=open
        """
        zones: dict[int, dict] = {}

        for line in text.splitlines():
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip()

            idx_match = re.search(r"zone\[(\d+)\]\.(\w+)", key)
            if idx_match:
                idx = int(idx_match.group(1))
                field = idx_match.group(2)
                if idx not in zones:
                    zones[idx] = {"number": idx + 1}
                zones[idx][field] = value

        return list(zones.values())

    def _parse_events(self, text: str) -> list[dict]:
        """
        Resposta típica:
          log[0].time=2024-01-15 10:30:00
          log[0].type=alarm
          log[0].zone=2
          log[0].description=Alarme de Intrusão
        """
        events: dict[int, dict] = {}

        for line in text.splitlines():
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip()

            idx_match = re.search(r"log\[(\d+)\]\.(\w+)", key)
            if idx_match:
                idx = int(idx_match.group(1))
                field = idx_match.group(2)
                if idx not in events:
                    events[idx] = {}
                events[idx][field] = value

        return list(events.values())
