"""
Utilitários para matching entre reações do VigiMed e hierarquia MedDRA.

Funções principais:
- meddra_exact_match: Join exato usando colunas normalizadas
- meddra_fuzzy_match: Fuzzy matching para registros não encontrados
- meddra_match_pipeline: Pipeline completo (exato + fuzzy)
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process


def _normalize_text(text: str) -> str:
    """
    Normaliza texto para comparação: remove acentos, caracteres especiais, 
    converte para minúsculas e padroniza espaços.
    """
    import re
    import unicodedata
    
    if pd.isna(text):
        return ''
    
    text = str(text).lower().strip()
    # Remove acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Remove caracteres especiais (mantém apenas letras, números e espaços)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _normalize_series(series: pd.Series) -> pd.Series:
    """Aplica normalização a uma Series inteira."""
    return series.apply(_normalize_text)


def _add_normalized_columns(
    df: pd.DataFrame, 
    columns: List[str],
    suffix: str = '_NORM'
) -> pd.DataFrame:
    """
    Adiciona colunas normalizadas ao DataFrame.
    
    Args:
        df: DataFrame original
        columns: Lista de colunas para normalizar
        suffix: Sufixo das colunas normalizadas
        
    Returns:
        DataFrame com colunas normalizadas adicionadas
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[f'{col}{suffix}'] = _normalize_series(df[col])
    return df


