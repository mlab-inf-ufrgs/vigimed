import re
import unicodedata
from typing import Mapping, Tuple

import numpy as np
import pandas as pd

def _normalize_text(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


UNKNOWN_LABEL = "desconhecido"
UNKNOWN_CODE = 0

_NUMBER_UNIT_RE = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*(.*)$")
_POR_SPLIT_RE = re.compile(r"\s+por\s+")

_FREQ_UNIT_SPECS = [
    {
        "label": "segundo",
        "category": "time",
        "aliases": {"segundo", "segundos", "seg", "s"},
    },
    {
        "label": "minuto",
        "category": "time",
        "aliases": {"minuto", "minutos", "min", "mins", "minute", "minutes"},
    },
    {
        "label": "hora",
        "category": "time",
        "aliases": {"hora", "horas", "hr", "h"},
    },
    {
        "label": "dia",
        "category": "time",
        "aliases": {"dia", "dias"},
    },
    {
        "label": "semana",
        "category": "time",
        "aliases": {"semana", "semanas", "sem"},
    },
    {
        "label": "mes",
        "category": "time",
        "aliases": {"mes", "meses", "mensal"},
    },
    {
        "label": "ano",
        "category": "time",
        "aliases": {"ano", "anos", "anual"},
    },
    {
        "label": "decada",
        "category": "time",
        "aliases": {"decada", "decadas", "década", "décadas"},
    },
    {
        "label": "ciclico",
        "category": "special",
        "aliases": {"ciclico", "ciclicos", "ciclica", "ciclicas", "ciclo"},
    },
    {
        "label": "total",
        "category": "special",
        "aliases": {"total", "{total}"},
    },
]

for idx, spec in enumerate(_FREQ_UNIT_SPECS, start=1):
    spec["code"] = idx

_LABEL_TO_SPEC: Mapping[str, dict] = {spec["label"]: spec for spec in _FREQ_UNIT_SPECS}
_ALIAS_TO_LABEL: Mapping[str, str] = {}
for spec in _FREQ_UNIT_SPECS:
    for alias in spec["aliases"] | {spec["label"]}:
        normalized_alias = _normalize_text(alias)
        if normalized_alias:
            _ALIAS_TO_LABEL[normalized_alias] = spec["label"]


def _to_float(token: str) -> float:
    token = token.replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return np.nan


def _split_number_unit(text: str) -> Tuple[float, str]:
    match = _NUMBER_UNIT_RE.match(text)
    if not match:
        return (np.nan, text.strip())
    number = _to_float(match.group(1))
    remainder = match.group(2).strip()
    return (number, remainder)


def _match_unit(text: str):
    key = _normalize_text(text)
    if not key:
        return None
    label = _ALIAS_TO_LABEL.get(key)
    if not label:
        return None
    return _LABEL_TO_SPEC[label]


def _parse_interval_part(text: str):
    value, unit_text = _split_number_unit(text)
    spec = _match_unit(unit_text)
    if spec:
        return (value, spec["label"], spec["code"])
    return (value, UNKNOWN_LABEL, UNKNOWN_CODE)


def _parse_frequency_value(raw) -> Tuple[float, float, str, int]:
    if pd.isna(raw):
        return (np.nan, np.nan, UNKNOWN_LABEL, UNKNOWN_CODE)

    text = str(raw).strip()
    if not text:
        return (np.nan, np.nan, UNKNOWN_LABEL, UNKNOWN_CODE)

    normalized = _normalize_text(text)
    if not normalized:
        return (np.nan, np.nan, UNKNOWN_LABEL, UNKNOWN_CODE)

    direct_spec = _match_unit(normalized)
    if direct_spec:
        if direct_spec["category"] == "time":
            return (1.0, 1.0, direct_spec["label"], direct_spec["code"])
        return (1.0, np.nan, direct_spec["label"], direct_spec["code"])

    if _POR_SPLIT_RE.search(normalized):
        left, right = _POR_SPLIT_RE.split(normalized, maxsplit=1)
        doses = _to_float(left)
        if np.isnan(doses):
            doses = 1.0
        interval_value, label, code = _parse_interval_part(right)
        return (doses, interval_value, label, code)

    value, remainder = _split_number_unit(normalized)
    if not np.isnan(value) and remainder:
        spec = _match_unit(remainder)
        if spec:
            if spec["category"] == "time":
                return (1.0, value, spec["label"], spec["code"])
            return (value, np.nan, spec["label"], spec["code"])

    if not np.isnan(value) and not remainder:
        return (value, np.nan, UNKNOWN_LABEL, UNKNOWN_CODE)

    return (np.nan, np.nan, UNKNOWN_LABEL, UNKNOWN_CODE)


def normalize_dose_freq(df: pd.DataFrame, col: str = "FREQUENCIA_DOSE") -> pd.DataFrame:
    """
    Deriva colunas estruturadas a partir de uma frequência textual.
    Cria:
      - FREQUENCIA_DOSE_DOSES: quantidade de administrações no intervalo declarado
      - FREQUENCIA_DOSE_INTERVALO_VALOR: tamanho do intervalo (float)
      - FREQUENCIA_DOSE_INTERVALO_TIPO_CHAVE: unidade normalizada (hora, dia, etc.)
      - FREQUENCIA_DOSE_INTERVALO_TIPO_VALOR: código inteiro da unidade
    """
    parsed = df[col].apply(_parse_frequency_value)
    df[
        [
            "FREQUENCIA_DOSE_DOSES",
            "FREQUENCIA_DOSE_INTERVALO_VALOR",
            "FREQUENCIA_DOSE_INTERVALO_TIPO_CHAVE",
            "FREQUENCIA_DOSE_INTERVALO_TIPO_VALOR",
        ]
    ] = pd.DataFrame(parsed.tolist(), index=df.index)

    df["FREQUENCIA_DOSE_INTERVALO_TIPO_VALOR"] = df[
        "FREQUENCIA_DOSE_INTERVALO_TIPO_VALOR"
    ].astype("Int64")
    return df

