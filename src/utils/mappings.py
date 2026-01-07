import pandas as pd
import unicodedata

def _normalize_text(value):
    """Remove acentos, normaliza caixa e espaços para comparação/mapeamento."""
    if not isinstance(value, str):
        return value

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # colapsa múltiplos espaços e remove espaços extras nas pontas
    collapsed = " ".join(without_accents.split())
    return collapsed.casefold().strip()


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
    map_source=None,
):
    if col not in df.columns:
        return df

    nome_valor = nome_valor or f"{col}_VALOR"   # texto original
    nome_chave = nome_chave or f"{col}_CHAVE"   # código

    # 1) guarda o valor original
    df[nome_valor] = df[col]

    # 2) usa map em vez de replace (ADEUS warning 😄)
    origem = map_source if map_source is not None else df[col]
    s = origem.map(mapa)

    # 3) se quiser chave numérica
    if tipo_int64:
        s = pd.to_numeric(s, errors="coerce")

    # 4) preenche NaN da chave, se pedido
    if fillna_chave is not None:
        s = s.fillna(fillna_chave)

    if tipo_int64:
        s = s.astype("Int64")

    df[nome_chave] = s

    # opcional: deixa chaves textuais em caixa alta (quando não for numérico)
    if not tipo_int64 and nome_chave in df.columns:
        df[nome_chave] = df[nome_chave].apply(
            lambda v: v.upper() if isinstance(v, str) else v
        )

    # 5) preenche NaN do valor (texto), se pedido
    if fillna_valor is not None:
        df[nome_valor] = df[nome_valor].fillna(fillna_valor)

    # mantém valor em caixa alta para consistência
    if nome_valor in df.columns:
        df[nome_valor] = df[nome_valor].apply(
            lambda v: v.upper() if isinstance(v, str) else v
        )

    # 6) remove coluna original se não precisar mais
    if drop_original:
        df = df.drop(columns=[col])

    return df


def mapping_column_from_df(
    df,
    dim_df,
    col,
    *,
    dim_join_col=None,
    chave_col=None,
    valor_col=None,
    fillna_valor=None,
    fillna_chave=None,
    tipo_int64=True,
    drop_original=True,
    preprocess=None,
):
    """
    Faz um LEFT JOIN de df com dim_df para trazer <col>_CHAVE e <col>_VALOR.

    - df: dataframe principal
    - dim_df: dataframe de dimensão/mapeamento
    - col: nome da coluna em df a ser usada no join
    - dim_join_col: nome da coluna em dim_df usada no join (default = col)
    - chave_col: nome da coluna de chave em dim_df (default = f"{col}_CHAVE")
    - valor_col: nome da coluna de valor em dim_df (default = f"{col}_VALOR")
    """
    if col not in df.columns:
        return df

    dim_join_col = dim_join_col or col
    chave_col = chave_col or f"{col}_CHAVE"
    valor_col = valor_col or f"{col}_VALOR"

    # normaliza coluna de join do df, se solicitado, usando coluna temporária
    temp_col = None
    if preprocess is not None:
        temp_col = f"__tmp_join_{col}"
        df[temp_col] = df[col].apply(preprocess)
        left_on = temp_col
    else:
        left_on = col

    # garantir apenas colunas necessárias e remover duplicados de chave
    dim_slim = (
        dim_df[[dim_join_col, chave_col, valor_col]]
        .drop_duplicates(subset=[dim_join_col], keep="last")
    )

    # merge
    df = df.merge(dim_slim, left_on=left_on, right_on=dim_join_col, how="left")

    # se a coluna de join da dimensão for diferente, podemos descartá-la
    if dim_join_col != col:
        df = df.drop(columns=[dim_join_col])

    # remove coluna temporária de join
    if temp_col is not None and temp_col in df.columns:
        df = df.drop(columns=[temp_col])

    # tratar NaNs
    if fillna_valor is not None and valor_col in df.columns:
        df[valor_col] = df[valor_col].fillna(fillna_valor)

    if fillna_chave is not None and chave_col in df.columns:
        if tipo_int64:
            df[chave_col] = (
                pd.to_numeric(df[chave_col], errors="coerce")
                .fillna(fillna_chave)
                .astype("Int64")
            )
        else:
            df[chave_col] = df[chave_col].fillna(fillna_chave)

    # valores textuais da dimensão em caixa alta
    if valor_col in df.columns:
        df[valor_col] = df[valor_col].apply(
            lambda v: v.upper() if isinstance(v, str) else v
        )

    # remover coluna original, se desejado
    if drop_original:
        df = df.drop(columns=[col])

    return df

def apply_mappings(df, mappings):
    """
    Aplica uma lista de mapeamentos declarativos sobre o df.

    Cada item de `mappings` é um dict com pelo menos:
      - "kind": "dict" ou "df"
      - "col": nome da coluna em df

    Para kind == "dict":
      - "map": dict de mapeamento

    Para kind == "df":
      - "dim_df": dataframe de dimensão

    Parâmetros opcionais (para ambos, quando fizer sentido):
      - nome_chave, nome_valor
      - dim_join_col, chave_col, valor_col
      - fillna_valor, fillna_chave
      - tipo_int64 (default True)
      - drop_original (default True)
    """
    for cfg in mappings:
        kind = cfg.get("kind", "dict")
        col = cfg["col"]

        norm_series = None
        if col in df.columns:
            # normaliza texto para mapeamento, sem perder o valor original
            norm_series = df[col].apply(_normalize_text)

        if kind == "dict":
            mapa_original = cfg["map"]
            mapa_normalizado = {
                _normalize_text(k): v for k, v in mapa_original.items()
            }

            df = mapping_column(
                df,
                col=col,
                mapa=mapa_normalizado,
                map_source=norm_series,
                nome_chave=cfg.get("nome_chave"),
                nome_valor=cfg.get("nome_valor"),
                tipo_int64=cfg.get("tipo_int64", True),
                fillna_valor=cfg.get("fillna_valor"),
                fillna_chave=cfg.get("fillna_chave"),
                drop_original=cfg.get("drop_original", True),
            )

        elif kind == "df":
            dim_join_col = cfg.get("dim_join_col")
            join_col = dim_join_col or col

            dim_df = cfg["dim_df"]
            dim_df_norm = dim_df.copy()
            if join_col in dim_df_norm.columns:
                dim_df_norm[join_col] = dim_df_norm[join_col].apply(_normalize_text)

            df = mapping_column_from_df(
                df,
                dim_df=dim_df_norm,
                col=col,
                dim_join_col=dim_join_col,
                chave_col=cfg.get("chave_col"),
                valor_col=cfg.get("valor_col"),
                fillna_valor=cfg.get("fillna_valor"),
                fillna_chave=cfg.get("fillna_chave"),
                tipo_int64=cfg.get("tipo_int64", True),
                drop_original=cfg.get("drop_original", True),
                preprocess=_normalize_text,
            )

        else:
            raise ValueError(f"Tipo de mapping desconhecido: {kind!r}")

    return df