def meddra_exact_match(
    vigimed_df: pd.DataFrame,
    meddra_df: pd.DataFrame,
    *,
    vigimed_cols: Dict[str, str] = None,
    meddra_cols: Dict[str, str] = None,
    prioritize_primary: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Realiza match exato entre reações do VigiMed e hierarquia MedDRA
    usando colunas normalizadas.
    
    Args:
        vigimed_df: DataFrame com reações do VigiMed
        meddra_df: DataFrame com hierarquia MedDRA (dim_soc_llt)
        vigimed_cols: Mapeamento de colunas VigiMed -> nome padrão
                      Ex: {'REACAO_EVTO_ADVERSO_MEDDRA_LLT': 'LLT', 'SOC': 'SOC', ...}
        meddra_cols: Mapeamento de colunas MedDRA -> nome padrão
                     Ex: {'LLT_NAME': 'LLT', 'SOC_NAME': 'SOC', ...}
        prioritize_primary: Se True, prioriza linhas com PRIMARY_FLAG = 'Y'
        
    Returns:
        Tuple com (matched_df, no_match_df)
    """
    # Mapeamentos padrão
    if vigimed_cols is None:
        vigimed_cols = {
            'REACAO_EVTO_ADVERSO_MEDDRA_LLT': 'LLT',
            'PT': 'PT',
            'HLT': 'HLT', 
            'HLGT': 'HLGT',
            'SOC': 'SOC'
        }
    
    if meddra_cols is None:
        meddra_cols = {
            'LLT_NAME': 'LLT',
            'PT_NAME': 'PT',
            'HLT_NAME': 'HLT',
            'HLGT_NAME': 'HLGT',
            'SOC_NAME': 'SOC'
        }
    
    # Colunas para join
    join_cols = ['LLT', 'PT', 'HLT', 'HLGT', 'SOC']
    norm_cols = [f'{col}_NORM' for col in join_cols]
    
    # Preparar VigiMed
    vigimed_work = vigimed_df.copy()
    for orig_col, new_col in vigimed_cols.items():
        if orig_col in vigimed_work.columns and orig_col != new_col:
            vigimed_work = vigimed_work.rename(columns={orig_col: new_col})
    vigimed_work = _add_normalized_columns(vigimed_work, join_cols)
    
    # Preparar MedDRA
    meddra_work = meddra_df.copy()
    for orig_col, new_col in meddra_cols.items():
        if orig_col in meddra_work.columns and orig_col != new_col:
            meddra_work = meddra_work.rename(columns={orig_col: new_col})
    meddra_work = _add_normalized_columns(meddra_work, join_cols)
    
    # Priorizar PRIMARY_FLAG = 'Y'
    if prioritize_primary and 'PRIMARY_FLAG' in meddra_work.columns:
        meddra_work = meddra_work.sort_values('PRIMARY_FLAG', ascending=False)
    
    # Remover duplicatas mantendo a primeira (PRIMARY_FLAG = 'Y')
    meddra_dedup = meddra_work.drop_duplicates(subset=norm_cols, keep='first')
    
    # Join usando colunas normalizadas
    joined = vigimed_work.merge(
        meddra_dedup,
        on=norm_cols,
        how='left',
        suffixes=('_VIGIMED', '_MEDDRA')
    )
    
    # Separar matched e não matched
    llt_meddra_col = 'LLT_MEDDRA' if 'LLT_MEDDRA' in joined.columns else 'LLT'
    matched_mask = joined[llt_meddra_col].notna() if llt_meddra_col in joined.columns else joined['LLT_CODE'].notna()
    
    # Identificar coluna de código LLT
    llt_code_col = 'LLT_CODE' if 'LLT_CODE' in joined.columns else None
    if llt_code_col:
        matched_mask = joined[llt_code_col].notna()
    
    matched_df = joined[matched_mask].copy()
    no_match_df = joined[~matched_mask].copy()
    
    return matched_df, no_match_df


def meddra_fuzzy_match(
    no_match_df: pd.DataFrame,
    meddra_df: pd.DataFrame,
    *,
    threshold: int = 75,
    weights: Dict[str, float] = None,
    meddra_cols: Dict[str, str] = None,
) -> pd.DataFrame:
    """
    Realiza fuzzy matching para registros que não tiveram match exato.
    
    Args:
        no_match_df: DataFrame com registros sem match (output de meddra_exact_match)
        meddra_df: DataFrame com hierarquia MedDRA original
        threshold: Score mínimo para aceitar match (0-100)
        weights: Pesos para cada coluna no score combinado
                 Ex: {'LLT': 0.4, 'PT': 0.25, 'HLT': 0.15, 'HLGT': 0.1, 'SOC': 0.1}
        meddra_cols: Mapeamento de colunas MedDRA
        
    Returns:
        DataFrame com matches fuzzy e scores
    """
    if weights is None:
        weights = {
            'LLT': 0.40,
            'PT': 0.25,
            'HLT': 0.15,
            'HLGT': 0.10,
            'SOC': 0.10
        }
    
    if meddra_cols is None:
        meddra_cols = {
            'LLT_NAME': 'LLT',
            'PT_NAME': 'PT',
            'HLT_NAME': 'HLT',
            'HLGT_NAME': 'HLGT',
            'SOC_NAME': 'SOC'
        }
    
    # Preparar MedDRA com colunas normalizadas
    meddra_work = meddra_df.copy()
    for orig_col, new_col in meddra_cols.items():
        if orig_col in meddra_work.columns:
            meddra_work[f'{new_col}_NORM'] = _normalize_series(meddra_work[orig_col])
    
    # Lista de LLTs únicos para busca rápida
    llt_norm_col = 'LLT_NORM'
    if llt_norm_col not in meddra_work.columns:
        meddra_work[llt_norm_col] = _normalize_series(meddra_work.get('LLT_NAME', meddra_work.get('LLT', '')))
    
    dim_llt_list = meddra_work[llt_norm_col].dropna().unique().tolist()
    
    results = []
    
    for idx, row in no_match_df.iterrows():
        # Obter LLT normalizado do VigiMed
        llt_vigimed = str(row.get('LLT_NORM', '')) if pd.notna(row.get('LLT_NORM')) else ''
        
        if not llt_vigimed:
            result = row.to_dict()
            result['MATCH_SCORE'] = 0
            result['MATCH_TYPE'] = 'NO_MATCH'
            results.append(result)
            continue
        
        # Buscar top 5 matches por LLT
        matches = process.extract(
            llt_vigimed,
            dim_llt_list,
            scorer=fuzz.ratio,
            limit=5
        )
        
        best_score = 0
        best_match = None
        
        for match_llt, llt_score, _ in matches:
            # Filtrar candidatos por esse LLT
            candidates = meddra_work[meddra_work[llt_norm_col] == match_llt]
            
            for _, meddra_row in candidates.iterrows():
                # Calcular score para cada coluna
                scores = {}
                scores['LLT'] = llt_score
                
                for col in ['PT', 'HLT', 'HLGT', 'SOC']:
                    vigimed_val = str(row.get(f'{col}_NORM', '')) if pd.notna(row.get(f'{col}_NORM')) else ''
                    meddra_val = str(meddra_row.get(f'{col}_NORM', '')) if pd.notna(meddra_row.get(f'{col}_NORM')) else ''
                    scores[col] = fuzz.ratio(vigimed_val, meddra_val)
                
                # Score ponderado
                combined_score = sum(scores[col] * weights[col] for col in weights)
                
                # Bônus para PRIMARY_FLAG = 'Y'
                if meddra_row.get('PRIMARY_FLAG') == 'Y':
                    combined_score += 1
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = meddra_row
        
        # Montar resultado
        result = row.to_dict()
        result['MATCH_SCORE'] = round(best_score, 2)
        
        if best_score >= threshold and best_match is not None:
            result['MATCH_TYPE'] = 'FUZZY'
            result['REACAO_CHAVE'] = best_match.get('REACAO_CHAVE')
            result['LLT_CODE'] = best_match.get('LLT_CODE')
            result['LLT_MEDDRA'] = best_match.get('LLT_NAME')
            result['PT_CODE'] = best_match.get('PT_CODE')
            result['PT_MEDDRA'] = best_match.get('PT_NAME')
            result['HLT_CODE'] = best_match.get('HLT_CODE')
            result['HLT_MEDDRA'] = best_match.get('HLT_NAME')
            result['HLGT_CODE'] = best_match.get('HLGT_CODE')
            result['HLGT_MEDDRA'] = best_match.get('HLGT_NAME')
            result['SOC_CODE'] = best_match.get('SOC_CODE')
            result['SOC_MEDDRA'] = best_match.get('SOC_NAME')
            result['PRIMARY_FLAG'] = best_match.get('PRIMARY_FLAG')
        else:
            result['MATCH_TYPE'] = 'NO_MATCH'
            result['REACAO_CHAVE'] = None
        
        results.append(result)
    
    return pd.DataFrame(results)


def meddra_match_pipeline(
    vigimed_df: pd.DataFrame,
    meddra_df: pd.DataFrame,
    *,
    vigimed_cols: Dict[str, str] = None,
    meddra_cols: Dict[str, str] = None,
    fuzzy_threshold: int = 75,
    fuzzy_weights: Dict[str, float] = None,
    run_fuzzy: bool = True,
    output_mode: str = 'all',
    key_column: str = 'REACAO_CHAVE',
    extra_columns: List[str] = None,
) -> pd.DataFrame:
    """
    Pipeline completo de matching entre VigiMed e MedDRA.
    
    1. Executa match exato com colunas normalizadas
    2. Para registros não encontrados, executa fuzzy matching
    3. Combina resultados
    
    Args:
        vigimed_df: DataFrame com reações do VigiMed
        meddra_df: DataFrame com hierarquia MedDRA (dim_soc_llt)
        vigimed_cols: Mapeamento de colunas VigiMed
        meddra_cols: Mapeamento de colunas MedDRA
        fuzzy_threshold: Score mínimo para fuzzy match
        fuzzy_weights: Pesos para score fuzzy combinado
        run_fuzzy: Se True, executa fuzzy para não encontrados
        output_mode: Modo de saída das colunas:
            - 'all': Retorna todas as colunas (default)
            - 'slim': Retorna apenas colunas originais + key_column + MATCH_TYPE + MATCH_SCORE
            - 'minimal': Retorna apenas colunas originais + key_column
        key_column: Coluna chave do MedDRA para incluir no output slim/minimal (default: 'REACAO_CHAVE')
        extra_columns: Lista de colunas adicionais do MedDRA para incluir no output slim
        
    Returns:
        DataFrame combinado com todos os matches
    """
    # Guardar colunas originais do input
    original_columns = list(vigimed_df.columns)
    
    # Etapa 1: Match exato
    matched_df, no_match_df = meddra_exact_match(
        vigimed_df,
        meddra_df,
        vigimed_cols=vigimed_cols,
        meddra_cols=meddra_cols,
    )
    
    matched_df['MATCH_TYPE'] = 'EXACT'
    matched_df['MATCH_SCORE'] = 100.0
    
    print(f"Match exato: {len(matched_df)} registros")
    print(f"Sem match: {len(no_match_df)} registros")
    
    # Etapa 2: Fuzzy matching (opcional)
    if run_fuzzy and len(no_match_df) > 0:
        print(f"Executando fuzzy matching com threshold={fuzzy_threshold}...")
        
        fuzzy_df = meddra_fuzzy_match(
            no_match_df,
            meddra_df,
            threshold=fuzzy_threshold,
            weights=fuzzy_weights,
            meddra_cols=meddra_cols,
        )
        
        fuzzy_matched = fuzzy_df[fuzzy_df['MATCH_TYPE'] == 'FUZZY']
        fuzzy_no_match = fuzzy_df[fuzzy_df['MATCH_TYPE'] == 'NO_MATCH']
        
        print(f"Fuzzy matched: {len(fuzzy_matched)} registros")
        print(f"Sem match final: {len(fuzzy_no_match)} registros")
        
        # Combinar resultados
        result_df = pd.concat([matched_df, fuzzy_df], ignore_index=True)
    else:
        no_match_df['MATCH_TYPE'] = 'NO_MATCH'
        no_match_df['MATCH_SCORE'] = 0.0
        result_df = pd.concat([matched_df, no_match_df], ignore_index=True)
    
    # Filtrar colunas conforme output_mode
    if output_mode == 'slim':
        # Colunas originais + chave + tipo/score + extras
        output_cols = original_columns.copy()
        
        # Adicionar coluna chave se existir
        if key_column in result_df.columns:
            output_cols.append(key_column)
        
        # Adicionar colunas extras
        if extra_columns:
            for col in extra_columns:
                if col in result_df.columns and col not in output_cols:
                    output_cols.append(col)
        
        # Adicionar metadados de match
        output_cols.extend(['MATCH_TYPE', 'MATCH_SCORE'])
        
        # Filtrar apenas colunas existentes
        output_cols = [c for c in output_cols if c in result_df.columns]
        result_df = result_df[output_cols]
        
    elif output_mode == 'minimal':
        # Apenas colunas originais + chave
        output_cols = original_columns.copy()
        
        if key_column in result_df.columns:
            output_cols.append(key_column)
        
        # Filtrar apenas colunas existentes
        output_cols = [c for c in output_cols if c in result_df.columns]
        result_df = result_df[output_cols]
    
    # output_mode == 'all' retorna todas as colunas
    
    return result_df


def get_match_summary(result_df: pd.DataFrame) -> pd.DataFrame:
    """
    Gera resumo estatístico dos matches.
    
    Args:
        result_df: DataFrame resultante do pipeline
        
    Returns:
        DataFrame com estatísticas por tipo de match
    """
    summary = result_df.groupby('MATCH_TYPE').agg(
        count=('MATCH_TYPE', 'size'),
        avg_score=('MATCH_SCORE', 'mean'),
        min_score=('MATCH_SCORE', 'min'),
        max_score=('MATCH_SCORE', 'max'),
    ).reset_index()
    
    summary['pct'] = (summary['count'] / summary['count'].sum() * 100).round(2)
    
    return summary
