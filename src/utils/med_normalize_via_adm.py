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
)


SPECIAL_SEQUENCE_PATTERN = re.compile(r"_x[0-9a-f]{4}_", re.IGNORECASE)
NON_ALPHABETIC_PATTERN = re.compile(r"[^a-z\s]")
EXTRA_WHITESPACE_PATTERN = re.compile(r"\s+")


def _normalize_text(value) -> str:
    """
    Normaliza texto removendo acentos, caracteres especiais,
    dígitos e sequências como '_x0009_'.
    """
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
    code: _dedupe_preserve_order(words)
    for code, words in BASE_CANONICAL_KEYWORDS.items()
}

MANUAL_LOOKUP: Dict[str, str] = {}
for code, keywords in CANONICAL_KEYWORDS.items():
    normalized_keywords = []
    for keyword in keywords:
        normalized_keyword = _normalize_text(keyword)
        if not normalized_keyword:
            continue
        MANUAL_LOOKUP[normalized_keyword] = code
        normalized_keywords.append(keyword)
    CANONICAL_KEYWORDS[code] = normalized_keywords

UNKNOWN_TOKENS = sorted(
    {
        normalized
        for token in BASE_UNKNOWN_TOKENS
        if (normalized := _normalize_text(token))
    }
)


CANONICAL_FLAT = []
for code, words in CANONICAL_KEYWORDS.items():
    for w in words:
        normalized = _normalize_text(w)
        if not normalized:
            continue
        CANONICAL_FLAT.append((normalized, code))

CANDIDATE_TEXTS = [text for text, _ in CANONICAL_FLAT]
CANDIDATE_CODES = [code for _, code in CANONICAL_FLAT]


def _preprocess(text: str) -> str:
    return _normalize_text(text)


def normalizar_via_fuzzy(
    value: str,
    *,
    score_threshold: int = 80,
    return_numeric: bool = False,
    return_description: bool = False,
) -> str | int:
    """
    Normaliza via de administração usando fuzzy matching
    contra palavras canônicas definidas em CANONICAL_KEYWORDS.
    Retorna um dos códigos:
      Implant, Inhal, Instill, N, O, P, R, SL, TD, V
    ou 'desconhecido'. Quando `return_numeric=True`, retorna o
    identificador numérico correspondente (0 para desconhecido).
    """
    if pd.isna(value):
        return _return_result("desconhecido", return_numeric)

    s = _preprocess(value)

    manual_code = MANUAL_LOOKUP.get(s)
    if manual_code:
        return _return_result(manual_code, return_numeric, return_description)

    if not s or _is_unknown(s):
        return _return_result("desconhecido", return_numeric, return_description)

    # 3) Fuzzy: compara a string s com todas as palavras canônicas
    best, score, idx = process.extractOne(
        s,
        CANDIDATE_TEXTS,
        scorer=fuzz.partial_ratio
    )

    if score < score_threshold:
        return _return_result("desconhecido", return_numeric, return_description)

    # recupera o código associado à palavra canônica escolhida
    return _return_result(CANDIDATE_CODES[idx], return_numeric, return_description)


def _is_unknown(text: str) -> bool:
    return any(unknown in text for unknown in UNKNOWN_TOKENS)


def _return_result(label: str, return_numeric: bool, return_description: bool) -> str | int:
    if return_description:
        return CANONICAL_DESCRIPTIONS.get(label, CANONICAL_DESCRIPTIONS["desconhecido"])
    if return_numeric:
        return CANONICAL_CODE_MAP.get(label, CANONICAL_CODE_MAP["desconhecido"])
    return label
