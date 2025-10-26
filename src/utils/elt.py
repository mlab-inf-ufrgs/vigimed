# scd2 hash

import hashlib
import pandas as pd
from typing import List, Literal

def build_row_hash(
    df: pd.DataFrame,
    cols: List[str],
    algo: Literal["sha256", "md5"] = "sha256",
    sep: str = "|",
) -> pd.Series:
    """
    Gera um hash por linha a partir das colunas escolhidas.

    Parâmetros
    ----------
    df : DataFrame de origem
    cols : lista de colunas que entram no hash
    algo : algoritmo ("sha256" ou "md5")
    sep  : separador usado na concatenação

    Retorno
    -------
    Series de strings com o hash (mesmo índice do df)
    """
    if algo not in {"sha256", "md5"}:
        raise ValueError("Somente 'sha256' ou 'md5' são suportados.")

    # Seleciona colunas + garante que NaNs virem string vazia
    joined = (
        df[cols]
        .fillna("")                     # evita 'nan' literais
        .astype(str)
        .agg(sep.join, axis=1)          # concatena linha a linha
    )

    # Escolhe a função de hash
    hfunc = hashlib.sha256 if algo == "sha256" else hashlib.md5

    # Aplica o hash – list comprehension costuma ser mais rápida que .apply
    return joined.map(lambda x: hfunc(x.encode("utf-8")).hexdigest())
