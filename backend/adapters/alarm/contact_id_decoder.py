"""
Contact ID Protocol Decoder (ANSI/SIA DC-05)

Suporta qualquer central que use Contact ID: Intelbras AMT, DSC, Paradox,
Bosch, Honeywell, JFL, IRS, Ademco e qualquer outra marca.

Formato da mensagem:  ACCT  MT  Q  XYZ  GG  ZZZ
                      4 hex 2   1  3    2   3    = 15 chars + 1 check digit
Exemplo: 12341803011001
  ACCT=1234, MT=18, Q=0, Event=301 (Falta AC), Part=10, Zone=001
"""

import re

# ── Tabela de eventos Contact ID ─────────────────────────────────────────────

EVENTS: dict[str, tuple[str, str]] = {
    # Medical
    "100": ("Alarme Médico",              "medical"),
    "101": ("Emergência Pessoal",          "medical"),
    "102": ("Falha de Fumaça",             "medical"),
    # Fire
    "110": ("Alarme de Incêndio",          "fire"),
    "111": ("Fumaça Detectada",            "fire"),
    "112": ("Combustão Detectada",         "fire"),
    "113": ("Fluxo de Água",               "fire"),
    "114": ("Alarme de Calor",             "fire"),
    "115": ("Sensor de Puxar",             "fire"),
    "116": ("Detector de Duto",            "fire"),
    "117": ("Alarme de Chama",             "fire"),
    "118": ("Sensor de CO",                "fire"),
    "119": ("Detector de Gas",             "fire"),
    # Panic
    "120": ("Pânico",                      "panic"),
    "121": ("Coerção / Duress",            "panic"),
    "122": ("Pânico Silencioso",           "panic"),
    "123": ("Pânico Audível",              "panic"),
    # Burglary / Intrusion
    "130": ("Alarme de Intrusão",          "alarm"),
    "131": ("Alarme de Perímetro",         "alarm"),
    "132": ("Alarme Interior",             "alarm"),
    "133": ("Zona 24 Horas",               "alarm"),
    "134": ("Alarme Entrada/Saída",        "alarm"),
    "135": ("Zona Dia/Noite",              "alarm"),
    "136": ("Alarme Externo",              "alarm"),
    "137": ("Tamper / Violação",           "tamper"),
    "138": ("Pré-Alarme",                  "alarm"),
    "139": ("Verificador de Intrusão",     "alarm"),
    "140": ("Alarme Geral",                "alarm"),
    "150": ("Gás Detectado",               "alarm"),
    "151": ("Temperatura Critica",         "alarm"),
    "152": ("Perda de Calor",              "alarm"),
    "154": ("Sensor de Água",              "alarm"),
    "158": ("Sensor de Alta Temperatura",  "alarm"),
    "159": ("Sensor de Baixa Temperatura", "alarm"),
    # Supervisory / 24h
    "200": ("Falha Sistema de Incêndio",   "fault"),
    "201": ("Baixa Pressão",               "fault"),
    "202": ("Baixo CO2",                   "fault"),
    "203": ("Porta do Painel Aberta",      "tamper"),
    "204": ("Falha no Serviço",            "fault"),
    "205": ("Impedância Alta",             "fault"),
    # System troubles
    "300": ("Falha de Sistema",            "fault"),
    "301": ("Falta de Energia AC",         "fault"),
    "302": ("Bateria Fraca / Baixa",       "fault"),
    "303": ("RAM Corrompida",              "fault"),
    "304": ("ROM Corrompida",              "fault"),
    "305": ("Reset do Sistema",            "system"),
    "306": ("Acesso do Instalador",        "system"),
    "307": ("Falha no Auto-Teste",         "fault"),
    "308": ("Desligamento do Sistema",     "system"),
    "309": ("Bateria Ausente",             "fault"),
    "310": ("Falha no Detector",           "fault"),
    "311": ("Falha de Energia no Detector","fault"),
    "312": ("Loop Aberto",                 "fault"),
    "313": ("Loop em Curto",               "fault"),
    "314": ("Falha RF no Incêndio",        "fault"),
    "315": ("Falha de Detector",           "fault"),
    "316": ("Tamper no Detector",          "tamper"),
    "317": ("Loop RF Sem Supervisão",      "fault"),
    "320": ("Falha na Sirene",             "fault"),
    "321": ("Falha na Campainha",          "fault"),
    "330": ("Problema no Sistema",         "fault"),
    "331": ("Problema na Zona",            "fault"),
    "332": ("Problema na Alimentação",     "fault"),
    "333": ("Problema de RF",              "fault"),
    "334": ("Falha de Comunicação",        "fault"),
    "336": ("Falha no Expansor",           "fault"),
    "337": ("Falha no Módulo",             "fault"),
    "338": ("Problema no Relógio",         "fault"),
    "339": ("Sirene em Aberto",            "fault"),
    "344": ("Problema de RF",              "fault"),
    "345": ("Perda de RF na Central",      "fault"),
    "350": ("Falha de Comunicação",        "fault"),
    "351": ("Overflow Buffer Telefônico",  "fault"),
    "352": ("Perda de Sinal RF",           "fault"),
    "353": ("Linha Telefônica Longa",      "fault"),
    "354": ("Falha de Comunicação 2",      "fault"),
    "355": ("Falha no Receptor GSM",       "fault"),
    "356": ("Perda de Rota",               "fault"),
    "357": ("Falha de Iniciação",          "fault"),
    "360": ("Expansor de Zona Offline",    "fault"),
    "370": ("Proteção de Perímetro",       "fault"),
    "371": ("Perturbação de Rede",         "fault"),
    # Arm / Disarm
    "400": ("Armado/Desarmado",            "arm"),
    "401": ("Armado Manual",               "arm"),
    "402": ("Armado Automático",           "arm"),
    "403": ("Armado por Pânico",           "arm"),
    "404": ("Saída do Modo Teste",         "system"),
    "405": ("Armado por Sensor",           "arm"),
    "406": ("Cancelamento por Usuário",    "system"),
    "407": ("Armado/Desarmado Remoto",     "arm"),
    "408": ("Armado Rápido",               "arm"),
    "409": ("Armado por Teclado",          "arm"),
    "411": ("Desarmado — Alarme Anterior", "disarm"),
    "412": ("Desarmado pelo Usuário",      "disarm"),
    "413": ("Armado por Horário",          "arm"),
    "414": ("Desarmado por Horário",       "disarm"),
    "418": ("Armado Parcial",              "arm"),
    "441": ("Armado Presente (Stay)",      "arm"),
    "442": ("Armado Ausente (Away)",       "arm"),
    # Bypass
    "570": ("Bypass de Zona",              "bypass"),
    "571": ("Bypass por Incêndio",         "bypass"),
    "572": ("Bypass Manual de Incêndio",   "bypass"),
    # Test / Maintenance
    "574": ("Entrada no Modo Teste",       "system"),
    "575": ("Saída do Modo Teste",         "system"),
    "601": ("Teste Manual",                "test"),
    "602": ("Teste Periódico",             "test"),
    "603": ("Falha no Teste Periódico",    "fault"),
    "604": ("Relatório de Incêndio",       "test"),
    "605": ("Alarme de Supervisão",        "test"),
    "606": ("Teste do Sistema",            "test"),
    "607": ("Entrada em Programação",      "system"),
    "608": ("Saída de Programação",        "system"),
}

