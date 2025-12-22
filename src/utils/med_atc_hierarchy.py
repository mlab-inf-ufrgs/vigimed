"""
Funções para criar dimensão ATC com estrutura hierárquica de 5 níveis.
A estrutura ATC oficial possui apenas 5 níveis: 1, 3, 4, 5 e 7 (níveis 2 e 6 não existem).
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, Dict


def extract_atc_levels(atc_code: str) -> Dict[str, Optional[str]]:
    """
    Extrai os níveis hierárquicos de um código ATC.
    
    Estrutura dos níveis (apenas os que existem na estrutura ATC):
    - ATC_CODE_LEVEL_1: 1 caractere (ex: A) - Nível 1
    - ATC_CODE_LEVEL_2: 3 caracteres (ex: A01) - Nível 2
    - ATC_CODE_LEVEL_3: 4 caracteres (ex: A01A) - Nível 3
    - ATC_CODE_LEVEL_4: 5 caracteres (ex: A01AA) - Nível 4
    - ATC_CODE_LEVEL_5: 7 caracteres (ex: A01AA02) - Nível 5
    
    Nota: Os níveis 2 e 6 não existem na estrutura ATC oficial.
    
    Parameters:
    -----------
    atc_code : str
        Código ATC completo (ex: "A01AA02")
        
    Returns:
    --------
    dict
        Dicionário com os níveis extraídos (apenas os que existem)
    """
    if not atc_code or pd.isna(atc_code):
        return {
            'ATC_CODE_LEVEL_1': None,
            'ATC_CODE_LEVEL_2': None,
            'ATC_CODE_LEVEL_3': None,
            'ATC_CODE_LEVEL_4': None,
            'ATC_CODE_LEVEL_5': None
        }
    
    atc_str = str(atc_code).strip().upper()
    
    # Extrair apenas os níveis que existem na estrutura ATC
    # Nível 1: 1 caractere, Nível 2: 3 caracteres, Nível 3: 4 caracteres,
    # Nível 4: 5 caracteres, Nível 5: 7 caracteres
    levels = {
        'ATC_CODE_LEVEL_1': atc_str[0] if len(atc_str) >= 1 else None,
        'ATC_CODE_LEVEL_2': atc_str[:3] if len(atc_str) >= 3 else None,
        'ATC_CODE_LEVEL_3': atc_str[:4] if len(atc_str) >= 4 else None,
        'ATC_CODE_LEVEL_4': atc_str[:5] if len(atc_str) >= 5 else None,
        'ATC_CODE_LEVEL_5': atc_str[:7] if len(atc_str) >= 7 else None
    }
    
    return levels


def build_dim_atc(
    df: pd.DataFrame,
    atc_code_col: str = 'ATC code',
    atc_name_col: str = 'ATC level name',
    ddd_col: Optional[str] = 'DDD',
    unit_col: Optional[str] = 'Unit',
    adm_r_col: Optional[str] = 'Adm.R',
    comment_col: Optional[str] = 'Comment'
) -> pd.DataFrame:
    """
    Constrói a dimensão ATC (dim_atc) com estrutura hierárquica de 5 níveis.
    
    A função cria:
    - Colunas ATC_CODE_LEVEL_1, ATC_CODE_LEVEL_2, ATC_CODE_LEVEL_3, ATC_CODE_LEVEL_4, ATC_CODE_LEVEL_5 com os códigos hierárquicos
      (níveis 2 e 6 não existem na estrutura ATC oficial)
    - Coluna ATC_LEVEL com o comprimento do código ATC (1, 3, 4, 5, ou 7)
    - Colunas ATC_CODE_LEVEL_1_LEVEL_NAME, ATC_CODE_LEVEL_2_LEVEL_NAME, ATC_CODE_LEVEL_3_LEVEL_NAME,
      ATC_CODE_LEVEL_4_LEVEL_NAME, ATC_CODE_LEVEL_5_LEVEL_NAME com os nomes dos níveis
    - Mantém informações adicionais (DDD, Unit, Adm.R, Comment)
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame com dados ATC do arquivo Excel
    atc_code_col : str
        Nome da coluna com o código ATC completo
    atc_name_col : str
        Nome da coluna com o nome do nível ATC
    ddd_col : str, optional
        Nome da coluna com DDD (Defined Daily Dose)
    unit_col : str, optional
        Nome da coluna com unidade
    adm_r_col : str, optional
        Nome da coluna com via de administração
    comment_col : str, optional
        Nome da coluna com comentários
        
    Returns:
    --------
    pd.DataFrame
        DataFrame dim_atc com estrutura hierárquica incluindo códigos e nomes dos níveis
    """
    # Criar cópia do DataFrame
    dim_atc = df.copy()
    
    # Garantir que a coluna de código ATC existe
    if atc_code_col not in dim_atc.columns:
        raise ValueError(f"Coluna '{atc_code_col}' não encontrada no DataFrame")
    
    # Extrair níveis hierárquicos para cada código ATC
    levels_list = []
    for idx, row in dim_atc.iterrows():
        atc_code = row[atc_code_col]
        levels = extract_atc_levels(atc_code)
        levels_list.append(levels)
    
    # Criar DataFrame com os níveis
    levels_df = pd.DataFrame(levels_list)
    
    # Adicionar níveis ao DataFrame principal
    for col in levels_df.columns:
        dim_atc[col] = levels_df[col]
    
    # Adicionar coluna ATC_LEVEL mapeando comprimento do código ATC para nível lógico
    # Mapeamento: 1 -> 1, 3 -> 2, 4 -> 3, 5 -> 4, 7 -> 5
    code_length = dim_atc[atc_code_col].astype(str).str.len()
    dim_atc['ATC_LEVEL'] = np.where(code_length == 1, 1,
                          np.where(code_length == 3, 2,
                          np.where(code_length == 4, 3,
                          np.where(code_length == 5, 4,
                          np.where(code_length == 7, 5, None)))))
    
    # Criar mapeamento de nomes para cada nível hierárquico
    # Para cada nível, criar um dicionário código -> nome
    # O mapeamento é feito baseado no comprimento do código ATC original
    # Apenas processar os níveis que existem: 1, 3, 4, 5, 7 (níveis 2 e 6 não existem)
    level_name_mappings = {}
    
    # Comprimentos esperados para cada nível (apenas os que existem)
    # Mapeamento: nível lógico -> (comprimento esperado, nome da coluna)
    level_configs = {
        1: (1, 'ATC_CODE_LEVEL_1'),   # 1 caractere
        2: (3, 'ATC_CODE_LEVEL_2'),   # 3 caracteres (nível 2 real)
        3: (4, 'ATC_CODE_LEVEL_3'),   # 4 caracteres (nível 3 real)
        4: (5, 'ATC_CODE_LEVEL_4'),   # 5 caracteres (nível 4 real)
        5: (7, 'ATC_CODE_LEVEL_5')    # 7 caracteres (nível 5 real)
    }
    
    for level_num, (expected_len, level_col) in level_configs.items():
        level_name_col = f'{level_col}_LEVEL_NAME'
        
        # Criar mapeamento: código do nível -> nome
        # Pegar apenas linhas onde o código ATC tem o tamanho correspondente ao nível
        level_mapping = {}
        
        for idx, row in dim_atc.iterrows():
            atc_code = str(row[atc_code_col]).strip().upper() if pd.notna(row[atc_code_col]) else ''
            level_code = row[level_col]
            # Forçar nomes de nível em caixa alta para padronização
            level_name = (
                str(row[atc_name_col]).upper()
                if pd.notna(row[atc_name_col])
                else None
            )
            
            # Se o código ATC tem o tamanho exato do nível, esse é o nome do nível
            if len(atc_code) == expected_len and pd.notna(level_code) and level_name:
                # Se já existe um mapeamento para esse código, manter o primeiro (ou fazer merge)
                if level_code not in level_mapping:
                    level_mapping[level_code] = level_name
        
        # Aplicar mapeamento
        dim_atc[level_name_col] = dim_atc[level_col].map(level_mapping)
        level_name_mappings[level_name_col] = level_mapping
    
    # Reordenar colunas: códigos hierárquicos primeiro, depois nível, depois nomes, depois informações adicionais
    # Apenas incluir os níveis que existem: 1, 3, 4, 5, 7 (níveis 2 e 6 não existem)
    base_cols = [
        'ATC_CODE_LEVEL_1', 'ATC_CODE_LEVEL_2', 'ATC_CODE_LEVEL_3',
        'ATC_CODE_LEVEL_4', 'ATC_CODE_LEVEL_5'
    ]
    
    # Coluna com o nível (comprimento do código ATC)
    level_col_list = ['ATC_LEVEL']
    
    # Colunas de nomes dos níveis (apenas para os níveis que existem)
    level_name_cols = [
        'ATC_CODE_LEVEL_1_LEVEL_NAME', 'ATC_CODE_LEVEL_2_LEVEL_NAME',
        'ATC_CODE_LEVEL_3_LEVEL_NAME', 'ATC_CODE_LEVEL_4_LEVEL_NAME',
        'ATC_CODE_LEVEL_5_LEVEL_NAME'
    ]
    
    # Colunas de informação (manter as que existem)
    info_cols = [atc_code_col, atc_name_col]
    if ddd_col and ddd_col in dim_atc.columns:
        info_cols.append(ddd_col)
    if unit_col and unit_col in dim_atc.columns:
        info_cols.append(unit_col)
    if adm_r_col and adm_r_col in dim_atc.columns:
        info_cols.append(adm_r_col)
    if comment_col and comment_col in dim_atc.columns:
        info_cols.append(comment_col)
    
    # Ordem final das colunas: códigos, nível, nomes dos níveis, informações adicionais
    final_cols = base_cols + level_col_list + level_name_cols + info_cols
    
    # Adicionar outras colunas que possam existir
    other_cols = [col for col in dim_atc.columns if col not in final_cols]
    final_cols = final_cols + other_cols
    
    # Reordenar
    dim_atc = dim_atc[final_cols]
    
    # Remover duplicatas baseado nos códigos hierárquicos
    dim_atc = dim_atc.drop_duplicates(subset=base_cols, keep='first')
    
    # Ordenar por códigos hierárquicos
    dim_atc = dim_atc.sort_values(by=base_cols).reset_index(drop=True)
    
    return dim_atc


def expand_atc_hierarchy_from_codes(atc_codes: pd.Series) -> pd.DataFrame:
    """
    Cria dim_atc a partir de uma série de códigos ATC únicos.
    Útil quando você tem apenas os códigos e quer criar a estrutura hierárquica.
    
    Parameters:
    -----------
    atc_codes : pd.Series
        Série com códigos ATC únicos
        
    Returns:
    --------
    pd.DataFrame
        DataFrame dim_atc com estrutura hierárquica
    """
    # Remover duplicatas e valores nulos
    unique_codes = atc_codes.dropna().unique()
    
    # Extrair níveis para cada código
    levels_list = []
    for code in unique_codes:
        levels = extract_atc_levels(code)
        levels['ATC_CODE'] = code  # Manter o código original
        levels_list.append(levels)
    
    dim_atc = pd.DataFrame(levels_list)
    
    # Reordenar colunas (apenas os níveis que existem: 1, 3, 4, 5, 7)
    base_cols = [
        'ATC_CODE_LEVEL_1', 'ATC_CODE_LEVEL_2', 'ATC_CODE_LEVEL_3',
        'ATC_CODE_LEVEL_4', 'ATC_CODE_LEVEL_5'
    ]
    final_cols = base_cols + ['ATC_CODE']
    dim_atc = dim_atc[final_cols]
    
    # Ordenar
    dim_atc = dim_atc.sort_values(by=base_cols).reset_index(drop=True)
    
    return dim_atc

