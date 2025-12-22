"""
Funções para implementar versionamento SCD Type 2 (Slowly Changing Dimension Type 2).

SCD Type 2 mantém histórico de mudanças criando novas versões de registros quando os dados mudam,
mantendo as versões antigas com flags e datas de validade.
"""

import pandas as pd
from typing import List, Optional, Union
from datetime import datetime, date

# Importar função existente de build_row_hash
from .elt import build_row_hash


def apply_scd2(
    df_new: pd.DataFrame,
    df_historical: Optional[pd.DataFrame] = None,
    business_key_cols: List[str] = None,
    data_cols: Optional[List[str]] = None,
    date_update: Optional[Union[str, datetime, date]] = None,
    date_valid_end_default: str = "9999-01-01",
    current_flag_col: str = "CURRENT_FLAG",
    date_update_col: str = "DATE_UPDATE",
    date_data_valid_start_col: str = "DATE_DATA_VALID_START",
    date_data_valid_end_col: str = "DATE_DATA_VALID_END",
) -> pd.DataFrame:
    """
    Aplica versionamento SCD Type 2 em um DataFrame.

    Esta função:
    1. Compara dados novos com dados históricos baseado na chave de negócio
    2. Para registros que mudaram: fecha versão antiga e cria nova versão
    3. Para registros novos: insere normalmente
    4. Para registros inalterados: mantém como estão

    Parameters
    ----------
    df_new : pd.DataFrame
        DataFrame com dados novos/atualizados
    df_historical : pd.DataFrame, optional
        DataFrame com dados históricos. Se None, trata df_new como primeira carga
    business_key_cols : List[str]
        Lista de colunas que formam a chave de negócio (identificam unicamente um registro)
    data_cols : List[str], optional
        Lista de colunas de dados que devem ser comparadas para detectar mudanças.
        Se None, usa todas as colunas exceto as de controle SCD2
    date_update : str, datetime ou date, optional
        Data de atualização. Se None, usa data atual
    date_valid_end_default : str, default "9999-01-01"
        Data padrão para DATE_DATA_VALID_END (indica registro atual)
    current_flag_col : str, default "CURRENT_FLAG"
        Nome da coluna com flag de registro atual (1=atual, 0=histórico)
    date_update_col : str, default "DATE_UPDATE"
        Nome da coluna com data de atualização
    date_data_valid_start_col : str, default "DATE_DATA_VALID_START"
        Nome da coluna com início da validade
    date_data_valid_end_col : str, default "DATE_DATA_VALID_END"
        Nome da coluna com fim da validade

    Returns
    -------
    pd.DataFrame
        DataFrame com versionamento SCD2 aplicado

    Examples
    --------
    >>> # Primeira carga (sem histórico)
    >>> df_result = apply_scd2(
    ...     df_new=df,
    ...     business_key_cols=['id', 'codigo'],
    ...     data_cols=['nome', 'valor']
    ... )
    >>>
    >>> # Carga incremental (com histórico)
    >>> df_historical = pd.read_parquet('dim_table.parquet')
    >>> df_result = apply_scd2(
    ...     df_new=df_new,
    ...     df_historical=df_historical,
    ...     business_key_cols=['id', 'codigo'],
    ...     data_cols=['nome', 'valor']
    ... )
    """
    if df_new.empty:
        return df_new.copy()

    # Validar colunas de chave de negócio
    if not business_key_cols:
        raise ValueError("business_key_cols deve ser fornecido e não pode estar vazio")

    missing_cols = [col for col in business_key_cols if col not in df_new.columns]
    if missing_cols:
        raise ValueError(f"Colunas de chave de negócio não encontradas em df_new: {missing_cols}")

    # Preparar data de atualização
    if date_update is None:
        date_update = pd.Timestamp.now().floor("d")
    else:
        date_update = pd.Timestamp(date_update).floor("d")

    # Converter date_valid_end_default para Timestamp
    date_valid_end_ts = pd.Timestamp(date_valid_end_default)

    # Definir colunas de dados (todas exceto as de controle SCD2)
    scd2_control_cols = [
        current_flag_col,
        date_update_col,
        date_data_valid_start_col,
        date_data_valid_end_col,
    ]

    if data_cols is None:
        # Usar todas as colunas exceto as de controle SCD2 e as de chave de negócio
        data_cols = [
            col
            for col in df_new.columns
            if col not in business_key_cols and col not in scd2_control_cols
        ]

    # Verificar se colunas de dados existem
    missing_data_cols = [col for col in data_cols if col not in df_new.columns]
    if missing_data_cols:
        raise ValueError(f"Colunas de dados não encontradas em df_new: {missing_data_cols}")

    # Preparar DataFrame novo
    df_new_work = df_new.copy()

    # Se não há histórico, primeira carga - apenas adicionar colunas de controle
    if df_historical is None or df_historical.empty:
        df_new_work[date_update_col] = date_update
        df_new_work[date_data_valid_start_col] = date_update
        df_new_work[date_data_valid_end_col] = date_valid_end_ts
        df_new_work[current_flag_col] = 1

        return df_new_work

    # Preparar DataFrame histórico
    df_historical_work = df_historical.copy()

    # Garantir que colunas de controle existem no histórico
    if date_update_col not in df_historical_work.columns:
        df_historical_work[date_update_col] = date_update
    if date_data_valid_start_col not in df_historical_work.columns:
        df_historical_work[date_data_valid_start_col] = date_update
    if date_data_valid_end_col not in df_historical_work.columns:
        df_historical_work[date_data_valid_end_col] = date_valid_end_ts
    if current_flag_col not in df_historical_work.columns:
        df_historical_work[current_flag_col] = 1

    # Garantir que apenas registros atuais sejam considerados para comparação
    df_historical_current = df_historical_work[
        df_historical_work[current_flag_col] == 1
    ].copy()

    if df_historical_current.empty:
        # Não há registros atuais, tratar como primeira carga
        df_new_work[date_update_col] = date_update
        df_new_work[date_data_valid_start_col] = date_update
        df_new_work[date_data_valid_end_col] = date_valid_end_ts
        df_new_work[current_flag_col] = 1

        return pd.concat([df_historical_work, df_new_work], ignore_index=True)

    # Criar hash para comparação
    # Hash da chave de negócio + dados
    all_cols_for_hash = business_key_cols + data_cols

    df_new_work["_hash_new"] = build_row_hash(df_new_work, all_cols_for_hash)
    df_historical_current["_hash_hist"] = build_row_hash(
        df_historical_current, all_cols_for_hash
    )

    # Criar chave de negócio como string para merge
    def create_business_key(row, cols):
        return "|".join(str(row[col]) if pd.notna(row[col]) else "" for col in cols)

    df_new_work["_business_key"] = df_new_work.apply(
        lambda row: create_business_key(row, business_key_cols), axis=1
    )
    df_historical_current["_business_key"] = df_historical_current.apply(
        lambda row: create_business_key(row, business_key_cols), axis=1
    )

    # Merge para identificar mudanças
    merged = df_new_work.merge(
        df_historical_current[["_business_key", "_hash_hist"]],
        on="_business_key",
        how="left",
        suffixes=("", "_hist"),
    )

    # Identificar registros que mudaram (hash diferente)
    changed_mask = (
        merged["_hash_new"] != merged["_hash_hist"]
    ) & merged["_hash_hist"].notna()

    # Identificar registros novos (não existem no histórico)
    new_mask = merged["_hash_hist"].isna()

    # Identificar registros inalterados (hash igual)
    unchanged_mask = merged["_hash_new"] == merged["_hash_hist"]

    # Processar registros que mudaram
    if changed_mask.any():
        changed_business_keys = merged.loc[changed_mask, "_business_key"].unique()

        # Fechar versões antigas no histórico completo
        mask_close = df_historical_work.apply(
            lambda row: create_business_key(row, business_key_cols) in changed_business_keys,
            axis=1,
        ) & (df_historical_work[current_flag_col] == 1)

        df_historical_work.loc[mask_close, current_flag_col] = 0
        df_historical_work.loc[mask_close, date_data_valid_end_col] = date_update

        # Preparar novos registros (mudados)
        df_changed = df_new_work[changed_mask].copy()
        df_changed[date_update_col] = date_update
        df_changed[date_data_valid_start_col] = date_update
        df_changed[date_data_valid_end_col] = date_valid_end_ts
        df_changed[current_flag_col] = 1

        # Remover colunas auxiliares
        df_changed = df_changed.drop(columns=["_hash_new", "_business_key"])

        # Adicionar ao histórico
        df_historical_work = pd.concat([df_historical_work, df_changed], ignore_index=True)

    # Processar registros novos
    if new_mask.any():
        df_new_records = df_new_work[new_mask].copy()
        df_new_records[date_update_col] = date_update
        df_new_records[date_data_valid_start_col] = date_update
        df_new_records[date_data_valid_end_col] = date_valid_end_ts
        df_new_records[current_flag_col] = 1

        # Remover colunas auxiliares
        df_new_records = df_new_records.drop(columns=["_hash_new", "_business_key"])

        # Adicionar ao histórico
        df_historical_work = pd.concat([df_historical_work, df_new_records], ignore_index=True)

    # Registros inalterados não precisam ser processados (já estão no histórico)

    # Remover colunas auxiliares do histórico se existirem
    cols_to_drop = ["_hash_new", "_hash_hist", "_business_key"]
    existing_cols_to_drop = [col for col in cols_to_drop if col in df_historical_work.columns]
    if existing_cols_to_drop:
        df_historical_work = df_historical_work.drop(columns=existing_cols_to_drop)

    return df_historical_work


