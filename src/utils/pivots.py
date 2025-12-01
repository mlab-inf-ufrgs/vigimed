import re
from unidecode import unidecode
import pandas as pd
from unidecode import unidecode

def _slug_col_name(texto: str) -> str:
    """
    Normaliza texto para virar nome de coluna.
    Extra: garante que X000D não apareça em nomes.
    """
    s = unidecode(str(texto)).upper().replace("X000D", " ")
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def expandir_lista_wide(df, col, prefix=None, dtype="int8"):
    if col not in df.columns:
        return df

    if prefix is None:
        prefix = _slug_col_name(col) + "_"

    s = df[col]

    # categorias distintas (já limpas)
    categorias = (
        s.explode()
         .dropna()
         .astype(str)
         .str.strip()
         .loc[lambda x: x != ""]
         .drop_duplicates()
         .sort_values()
    )

    for valor in categorias:
        col_out = prefix + _slug_col_name(valor)
        df[col_out] = s.apply(
            lambda lst: valor in lst if isinstance(lst, (list, tuple, set)) else False
        ).astype(dtype)

    return df
