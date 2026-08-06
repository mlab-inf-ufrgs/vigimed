"""Métricas e tabelas de análise de desproporcionalidade (ROR, PRR, IC, EBGM, etc.)."""

from __future__ import annotations

import pandas as pd


def disproportionality_table(
    df: pd.DataFrame,
    *,
    case_col: str,
    drug_col: str,
    event_col: str,
    **kwargs,
) -> pd.DataFrame:
    """
    Gera a tabela de contingência / métricas de desproporcionalidade.

    TODO: extrair a lógica dos notebooks de disproportionality_analysis para cá.
    """
    raise NotImplementedError("Implementar análise de desproporcionalidade.")
