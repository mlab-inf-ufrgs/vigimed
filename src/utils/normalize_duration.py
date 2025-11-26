import pandas as pd
def normalize_duration(df, col='DURACAO', prefix='DURACAO'):
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
        'dia': 'DIA(S)',
        'dias': 'DIA(S)',

        'semana': 'SEMANA(S)',
        'semanas': 'SEMANA(S)',

        'mes': 'MES(ES)',
        'mês': 'MES(ES)',
        'meses': 'MES(ES)',

        'ano': 'ANO(S)',
        'anos': 'ANO(S)',

        'minuto': 'MINUTO(S)',
        'minutos': 'MINUTO(S)',

        'hora': 'HORA(S)',
        'horas': 'HORA(S)',

        'segundo': 'SEGUNDO(S)',
        'segundos': 'SEGUNDO(S)',

        'década': 'DECADA(S)',
        'decada': 'DECADA(S)',
        'décadas': 'DECADA(S)',
        'decadas': 'DECADA(S)',
    }

    df[tipo_col] = (
        df[tipo_col]
        .str.strip()
        .map(tipo_map)
        .fillna(df[tipo_col])   # se aparecer algo estranho, mantém o original
    )

    return df