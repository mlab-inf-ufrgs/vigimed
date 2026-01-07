import re
import unicodedata
import numpy as np
import pandas as pd

_UNIDADES_DURACAO = {
    "SEGUNDO": {"aliases": {"SEG", "SEGUNDO", "SEGUNDOS"}, "tipo_valor": 1},
    "MINUTO": {"aliases": {"MIN", "MINUTO", "MINUTOS"}, "tipo_valor": 2},
    "HORA": {"aliases": {"H", "HR", "HORA", "HORAS"}, "tipo_valor": 3},
    "DIA": {"aliases": {"DIA", "DIAS"}, "tipo_valor": 4},
    "SEMANA": {"aliases": {"SEM", "SEMANA", "SEMANAS"}, "tipo_valor": 5},
    "MES": {"aliases": {"MES", "MESES", "MÊS", "MÊSES"}, "tipo_valor": 6},
    "ANO": {"aliases": {"ANO", "ANOS"}, "tipo_valor": 7},
    "DECADA": {"aliases": {"DEC", "DÉCADA", "DÉCADAS"}, "tipo_valor": 8},
    "CICLICO": {"aliases": {"CIC", "CICLO", "CICLOS"}, "tipo_valor": 9},
}

_ALIAS_LOOKUP = {
    alias: (unidade, cfg["tipo_valor"])
    for unidade, cfg in _UNIDADES_DURACAO.items()
    for alias in cfg["aliases"]
}

_NUMERO_UNIDADE_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]+)\s*$")
UNKNOWN_CHAVE = "DESCONHECIDO"
UNKNOWN_VALOR = 0

def _remover_acentos(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def _parse_duracao(valor):
    if pd.isna(valor):
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none"}:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto_sem_acento = _remover_acentos(texto).upper()
    match = _NUMERO_UNIDADE_RE.match(texto_sem_acento)
    if not match:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    numero_str, unidade_raw = match.groups()
    unidade = _ALIAS_LOOKUP.get(unidade_raw)
    if not unidade:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    tipo_chave, tipo_valor = unidade
    numero = float(numero_str.replace(",", "."))
    return (tipo_chave, tipo_valor, numero)


def normalize_duracao(df: pd.DataFrame, coluna: str = "DURACAO") -> pd.DataFrame:
    """
    Lê df[coluna] e cria DURACAO_TIPO_VALOR, DURACAO_TIPO_CHAVE e DURACAO_VALOR.
    Retorna o próprio DataFrame para permitir encadeamento.
    """
    resultados = df[coluna].apply(_parse_duracao)
    df[["DURACAO_TIPO_VALOR", "DURACAO_TIPO_CHAVE", "DURACAO_VALOR"]] = (
        pd.DataFrame(resultados.tolist(), index=df.index)
    )
    return df