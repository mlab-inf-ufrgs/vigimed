import re
import unicodedata
import numpy as np
import pandas as pd

_UNIDADES_IDADE = {
    "MES": {"aliases": {"MES", "MESES", "MÊS", "MÊSES"}, "tipo_valor": 1},
    "ANO": {"aliases": {"ANO", "ANOS"}, "tipo_valor": 2},
}

_ALIAS_LOOKUP_IDADE = {
    alias: (unidade, cfg["tipo_valor"])
    for unidade, cfg in _UNIDADES_IDADE.items()
    for alias in cfg["aliases"]
}

_NUMERO_UNIDADE_RE = re.compile(
    r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]+)\s*$"
)

UNKNOWN_CHAVE = "DESCONHECIDO"
UNKNOWN_VALOR = 0


def _remover_acentos(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def _parse_idade(valor):
    """
    Retorna:
    - IDADE_MOMENTO_REACAO_TIPO_CHAVE  -> 'ANO' | 'MES' | 'DESCONHECIDO'
    - IDADE_MOMENTO_REACAO_TIPO_VALOR  -> código inteiro
    - IDADE_MOMENTO_REACAO_VALOR       -> valor numérico original (sem conversão)
    """
    if pd.isna(valor):
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none"}:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto = _remover_acentos(texto).upper()
    match = _NUMERO_UNIDADE_RE.match(texto)
    if not match:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    numero_str, unidade_raw = match.groups()
    unidade = _ALIAS_LOOKUP_IDADE.get(unidade_raw)
    if not unidade:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    tipo_chave, tipo_valor = unidade
    numero = float(numero_str.replace(",", "."))

    return (tipo_chave, tipo_valor, numero)


def normalize_idade_momento_reacao(
    df: pd.DataFrame,
    coluna: str = "IDADE_MOMENTO_REACAO",
) -> pd.DataFrame:
    """
    Preserva a unidade original da idade.
    """
    resultados = df[coluna].apply(_parse_idade)

    df[
        [
            "IDADE_MOMENTO_REACAO_TIPO_CHAVE",
            "IDADE_MOMENTO_REACAO_TIPO_VALOR",
            "IDADE_MOMENTO_REACAO_VALOR",
        ]
    ] = pd.DataFrame(resultados.tolist(), index=df.index)

    return df
