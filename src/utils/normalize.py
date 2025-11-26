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
 
def mapping_column(df, col, mapa, nome_valor=None, tipo_int64=True):
    if col not in df.columns:
        return df

    nome_valor = nome_valor or f"{col}_VALOR"
    df[nome_valor] = df[col]

    # Substitui pelos códigos
    df[col] = df[col].replace(mapa)
    
    if tipo_int64:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("Int64")

    return df
 
def duration_normalize(df, col='DURACAO', prefix='DURACAO'):
    """
    Normaliza uma coluna de duração em duas:
      - <prefix>_VALOR: valor numérico (float)
      - <prefix>_TIPO : unidade padronizada (dia, hora, minuto, semana, mês, ano, segundo, década)

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame de entrada.
    col : str, default 'DURACAO'
        Nome da coluna de texto com a duração (ex: '1 dia', '30 minuto', '1.5 hora').
    prefix : str, default 'DURACAO'
        Prefixo para os nomes das colunas de saída.

    Retorna
    -------
    df : pd.DataFrame
        O mesmo DataFrame com duas novas colunas adicionadas:
        - f'{prefix}_VALOR'
        - f'{prefix}_TIPO'
    """
    # garante string e tira espaços
    s = df[col].astype(str).str.strip()

    # regex: captura número (inclui decimais com . ou ,) e depois a unidade (uma palavra)
    tmp = s.str.extract(
        r'^\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-zçÇáàãâéêíóôõúüÁÀÃÂÉÊÍÓÔÕÚÜ]+)?'
    )

    valor_col = f'{prefix}_VALOR'
    tipo_col = f'{prefix}_TIPO'

    # ---- VALOR ----
    df[valor_col] = (
        tmp[0]
        .str.replace(',', '.', regex=False)   # vírgula -> ponto
    )
    df[valor_col] = pd.to_numeric(df[valor_col], errors='coerce')  # float (NaN se não der)

    # ---- TIPO (unidade) ----
    df[tipo_col] = tmp[1].str.lower()

    # linhas sem número, mas com texto tipo "dia", "semana", "hora"
    mask_sem_numero = df[valor_col].isna() & s.str.contains(r'[A-Za-z]', na=False)
    df.loc[mask_sem_numero, tipo_col] = s[mask_sem_numero].str.lower()

    # mapa de normalização das unidades
    tipo_map = {
        'dia': 'dia',
        'dias': 'dia',

        'semana': 'semana',
        'semanas': 'semana',

        'mes': 'mês',
        'mês': 'mês',
        'meses': 'mês',

        'ano': 'ano',
        'anos': 'ano',

        'minuto': 'minuto',
        'minutos': 'minuto',

        'hora': 'hora',
        'horas': 'hora',

        'segundo': 'segundo',
        'segundos': 'segundo',

        'década': 'década',
        'decada': 'década',
        'décadas': 'década',
        'decadas': 'década',
    }

    df[tipo_col] = (
        df[tipo_col]
        .str.strip()
        .map(tipo_map)
        .fillna(df[tipo_col])   # se aparecer algo estranho, mantém o original
    )

    return df

import pandas as pd

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
