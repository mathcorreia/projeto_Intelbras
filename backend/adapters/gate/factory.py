"""
Factory de adaptadores de portão.

O campo `brand` do modelo Gate determina qual adaptador é usado.
Valores válidos (case-insensitive):
  ppa, peccinin         → PPAAdapter
  intelbras, dahua      → IntelbrasRelayAdapter
  generic, tasmota,
  sonoff, esp, arduino  → GenericHTTPGateAdapter
  (qualquer outro)      → GenericHTTPGateAdapter (fallback seguro)
"""

from .ppa_adapter import PPAAdapter
from .intelbras_relay_adapter import IntelbrasRelayAdapter
from .generic_adapter import GenericHTTPGateAdapter
from .base_gate_adapter import GateAdapter


def get_gate_adapter(gate) -> GateAdapter:
    """
    Cria o adaptador correto para um objeto Gate do banco.
    `gate` é uma instância de models.Gate ou qualquer objeto com os campos:
      ip, port, username, password, pulse_time, brand
    """
    brand = (gate.brand or "").lower().strip()

    common = dict(
        ip=gate.ip,
        port=gate.port or 80,
        username=gate.username,
        password=gate.password,
        pulse_time=gate.pulse_time or 1,
    )

    if brand in ("ppa", "peccinin"):
        return PPAAdapter(**common)

    if brand in ("intelbras", "dahua", "intelbras_relay"):
        return IntelbrasRelayAdapter(**common)

    # Fallback genérico — tenta múltiplos endpoints
    return GenericHTTPGateAdapter(**common)
