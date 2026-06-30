"""
Adaptador para portões PPA (Peccinin/PPA).

Modelos suportados:
  - PPA Contatto Wi-Fi
  - PPA Connect Wi-Fi
  - PPA ZipCode  (via módulo Wi-Fi)
  - Peccinin Connect (mesma API)

Protocolo: HTTP GET para o módulo Wi-Fi do motor.
A PPA usa duas APIs alternativas dependendo do firmware:
  - /cgi-bin/operator.cgi  (firmware mais novo)
  - /relay?action=pulse    (firmware legado)
"""

import requests
import re
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import logging
from .base_gate_adapter import GateAdapter

logger = logging.getLogger("gate.ppa")


class PPAAdapter(GateAdapter):

    def trigger(self) -> bool:
        """Tenta as endpoints PPA em ordem até uma funcionar."""
        for strategy in (self._try_cgi, self._try_legacy, self._try_json):
            success = strategy()
            if success:
                return True
        logger.warning(f"[PPA] Nenhuma estratégia funcionou para {self.ip}")
        return False

    def get_status(self) -> str:
        try:
            resp = self._get("/cgi-bin/operator.cgi?action=Get&channel=relay&cmd=status")
            if resp:
                lower = resp.lower()
                if "open" in lower or "aberto" in lower:
                    return "open"
                if "closed" in lower or "fechado" in lower:
                    return "closed"
                if "moving" in lower or "movendo" in lower:
                    return "moving"
        except Exception:
            pass
        return "unknown"

    # ── Estratégias de trigger ────────────────────────────────────────────────

    def _try_cgi(self) -> bool:
        """API CGI padrão PPA/Peccinin."""
        pulse_ms = self.pulse_time * 1000
        path = f"/cgi-bin/operator.cgi?action=Set&channel=relay&cmd=pulse&arg=0&time={pulse_ms}"
        resp = self._get(path)
        return resp is not None and ("OK" in resp or "ok" in resp.lower())

    def _try_legacy(self) -> bool:
        """API legada firmware antigo."""
        path = f"/relay?action=pulse&relay=1&time={self.pulse_time}"
        resp = self._get(path)
        return resp is not None

    def _try_json(self) -> bool:
        """Alguns módulos PPA aceitam JSON POST."""
        try:
            url = f"http://{self.ip}:{self.port}/api/relay/pulse"
            payload = {"relay": 1, "time": self.pulse_time}
            auth = self._get_auth()
            resp = requests.post(url, json=payload, auth=auth, timeout=3)
            return resp.status_code in (200, 201)
        except Exception:
            return False

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _get(self, path: str) -> str | None:
        for auth in (self._get_auth(), None):  # tenta com e sem auth
            try:
                url = f"http://{self.ip}:{self.port}{path}"
                resp = requests.get(url, auth=auth, timeout=3)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                pass
        return None

    def _get_auth(self):
        if self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        return None
