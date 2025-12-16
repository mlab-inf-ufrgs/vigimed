import re
from unidecode import unidecode
import pandas as pd


def _slug_col_name(texto: str) -> str:
    """
    Normaliza texto para virar nome de coluna:
    - remove acentos
    - coloca maiúsculas
    - troca não-alfanumérico por "_"
    - colapsa múltiplos "_" em um só
    - tira "_" das pontas
    """
    s = unidecode(str(texto)).upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def clean_problema_token(p: str) -> str:
    """
    Limpa um token individual removendo ruídos comuns (p. ex. X000D) e
    normalizando espaços/separadores. Retorna string vazia se o token for lixo.
    """
    texto = str(p).upper()
    texto = texto.replace("X000D", " ")
    texto = re.sub(r"[_\s]+", " ", texto)
    texto = texto.strip()
    if texto in ("", "X000D"):
        return ""
    return texto


def _prepare_list_column(
    series: pd.Series,
    *,
    token_cleaner=clean_problema_token,
    sep: str = "|",
) -> pd.Series:
    """
    Garante que a série contenha listas limpas, mesmo que originalmente
    fossem strings separadas por delimitador.
    """

    def _clean_list(lst):
        if not isinstance(lst, (list, tuple, set)):
            return []
        cleaned = [
            token_cleaner(item)
            for item in lst
        ]
        return [valor for valor in cleaned if valor]

    if series.apply(lambda v: isinstance(v, (list, tuple, set))).all():
        return series.apply(_clean_list)

    s = series.fillna("").astype(str).str.upper()
    s = s.str.replace(r"X000D", " ", regex=True)
    s = s.str.replace(r"[\r\n\t]", " ", regex=True)
    s = s.str.replace('"', "")
    s = s.str.replace(r"[|_]+", "|", regex=True)
    s = s.str.replace(r"\|{2,}", "|", regex=True)
    s = s.str.strip(" |")

    return s.apply(
        lambda txt: [
            token
            for token in (token_cleaner(part) for part in txt.split(sep))
            if token
        ]
    )


def expandir_lista_wide(
    df,
    col,
    prefix=None,
    dtype="int8",
    *,
    sep: str = "|",
    token_cleaner=clean_problema_token,
):
    """
    Cria colunas dummies (0/1) para cada valor distinto em uma coluna de LISTAS.

    Ex:
      df[col] = ['ABUSO', 'ERRO DE MEDICAÇÃO']
      -> GRUPO_PROB_ABUSO = 1, GRUPO_PROB_ERRO_DE_MEDICACAO = 1

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com a coluna de listas.
    col : str
        Nome da coluna que contém listas (ex: PROBLEMAS_ADICIONAIS_RELCIONADOS_MEDICAMENTO).
    prefix : str, opcional
        Prefixo para os nomes das colunas geradas. Default: f"{col}_" normalizado.
    dtype : str, default "int8"
        Tipo para as colunas 0/1.

    Retorna
    -------
    df : pd.DataFrame
        Mesmo DataFrame de entrada, com novas colunas 0/1.
    """
    if col not in df.columns:
        return df

    # garante prefixo bonitinho
    if prefix is None:
        prefix = _slug_col_name(col) + "_"

    df[col] = _prepare_list_column(df[col], token_cleaner=token_cleaner, sep=sep)
    s = df[col]

    # explode para descobrir todos os valores distintos
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
        # cria dummy: 1 se o valor estiver na lista daquela linha
        df[col_out] = s.apply(
            lambda lst: valor in lst if isinstance(lst, (list, tuple, set)) else False
        ).astype(dtype)

    return df
