import re
import unicodedata
import numpy as np
import pandas as pd

_UNIDADES_DURACAO = {
    "segundo": {"aliases": {"seg", "segundo", "segundos"}, "tipo_valor": 1},
    "minuto": {"aliases": {"min", "minuto", "minutos"}, "tipo_valor": 2},
    "hora":   {"aliases": {"h", "hr", "hora", "horas"},   "tipo_valor": 3},
    "dia":    {"aliases": {"dia", "dias"},                "tipo_valor": 4},
    "semana": {"aliases": {"sem", "semana", "semanas"},   "tipo_valor": 5},
    "mes":    {"aliases": {"mes", "meses", "mês", "mêses"}, "tipo_valor": 6},
    "ano":    {"aliases": {"ano", "anos"},                "tipo_valor": 7},
    "decada": {"aliases": {"dec", "década", "décadas"},   "tipo_valor": 8},
    "ciclico": {"aliases": {"cic", "ciclo", "ciclos"},    "tipo_valor": 9}
}

_ALIAS_LOOKUP = {
    alias: (unidade, cfg["tipo_valor"])
    for unidade, cfg in _UNIDADES_DURACAO.items()
    for alias in cfg["aliases"]
}

_NUMERO_UNIDADE_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-zçãéêõú]+)\s*$")
UNKNOWN_CHAVE = "desconhecido"
UNKNOWN_VALOR = 0

def _remover_acentos(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def _parse_duracao(valor):
    if pd.isna(valor):
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto = str(valor).strip().lower()
    if not texto or texto in {"nan", "none"}:
        return (UNKNOWN_CHAVE, UNKNOWN_VALOR, np.nan)

    texto_sem_acento = _remover_acentos(texto)
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
    Lê df[coluna] e cria DURACAO_TIPO_CHAVE, DURACAO_TIPO_VALOR e DURACAO_VALOR.
    Retorna o próprio DataFrame para permitir encadeamento.
    """
    resultados = df[coluna].apply(_parse_duracao)
    df[["DURACAO_TIPO_CHAVE", "DURACAO_TIPO_VALOR", "DURACAO_VALOR"]] = (
        pd.DataFrame(resultados.tolist(), index=df.index)
    )
    return df