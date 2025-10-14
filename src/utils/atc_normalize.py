import pandas as pd
import unicodedata
from typing import Optional, List, Dict

def _strip_accents(s: str) -> str:
    """Remove acentos e normaliza string."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def normalize_principio_ativo_atc(
    df: pd.DataFrame,
    atc_col: str = "CODIGO_ATC",
    ativo_col: str = "PRINCIPIOS_ATIVOS_WHODRUG",
    pk_atc_col: str = "PK_ATC",
    descricao_col: str = "DESCRICAO",
    regras: Optional[List[Dict[str, str]]] = None
) -> pd.DataFrame:
    """
    Cria colunas `PK_ATC` e `DESCRICAO` baseado em regras.
    
    Cada regra deve conter:
        - 'atc': código ATC a comparar com a coluna CODIGO_ATC
        - 'principio': princípio ativo a comparar
        - 'pk': valor que será atribuído à PK_ATC
        - 'descricao': valor que será atribuído à DESCRICAO
    """
    if not regras:
        raise ValueError("Forneça `regras` como lista de dicts: {'atc','principio','pk','descricao'}.")

    # inicializa colunas
    df[pk_atc_col] = "outros"
    df[descricao_col] = "outros"

    # normaliza colunas do df para comparação
    atc_norm = df[atc_col].astype(str).fillna("").str.upper().map(_strip_accents)
    ativo_norm = df[ativo_col].astype(str).fillna("").str.upper().map(_strip_accents)

    for r in regras:
        atc_rule = _strip_accents(r["atc"].upper())
        principio_rule = _strip_accents(r["principio"].upper())
        pk_rule = r["pk"]
        descricao_rule = r["descricao"].upper()

        # máscara: ATC bate e princípio ativo bate
        mask = (atc_norm == atc_rule) & (ativo_norm == principio_rule)

        df.loc[mask, pk_atc_col] = pk_rule
        df.loc[mask, descricao_col] = descricao_rule

    return df