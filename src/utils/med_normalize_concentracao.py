import re
import unicodedata
from typing import Mapping, Tuple

import numpy as np
import pandas as pd

from .med_normalize_concentracao_keyword_data import (
    CONCENTRACAO_METADATA,
    UNIT_SPECS_DATA,
    UNKNOWN_TOKENS,
)

UNKNOWN_LABEL = CONCENTRACAO_METADATA["desconhecido"]["label"]
UNKNOWN_CODE = CONCENTRACAO_METADATA["desconhecido"]["code"]


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace(" / ", "/")
    return normalized


def _normalize_unit_alias(alias: str) -> str:
    text = _normalize_text(alias)
    text = text.replace("por", "/")  # trata 'mg por ml' como 'mg/ml'
    text = re.sub(r"\s*/\s*", "/", text)
    return text


UNIT_SPECS = []
for unit_spec in UNIT_SPECS_DATA:
    metadata_key = unit_spec["metadata_key"]
    metadata = CONCENTRACAO_METADATA.get(metadata_key)
    if not metadata:
        continue
    UNIT_SPECS.append(
        {
            "label": metadata["label"],
            "code": metadata["code"],
            "aliases": set(unit_spec.get("aliases", [])),
        }
    )

_ALIAS_TO_SPEC: Mapping[str, dict] = {}
for spec in UNIT_SPECS:
    aliases = set(spec["aliases"])
    aliases.add(spec["label"])
    for alias in aliases:
        normalized = _normalize_unit_alias(alias)
        if normalized:
            _ALIAS_TO_SPEC[normalized] = spec

RATIO_REGEX = re.compile(
    r"([0-9]+(?:[.,][0-9]+)?)\s*([a-z%µ]+)\s*/\s*(?:([0-9]+(?:[.,][0-9]+)?)\s*)?([a-z%µ]+)"
)
SIMPLE_REGEX = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*([a-z%µ/]+)")


def _to_float(value: str) -> float:
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return np.nan


def _parse_concentration(raw):
    if pd.isna(raw):
        return (
            UNKNOWN_LABEL,
            UNKNOWN_CODE,
            np.nan,
            np.nan,
            np.nan,
        )

    text = str(raw).strip()
    if not text:
        return (
            UNKNOWN_LABEL,
            UNKNOWN_CODE,
            np.nan,
            np.nan,
            np.nan,
        )

    normalized = _normalize_text(text)
    if (
        not normalized
        or normalized in {"nan", "none"}
        or _is_unknown_text(normalized)
    ):
        return (
            UNKNOWN_LABEL,
            UNKNOWN_CODE,
            np.nan,
            np.nan,
            np.nan,
        )

    ratio = RATIO_REGEX.search(normalized)
    if ratio:
        numerator_value = _to_float(ratio.group(1))
        numerator_unit = _normalize_unit_alias(ratio.group(2))
        denominator_raw = ratio.group(3)
        denominator_value = _to_float(denominator_raw) if denominator_raw else 1.0
        denominator_unit = _normalize_unit_alias(ratio.group(4))

        alias = f"{numerator_unit}/{denominator_unit}"
        spec = _ALIAS_TO_SPEC.get(alias)
        if spec:
            ratio = (
                numerator_value / denominator_value
                if denominator_value not in (0, None, np.nan)
                else np.nan
            )
            return (
                spec["label"],
                spec["code"],
                ratio,
                numerator_value,
                denominator_value,
            )

    for match in SIMPLE_REGEX.finditer(normalized):
        unit_alias = _normalize_unit_alias(match.group(2))
        spec = _ALIAS_TO_SPEC.get(unit_alias)
        if spec:
            value = _to_float(match.group(1))
            return (
                spec["label"],
                spec["code"],
                value,
                value,
                np.nan,
            )

    numeric_only = _to_float(normalized)
    if not np.isnan(numeric_only):
        return (
            UNKNOWN_LABEL,
            UNKNOWN_CODE,
            numeric_only,
            numeric_only,
            np.nan,
        )
    return (
        UNKNOWN_LABEL,
        UNKNOWN_CODE,
        np.nan,
        np.nan,
        np.nan,
    )


def _is_unknown_text(text: str) -> bool:
    return any(token in text for token in UNKNOWN_TOKENS)


def normalize_concentracao(df: pd.DataFrame, col: str = "CONCENTRACAO") -> pd.DataFrame:
    parsed = df[col].apply(_parse_concentration)
    df[
        [
            "CONCENTRACAO_TIPO_CHAVE",
            "CONCENTRACAO_TIPO_VALOR",
            "CONCENTRACAO_VALOR",
            "CONCENTRACAO_VALOR_NUMERADOR",
            "CONCENTRACAO_VALOR_DENOMINADOR",
        ]
    ] = pd.DataFrame(parsed.tolist(), index=df.index)

    df["CONCENTRACAO_TIPO_VALOR"] = df["CONCENTRACAO_TIPO_VALOR"].astype("Int64")
    return df

