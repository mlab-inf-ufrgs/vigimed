"""Classifica linha da fat como vacina vs medicamento (só com dados da bronze/fat).

Regra (sem join com notificações):
- ATC nível 4 começa com ``J07`` (vacinas ATC), **ou**
- ``NOME_MEDICAMENTO_WHODRUG`` / ``PRINCIPIOS_ATIVOS_WHODRUG`` contém VACINA/VACCINE.

``TIPO_ENTRADA_VIGIMED = Serviços de Vacinação`` é canal de entrada na
notificação — não define o tipo do produto e não é usado aqui.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

TIPO_PRODUTO_VACINA = "VACINA"
TIPO_PRODUTO_MEDICAMENTO = "MEDICAMENTO"

_VACINA_TEXT = re.compile(r"\b(VACINA|VACCINE)S?\b", flags=re.IGNORECASE)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _text_suggests_vaccine(value: Any) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    text = _strip_accents(str(value)).upper()
    return bool(_VACINA_TEXT.search(text))


def _atc_is_vaccine(atc_value: Any) -> bool:
    if atc_value is None or (isinstance(atc_value, float) and pd.isna(atc_value)):
        return False
    # Pode haver múltiplos códigos separados por | após desagregação residual.
    for part in re.split(r"[|;,]", str(atc_value)):
        code = part.strip().upper()
        if code.startswith("J07"):
            return True
    return False


def is_vacina_row(
    atc_value: Any,
    nome_value: Any = None,
    principio_value: Any = None,
) -> bool:
    """True se a linha for classificada como vacina (ATC J07* ou texto VACINA/VACCINE)."""
    if _atc_is_vaccine(atc_value):
        return True
    if _text_suggests_vaccine(nome_value) or _text_suggests_vaccine(principio_value):
        return True
    return False


def add_tipo_produto(
    df: pd.DataFrame,
    *,
    atc_col: str = "ATC_CODE_LEVEL_4",
    nome_col: str = "NOME_MEDICAMENTO_WHODRUG",
    principio_col: str = "PRINCIPIOS_ATIVOS_WHODRUG",
    tipo_col: str = "TIPO_PRODUTO",
    flag_col: str = "VACINA_FLAG",
    inplace: bool = False,
) -> pd.DataFrame:
    """Adiciona ``TIPO_PRODUTO`` (VACINA|MEDICAMENTO) e ``VACINA_FLAG`` (0/1)."""
    # Aceitar CODIGO_ATC da bronze se ATC_CODE_LEVEL_4 ainda não existir.
    resolved_atc = atc_col
    if resolved_atc not in df.columns and "CODIGO_ATC" in df.columns:
        resolved_atc = "CODIGO_ATC"
    if resolved_atc not in df.columns:
        raise KeyError(
            f"Coluna ATC ausente (tentou {atc_col!r} e 'CODIGO_ATC'). "
            f"Colunas: {sorted(df.columns)[:20]}..."
        )

    target = df if inplace else df.copy()
    atc_s = target[resolved_atc]
    nome_s = target[nome_col] if nome_col in target.columns else pd.Series([None] * len(target), index=target.index)
    princ_s = (
        target[principio_col]
        if principio_col in target.columns
        else pd.Series([None] * len(target), index=target.index)
    )

    flags = [
        is_vacina_row(a, n, p)
        for a, n, p in zip(atc_s.tolist(), nome_s.tolist(), princ_s.tolist())
    ]
    target[flag_col] = pd.Series(flags, index=target.index, dtype="int8")
    target[tipo_col] = target[flag_col].map(
        {1: TIPO_PRODUTO_VACINA, 0: TIPO_PRODUTO_MEDICAMENTO}
    )
    return target


def summarize_tipo_produto(
    df: pd.DataFrame,
    *,
    tipo_col: str = "TIPO_PRODUTO",
    flag_col: str = "VACINA_FLAG",
) -> dict:
    """Contagens rápidas de vacina vs medicamento (QA)."""
    n = len(df)
    if flag_col in df.columns:
        n_vac = int(pd.to_numeric(df[flag_col], errors="coerce").fillna(0).astype(int).sum())
    elif tipo_col in df.columns:
        n_vac = int((df[tipo_col].astype(str).str.upper() == TIPO_PRODUTO_VACINA).sum())
    else:
        raise KeyError(f"Colunas ausentes: {tipo_col!r} / {flag_col!r}")
    return {
        "n_rows": n,
        "n_vacina": n_vac,
        "n_medicamento": n - n_vac,
        "pct_vacina": round(100.0 * n_vac / n, 2) if n else 0.0,
        "pct_medicamento": round(100.0 * (n - n_vac) / n, 2) if n else 0.0,
    }
