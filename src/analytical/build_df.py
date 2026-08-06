"""Constrói o DataFrame analítico (fat_analytical) a partir das tabelas gold."""

from __future__ import annotations

import pandas as pd


def build_analytical_df(*args, **kwargs) -> pd.DataFrame:
    """
    Monta o dataset analítico usado nas análises de desproporcionalidade.

    TODO: extrair a lógica dos notebooks de coleta/EDA para cá.
    """
    raise NotImplementedError("Implementar build do DataFrame analítico.")
