"""
Adaptador para módulos de relé e cancelas Intelbras.

Modelos suportados:
  - Intelbras XAL 4000 (módulo de expansão de saída)
  - Intelbras IRS (módulo de entrada/saída)
  - Cancelas com módulo IP Intelbras
  - Câmeras Intelbras/Dahua com saída de alarme (para acionar relé)
  - XPE 8000 Smart (via CGI)

Protocolo: HTTP CGI — mesma interface das câmeras IP Intelbras.
"""

import requests
from requests.auth import HTTPDigestAuth
import logging
from .base_gate_adapter import GateAdapter

logger = logging.getLogger("gate.intelbras_relay")


class IntelbrasRelayAdapter(GateAdapter):

    def __init__(self, *args, relay_channel: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.relay_channel = relay_channel  # canal do relé (1-4 dependendo do módulo)
        self.auth = HTTPDigestAuth(self.username or "admin", self.password or "admin")

    def trigger(self) -> bool:
        """
        Aciona o relé via CGI.
        Tenta múltiplas rotas para compatibilidade entre modelos.
        """
        for strategy in (self._try_alarm_out, self._try_ptz_relay, self._try_relay_cgi):
            if strategy():
                return True
        return False

    def get_status(self) -> str:
        try:
            resp = self._get(
                f"/cgi-bin/configManager.cgi?action=getConfig"
                f"&name=AlarmOut[{self.relay_channel - 1}]"
            )
            if resp:
                if "Enable=true" in resp or "Status=1" in resp:
                    return "open"
                return "closed"
        except Exception:
            pass
        return "unknown"

    # ── Estratégias ───────────────────────────────────────────────────────────

    def _try_alarm_out(self) -> bool:
        """Aciona via saída de alarme (AlarmOut) — mais comum em módulos XAL."""
        ch = self.relay_channel - 1
        params = {
            "action": "setConfig",
            f"AlarmOut[{ch}].Mode": 1,           # modo manual
            f"AlarmOut[{ch}].Enable": "true",
        }
        ok = self._get_params("/cgi-bin/configManager.cgi", params)
        if ok:
            import time
            time.sleep(self.pulse_time)
            # Desliga após pulse_time segundos
            params_off = {
                "action": "setConfig",
                f"AlarmOut[{ch}].Enable": "false",
            }
            self._get_params("/cgi-bin/configManager.cgi", params_off)
        return ok

    def _try_ptz_relay(self) -> bool:
        """Aciona via comando PTZ relay (funciona em algumas câmeras com saída)."""
        params = {
            "action": "start",
            "code": "Relay",
            "arg1": self.relay_channel,
            "arg2": self.pulse_time,
            "arg3": 0,
            "channel": 1,
        }
        return self._get_params("/cgi-bin/ptz.cgi", params)

    def _try_relay_cgi(self) -> bool:
        """Endpoint relay.cgi presente em alguns módulos XPE."""
        params = {"action": "pulse", "channel": self.relay_channel, "time": self.pulse_time}
        return self._get_params("/cgi-bin/relay.cgi", params)

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str) -> str | None:
        try:
            url = f"http://{self.ip}:{self.port}{path}"
            resp = requests.get(url, auth=self.auth, timeout=3)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            logger.debug(f"[Intelbras Relay] {self.ip}: {e}")
        return None

    def _get_params(self, path: str, params: dict) -> bool:
        try:
            url = f"http://{self.ip}:{self.port}{path}"
            resp = requests.get(url, auth=self.auth, params=params, timeout=3)
            return resp.status_code == 200 and "OK" in resp.text
        except Exception as e:
            logger.debug(f"[Intelbras Relay] {self.ip}: {e}")
        return False
