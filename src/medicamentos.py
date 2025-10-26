import re
import numpy as np
import pandas as pd
import unicodedata
from typing import Optional, List, Dict

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def make_nome_medicamento(
    df: pd.DataFrame,
    atc_col: str = "CODIGO_ATC",
    ativo_col: str = "PRINCIPIOS_ATIVOS_WHODRUG",
    saida_nome: str = "nome_medicamento",
    saida_flag: str = "medicamento_estudo",
    regras: Optional[List[Dict[str, str]]] = None,  # <-- compatível com Py<3.10
) -> pd.DataFrame:
    """
    Preenche `nome_medicamento` (string) e `medicamento_estudo` (bool) quando:
      (ATC começa com o código) E (princípio ativo contém o principio).
    Se várias regras casarem, a primeira na lista tem prioridade.
    """
    if not regras:
        raise ValueError("Forneça `regras` como lista de dicts: {'atc','principio','label'}.")

    # sanity checks mínimos
    faltando = {atc_col, ativo_col} - set(df.columns)
    if faltando:
        raise KeyError(f"Colunas ausentes no DataFrame: {faltando}")

    # normalização
    atc_norm = df[atc_col].astype(str).fillna("").str.lower().map(_strip_accents)
    ativo_norm = df[ativo_col].astype(str).fillna("").str.lower().map(_strip_accents)

    conditions, choices = [], []
    for r in regras:
        atc_code = _strip_accents(str(r["atc"]).lower())
        principio    = _strip_accents(str(r["principio"]).lower())
        label    = str(r["label"])

        # ATC: começa com (prefix match)
        mask_atc = atc_norm.str[:len(atc_code)].eq(atc_code)

        # ativo: contém
        principio_regex = re.compile(re.escape(principio))
        mask_ativo = ativo_norm.str.contains(principio_regex, na=False)

        conditions.append(mask_atc & mask_ativo)
        choices.append(label)

    df[saida_nome] = np.select(conditions, choices, default="outros")
    df[saida_flag] = df[saida_nome].ne("outros")
    return df
