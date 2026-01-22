import re
import unicodedata
import numpy as np
import pandas as pd

# =========================
# Domínio de unidades
# =========================

_UNIDADES_GESTACIONAL = {
    "SEMANA": {
        "aliases": {"SEMANA", "SEMANAS", "SEM"},
        "codigo": 1,
    },
    "MES": {
        "aliases": {"MES", "MESES", "MÊS", "MÊSES"},
        "codigo": 2,
    },
    "TRIMESTRE": {
        "aliases": {"TRIMESTRE", "TRIMESTRES", "TRI"},
        "codigo": 3,
    },
}

# agora: alias -> (codigo, categoria)
_ALIAS_LOOKUP_GESTACIONAL = {
    alias: (cfg["codigo"], unidade)
    for unidade, cfg in _UNIDADES_GESTACIONAL.items()
    for alias in cfg["aliases"]
}

_NUMERO_UNIDADE_RE = re.compile(
    r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]+)\s*$"
)

UNKNOWN_TIPO_CHAVE = 0
UNKNOWN_TIPO_VALOR = "DESCONHECIDO"

# =========================
# Utilitário
# =========================

def _remover_acentos(texto: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )

# =========================
# Parser
# =========================

def _parse_idade_gestacional(valor):
    """
    Retorna:
    - IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_CHAVE  -> código inteiro
    - IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_VALOR  -> 'SEMANA' | 'MES' | 'TRIMESTRE' | 'DESCONHECIDO'
    - IDADE_GESTACIONAL_MOMENTO_REACAO_VALOR       -> valor original (float)
    """
    if pd.isna(valor):
        return (UNKNOWN_TIPO_CHAVE, UNKNOWN_TIPO_VALOR, np.nan)

    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none"}:
        return (UNKNOWN_TIPO_CHAVE, UNKNOWN_TIPO_VALOR, np.nan)

    texto = _remover_acentos(texto).upper()
    match = _NUMERO_UNIDADE_RE.match(texto)
    if not match:
        return (UNKNOWN_TIPO_CHAVE, UNKNOWN_TIPO_VALOR, np.nan)

    numero_str, unidade_raw = match.groups()
    unidade = _ALIAS_LOOKUP_GESTACIONAL.get(unidade_raw)
    if not unidade:
        return (UNKNOWN_TIPO_CHAVE, UNKNOWN_TIPO_VALOR, np.nan)

    tipo_chave, tipo_valor = unidade
    numero = float(numero_str.replace(",", "."))

    return (tipo_chave, tipo_valor, numero)

# =========================
# Normalizador
# =========================

def normalize_idade_gestacional_momento_reacao(
    df: pd.DataFrame,
    coluna: str = "IDADE_GESTACIONAL_MOMENTO_REACAO",
) -> pd.DataFrame:
    """
    Cria:
    - IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_CHAVE  (código)
    - IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_VALOR  (categoria)
    - IDADE_GESTACIONAL_MOMENTO_REACAO_VALOR       (valor original)
    """
    resultados = df[coluna].apply(_parse_idade_gestacional)

    df[
        [
            "IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_CHAVE",
            "IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_VALOR",
            "IDADE_GESTACIONAL_MOMENTO_REACAO_VALOR",
        ]
    ] = pd.DataFrame(resultados.tolist(), index=df.index)

    return df