QUALIFIER_LABELS = {
    "1": "Evento Novo",
    "3": "Restaurado / Fim",
    "6": "Status / Repetição",
}

# ── Contact ID checksum ───────────────────────────────────────────────────────

_CID_DIGIT_VALUE = {str(i): i for i in range(10)}
_CID_DIGIT_VALUE.update({"A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 0})


def _checksum_valid(message: str) -> bool:
    """Soma de todos os dígitos CID deve ser divisível por 15."""
    total = sum(_CID_DIGIT_VALUE.get(c, 0) for c in message.upper())
    return total % 15 == 0


# ── Parsers ───────────────────────────────────────────────────────────────────

# Regex para Contact ID em ASCII/texto: AAAA MT Q EEE GG ZZZ [check]
_CID_PATTERN = re.compile(
    r"([0-9A-Fa-f]{4})"   # account
    r"(18|98)"             # message type (18 = Contact ID, 98 = optional)
    r"([136])"             # qualifier
    r"([0-9A-Fa-f]{3})"   # event code
    r"([0-9A-Fa-f]{2})"   # partition
    r"([0-9A-Fa-f]{3})"   # zone/user
)


def parse_contact_id_frame(data: bytes, raw_hex: str = "") -> dict | None:
    """
    Extrai e decodifica uma mensagem Contact ID de um frame binário.
    Tenta múltiplas estratégias para máxima compatibilidade.
    """
    # 1 — Tenta decodificar como ASCII/UTF-8 e buscar o padrão Contact ID
    result = _try_ascii(data)
    if result:
        return result

    # 2 — Tenta interpretar os bytes como BCD (Contact ID binário)
    result = _try_bcd(data)
    if result:
        return result

    # 3 — Tenta no hex string em si (alguns receivers encapsulam em hex ASCII)
    if raw_hex:
        result = _try_ascii(raw_hex.encode())
        if result:
            return result

    return None


def _try_ascii(data: bytes) -> dict | None:
    try:
        text = data.decode("ascii", errors="ignore").upper()
        match = _CID_PATTERN.search(text)
        if match:
            account, mt, qualifier, event_code, partition, zone = match.groups()
            full_msg = "".join(match.groups())
            # checksum opcional — não rejeita se inválido (alguns firmwares omitem)
            return _build_event(account, qualifier, event_code, partition, zone, full_msg)
    except Exception:
        pass
    return None


def _try_bcd(data: bytes) -> dict | None:
    """
    Muitas centrais enviam Contact ID em BCD empacotado.
    Formato típico Intelbras/Paradox:
      [HEADER 1-2 bytes] [ACCT 2 bytes BCD] [0x18] [Q|XYZ 2 bytes] [GG] [ZZZ 2 bytes] [checksum]
    """
    if len(data) < 8:
        return None
    try:
        # Varre o payload procurando 0x18 (indicador Contact ID)
        for i in range(len(data) - 7):
            if data[i + 2] == 0x18:  # MT byte
                acct_bcd = data[i: i + 2]
                qualifier_byte = data[i + 3]
                event_hi = data[i + 4]
                event_lo_part = data[i + 5] >> 4
                partition_lo = data[i + 5] & 0x0F
                partition = data[i + 5] & 0x0F
                zone_hi = data[i + 6]
                zone_lo = data[i + 7] if i + 7 < len(data) else 0

                account = f"{acct_bcd[0]:02X}{acct_bcd[1]:02X}"
                qualifier = str((qualifier_byte >> 4) & 0x0F)
                event_code = f"{qualifier_byte & 0x0F:01X}{event_hi:02X}"
                part = f"{(data[i+5] >> 4):01X}{data[i+5] & 0x0F:01X}"
                zone_str = f"{zone_hi >> 4:01X}{zone_hi & 0x0F:01X}{zone_lo >> 4:01X}"

                if qualifier in ("1", "3", "6"):
                    return _build_event(account, qualifier, event_code, part, zone_str, "")
    except Exception:
        pass
    return None


def _build_event(account: str, qualifier: str, event_code: str,
                 partition: str, zone: str, raw_msg: str) -> dict:
    code_upper = event_code.upper()
    description, category = EVENTS.get(code_upper, (f"Evento {code_upper}", "unknown"))

    # Converte zona e partição de hex para int
    try:
        zone_int = int(zone, 16)
    except ValueError:
        zone_int = 0
    try:
        partition_int = int(partition, 16)
    except ValueError:
        partition_int = 0

    return {
        "account":           account.upper(),
        "qualifier":         qualifier,
        "qualifier_label":   QUALIFIER_LABELS.get(qualifier, qualifier),
        "event_code":        code_upper,
        "event_description": description,
        "event_category":    category,
        "partition":         partition_int,
        "zone":              zone_int,
        "raw_message":       raw_msg,
    }


def decode_event_code(code: str) -> tuple[str, str]:
    """Retorna (descrição, categoria) para um código de evento."""
    return EVENTS.get(code.upper(), (f"Evento Desconhecido ({code})", "unknown"))
