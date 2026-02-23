from __future__ import annotations

import re
from typing import Dict, Iterable, List

import pandas as pd
from rapidfuzz import fuzz, process
from unidecode import unidecode

from .med_normalize_via_adm_keyword_data import (
    BASE_CANONICAL_KEYWORDS,
    BASE_UNKNOWN_TOKENS,
    CANONICAL_CODE_MAP,
    CANONICAL_DESCRIPTIONS,
    CANONICAL_METADATA,
)

SPECIAL_SEQUENCE_PATTERN = re.compile(r"_x[0-9a-f]{4}_", re.IGNORECASE)
NON_ALPHABETIC_PATTERN = re.compile(r"[^a-z\s]")
EXTRA_WHITESPACE_PATTERN = re.compile(r"\s+")

def _normalize_text(value) -> str:
    text = unidecode(str(value) or "")
    text = SPECIAL_SEQUENCE_PATTERN.sub(" ", text)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = text.lower()
    text = re.sub(r"\d+", " ", text)
    text = NON_ALPHABETIC_PATTERN.sub(" ", text)
    text = EXTRA_WHITESPACE_PATTERN.sub(" ", text).strip()
    return text


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result

CANONICAL_KEYWORDS = {
    label: _dedupe_preserve_order(words)
    for label, words in BASE_CANONICAL_KEYWORDS.items()
}

MANUAL_LOOKUP: Dict[str, str] = {}

for label, keywords in CANONICAL_KEYWORDS.items():
    for keyword in keywords:
        normalized_keyword = _normalize_text(keyword)
        if normalized_keyword:
            MANUAL_LOOKUP[normalized_keyword] = label


UNKNOWN_TOKENS = sorted(
    {
        normalized
        for token in BASE_UNKNOWN_TOKENS
        if (normalized := _normalize_text(token))
    }
)

CANONICAL_FLAT = []

for label, words in CANONICAL_KEYWORDS.items():
    for word in words:
        normalized = _normalize_text(word)
        if normalized:
            CANONICAL_FLAT.append((normalized, label))

CANDIDATE_TEXTS = [text for text, _ in CANONICAL_FLAT]
CANDIDATE_LABELS = [label for _, label in CANONICAL_FLAT]

def _is_unknown(text: str) -> bool:
    return any(token in text for token in UNKNOWN_TOKENS)


def _build_struct(label: str) -> dict:
    code = CANONICAL_CODE_MAP.get(label, CANONICAL_CODE_MAP["desconhecido"])
    description = CANONICAL_DESCRIPTIONS.get(label, CANONICAL_DESCRIPTIONS["desconhecido"])
    metadata = CANONICAL_METADATA.get(label, CANONICAL_METADATA["desconhecido"])

    return {
        "chave": code,
        "valor": label,
        "description": description,
        "description_pt": metadata.get("description_pt", description),
    }

def normalizar_via_fuzzy(
    value: str,
    *,
    score_threshold: int = 80,
) -> dict:
    """
    Normaliza via de administração usando fuzzy matching.
    Retorna sempre um dicionário estruturado:
    {
        "chave": int,
        "valor": str,
        "description": str,
        "description_pt": str
    }
    """

    if pd.isna(value):
        return _build_struct("desconhecido")

    s = _normalize_text(value)

    if s in MANUAL_LOOKUP:
        return _build_struct(MANUAL_LOOKUP[s])

    if not s or _is_unknown(s):
        return _build_struct("desconhecido")

    best, score, idx = process.extractOne(
        s,
        CANDIDATE_TEXTS,
        scorer=fuzz.partial_ratio
    )

    if score < score_threshold:
        return _build_struct("desconhecido")

    label = CANDIDATE_LABELS[idx]

    return _build_struct(label)