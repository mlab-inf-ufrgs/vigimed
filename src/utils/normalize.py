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