def apply_scd2_from_file(
    df_new: pd.DataFrame,
    historical_file_path: str,
    business_key_cols: List[str],
    data_cols: Optional[List[str]] = None,
    date_update: Optional[Union[str, datetime, date]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Aplica SCD2 carregando histórico de um arquivo.

    Parameters
    ----------
    df_new : pd.DataFrame
        DataFrame com dados novos/atualizados
    historical_file_path : str
        Caminho do arquivo com dados históricos (parquet, csv, etc.)
    business_key_cols : List[str]
        Lista de colunas que formam a chave de negócio
    data_cols : List[str], optional
        Lista de colunas de dados para comparação
    date_update : str, datetime ou date, optional
        Data de atualização
    **kwargs
        Argumentos adicionais passados para apply_scd2

    Returns
    -------
    pd.DataFrame
        DataFrame com versionamento SCD2 aplicado
    """
    import pathlib

    path = pathlib.Path(historical_file_path)

    if path.exists():
        if path.suffix == ".parquet":
            df_historical = pd.read_parquet(historical_file_path)
        elif path.suffix == ".csv":
            df_historical = pd.read_csv(historical_file_path)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {path.suffix}")
    else:
        df_historical = None

    return apply_scd2(
        df_new=df_new,
        df_historical=df_historical,
        business_key_cols=business_key_cols,
        data_cols=data_cols,
        date_update=date_update,
        **kwargs
    )

