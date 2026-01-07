import re
import unicodedata
from typing import Mapping, Tuple

import numpy as np
import pandas as pd

from .med_normalize_dose_keyword_data import (
    DOSE_METADATA,
    DOSE_UNIT_SPECS_DATA,
    UNKNOWN_TOKENS,
)

UNKNOWN_LABEL = DOSE_METADATA["desconhecido"]["label"]
UNKNOWN_CODE = DOSE_METADATA["desconhecido"]["code"]

_NUMBER_UNIT_RE = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*(.*)$")

_DOSE_UNIT_SPECS = []
for spec_data in DOSE_UNIT_SPECS_DATA:
    metadata_key = spec_data["metadata_key"]
    metadata = DOSE_METADATA.get(metadata_key)
    if not metadata:
        continue
    _DOSE_UNIT_SPECS.append(
        {
            "label": metadata["label"],
            "code": metadata["code"],
            "aliases": set(spec_data.get("aliases", [])),
        }
    )

_LABEL_TO_CODE: Mapping[str, int] = {
    spec["label"]: spec["code"] for spec in _DOSE_UNIT_SPECS
}


def _normalize_text(value: str) -> str:
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.replace("µ", "u")
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


_ALIAS_TO_LABEL: Mapping[str, str] = {}
for spec in _DOSE_UNIT_SPECS:
    for candidate in spec["aliases"] | {spec["label"]}:
        normalized_alias = _normalize_text(candidate)
        if normalized_alias:
            _ALIAS_TO_LABEL[normalized_alias] = spec["label"]


def _parse_dose_value(raw) -> Tuple[str, int, float]:
    if pd.isna(raw):
        return (UNKNOWN_LABEL, UNKNOWN_CODE, np.nan)

    text = str(raw).strip()
    normalized_text = _normalize_text(text)
    if not normalized_text or normalized_text in {"none", "nan"} or _is_unknown_text(normalized_text):
        return (UNKNOWN_LABEL, UNKNOWN_CODE, np.nan)

    match = _NUMBER_UNIT_RE.match(text)
    if not match:
        return (UNKNOWN_LABEL, UNKNOWN_CODE, np.nan)

    value_str, unit_raw = match.groups()
    value = _to_float(value_str)

    normalized_unit = _normalize_text(unit_raw.rstrip(" ."))
    if not normalized_unit:
        return (UNKNOWN_LABEL, UNKNOWN_CODE, value)

    label = _ALIAS_TO_LABEL.get(normalized_unit)
    if not label:
        return (UNKNOWN_LABEL, UNKNOWN_CODE, value)

    return (label, _LABEL_TO_CODE[label], value)


def _is_unknown_text(text: str) -> bool:
    return any(token in text for token in UNKNOWN_TOKENS)


def _to_float(value: str) -> float:
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return np.nan


def normalize_dose(df: pd.DataFrame, col: str = "DOSE") -> pd.DataFrame:
    """
    Normaliza a coluna de dose em três colunas:

    - DOSE_VALOR: parte numérica (float)
    - DOSE_TIPO_VALOR: unidade padronizada (ex.: 'MILLIGRAM (MG)')
    - DOSE_TIPO_CHAVE: código inteiro da unidade

    Valores sem unidade reconhecida são preenchidos com
    'desconhecido' / 0 e o valor numérico extraído permanece disponível.
    """

    parsed = df[col].apply(_parse_dose_value)
    # _parse_dose_value retorna: (label, code, value)
    df[["DOSE_TIPO_VALOR", "DOSE_TIPO_CHAVE", "DOSE_VALOR"]] = (
        pd.DataFrame(parsed.tolist(), index=df.index)
    )
    df["DOSE_TIPO_CHAVE"] = df["DOSE_TIPO_CHAVE"].astype("Int64")
    return df

