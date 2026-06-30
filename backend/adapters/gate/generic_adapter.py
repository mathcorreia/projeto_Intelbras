"""
Adaptador genérico para qualquer módulo de relé/portão com HTTP.

Cobre uma ampla gama de dispositivos IoT:
  - Módulos ESP8266/ESP32 com firmware Tasmota
  - Relés Arduino com servidor HTTP
  - Módulos genéricos chineses (Sonoff, ITEAD)
  - Control iD iDBlock, iDFace (porta de acesso)
  - Hikvision DS-K2800 (access control, via ISAPI)
  - Qualquer relay HTTP sem autenticação ou com Basic Auth

Estratégia: tenta múltiplos endpoints conhecidos em ordem.
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import logging
from .base_gate_adapter import GateAdapter

logger = logging.getLogger("gate.generic")

# Endpoints testados em ordem — primeiro match que responder 200 vence
_PULSE_ENDPOINTS = [
    # Tasmota
    "/cm?cmnd=Power%20TOGGLE",
    "/cm?cmnd=Power1%20TOGGLE",
    # ESP genérico
    "/relay/0/trigger",
    "/relay/pulse",
    "/gate/open",
    "/door/open",
    # Sonoff Basic
    "/switch/toggle",
    # Control iD (ISAPI)
    "/ISAPI/AccessControl/RemoteControl/door/1",
    # Hikvision ISAPI
    "/ISAPI/AccessControl/door/capabilities",
    # Genérico
    "/api/relay/pulse",
    "/api/door/open",
    "/open",
    "/trigger",
]

_STATUS_ENDPOINTS = [
    "/cm?cmnd=Power%20Status",
    "/relay/0/status",
    "/api/relay/status",
    "/status",
]


class GenericHTTPGateAdapter(GateAdapter):

    def trigger(self) -> bool:
        auth_methods = [self._build_auth("basic"), self._build_auth("digest"), None]

        for endpoint in _PULSE_ENDPOINTS:
            for auth in auth_methods:
                try:
                    url = f"http://{self.ip}:{self.port}{endpoint}"
                    resp = requests.get(url, auth=auth, timeout=2)
                    if resp.status_code in (200, 204):
                        logger.info(f"[Generic Gate] {self.ip} → {endpoint} OK")
                        return True
                    # Alguns endpoints aceitam POST
                    resp = requests.post(url, auth=auth, timeout=2)
                    if resp.status_code in (200, 204):
                        logger.info(f"[Generic Gate] {self.ip} POST→ {endpoint} OK")
                        return True
                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue

        logger.warning(f"[Generic Gate] Nenhum endpoint respondeu em {self.ip}:{self.port}")
        return False

    def get_status(self) -> str:
        for endpoint in _STATUS_ENDPOINTS:
            try:
                url = f"http://{self.ip}:{self.port}{endpoint}"
                resp = requests.get(url, auth=self._build_auth("basic"), timeout=2)
                if resp.status_code == 200:
                    lower = resp.text.lower()
                    if any(k in lower for k in ("open", "on", "1", "aberto")):
                        return "open"
                    if any(k in lower for k in ("closed", "off", "0", "fechado")):
                        return "closed"
            except Exception:
                continue
        return "unknown"

    def _build_auth(self, method: str):
        if not self.username:
            return None
        if method == "digest":
            return HTTPDigestAuth(self.username, self.password or "")
        return HTTPBasicAuth(self.username, self.password or "")
