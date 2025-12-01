import pandas as pd
import numpy as np
from unidecode import unidecode

# Normalizar as linhas
def normalize_rows(series):
    series = series.astype(str).str.strip()  # limpa espaços
    series = series.replace(["nan", "None", "NaT", "NULL"], np.nan)  # textos inválidos
    series = series.apply(lambda x: unidecode(x) if pd.notna(x) else x)
    series = series.str.upper()
    return series

# Converter datas no formato YYYY-MM-DD
def normalize_date_column(series):
    # Converte strings ou números para datetime
    series = pd.to_datetime(series.astype(str).str.strip(), errors="coerce", format="%Y%m%d")
    # Mantém apenas a parte da data (sem hora)
    series = series.dt.floor("d")  # arredonda para o dia
    return series
################################################################################################################
## MEDICAMENTOS ################################################################################################
################################################################################################################
import pandas as pd

def mapping_column(
    df,
    col,
    mapa,
    *,
    nome_chave=None,
    nome_valor=None,
    tipo_int64=True,
    fillna_valor=None,
    fillna_chave=None,
    drop_original=True,
):
    """
    - Cria <col>_VALOR com o texto original.
    - Cria <col>_CHAVE com o código (mapeado).
    - Opcionalmente remove a coluna original <col>.
    """

    if col not in df.columns:
        return df

    # nomes padrão das colunas derivadas
    nome_valor = nome_valor or f"{col}_VALOR"   # texto original
    nome_chave = nome_chave or f"{col}_CHAVE"   # código

    # 1) guardar o valor original (texto)
    df[nome_valor] = df[col]

    # 2) aplicar o mapa para obter a CHAVE
    s = df[col].replace(mapa)
    # remove o FutureWarning de downcasting silencioso
    s = s.infer_objects(copy=False)

    # 3) converter para Int64 se desejado
    if tipo_int64:
        s = pd.to_numeric(s, errors="coerce")

    # 4) preencher NaN da chave, se solicitado
    if fillna_chave is not None:
        s = s.fillna(fillna_chave)

    if tipo_int64:
        s = s.astype("Int64")

    df[nome_chave] = s

    # 5) preencher NaN do valor (texto), se solicitado
    if fillna_valor is not None:
        df[nome_valor] = df[nome_valor].fillna(fillna_valor)

    # 6) remover coluna original, se não for mais necessária
    if drop_original:
        df = df.drop(columns=[col])

    return df


################################################################################################################
## REACOES ################################################################################################
################################################################################################################
def expandir_gravidade_wide(df, col='GRAVIDADE', prefix='GRAVIDADE_'):
    """
    Cria colunas dummies (0/1) para cada tipo de gravidade encontrado em uma coluna texto.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com a coluna de gravidade.
    col : str, default 'GRAVIDADE'
        Nome da coluna que contém o texto de gravidade (ex: 'Resultou em óbito, Ameaça à vida').
    prefix : str, default 'GRAV_'
        Prefixo para os nomes das colunas geradas.

    Retorna
    -------
    df : pd.DataFrame
        Mesmo DataFrame de entrada, com novas colunas 0/1 para cada tipo de gravidade.
    """

    # garante string para evitar erro em .str.contains
    s = df[col].astype(str)

    # mapeamento: nome da coluna -> texto a ser procurado
    patterns = {
        prefix + 'RESULTADO_OBITO':      'Resultou em óbito',
        prefix + 'AMEACA_VIDA':         'Ameaça à vida',
        prefix + 'INCAPACIDADE':        'Incapacidade persistente ou significativa',
        prefix + 'HOSPITALIZACAO':      'Hospitalização/Prolongamento de hospitalização',
        prefix + 'OUTRO_EFEITO':        'Outro efeito clinicamente significativo',
        prefix + 'ANOMALIA_CONGENITA':  'Anomalia congênita ou malformação ao nascer',
    }

    for col_out, texto in patterns.items():
        df[col_out] = s.str.contains(texto, na=False).astype('int8')

    return df
