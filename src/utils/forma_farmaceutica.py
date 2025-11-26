import re
import pandas as pd
from unidecode import unidecode

def normalizar_forma_farmaceutica_raw(txt: str) -> str:
    """
    Recebe o texto original da forma farmacêutica e devolve
    uma categoria padronizada (para usar na dimensão).
    """
    if pd.isna(txt) or not str(txt).strip():
        return "Desconhecido"

    t = str(txt)
    t = unidecode(t).lower()
    t = re.sub(r'\s+', ' ', t).strip()
    
    # *** comprimidos / tablets ***
    if ("tablet" in t or "comprim" in t or "drage" in t
        or "orodispers" in t):
        return "Comprimido"

    # *** cápsulas ***
    if "capsul" in t:
        return "Capsula"

    # *** injetável / solução injetável ***
    if ("injet" in t or "inject" in t or re.search(r"\binj\b", t)):
        # Pó para reconstituição injetável
        if "po" in t or "powder" in t or "liofil" in t:
            return "Po para solucao injetavel"
        return "Solucao injetavel"

    # *** soluções para infusão ***
    if "infus" in t:
        return "Solucao para infusao"

    # *** soluções orais / via oral ***
    if "oral" in t or "via oral" in t or re.fullmatch(r"vo", t):
        return "Solucao oral"

    # *** suspensões ***
    if "suspens" in t:
        if "injet" in t or "inject" in t:
            return "Suspensao injetavel"
        return "Suspensao oral"

    # *** gotas / drops (não oftálmico) ***
    if ("gota" in t or "drops" in t) and "eye" not in t and "ocul" not in t:
        return "Gotas orais"

    # *** colírio / eye drops ***
    if "eye drops" in t or "colirio" in t or "colirio" in t:
        return "Colirio"

    # *** xaropes ***
    if "xarope" in t or "syrup" in t:
        return "Xarope"

    # *** spray / aerossol / inalador ***
    if ("spray" in t or "aerosol" in t or "aerossol" in t
        or "inhal" in t or "inala" in t or "nebul" in t):
        return "Inalacao / spray"

    # *** tópicos: creme, gel, pomada, loção, solução tópica ***
    if "pomada" in t or "ointment" in t:
        return "Pomada"
    if "cream" in t or "creme" in t:
        return "Creme"
    if "gel" in t:
        return "Gel"
    if "locao" in t or "lotion" in t or "cutaneous" in t:
        return "Topico (solucao/locao)"

    # *** adesivo / patch ***
    if "patch" in t or "adesivo" in t:
        return "Adesivo transdermico"

    # *** supositório ***
    if "supositor" in t or "suppository" in t:
        return "Supositorio"

    # *** implante ***
    if "implant" in t or "implante" in t:
        return "Implante"

    # *** vaginais ***
    if "vaginal" in t:
        return "Forma vaginal"

    # *** desconhecido / lixo / nome de contraste/medicamento ***
    if "desconhec" in t or "unknown" in t:
        return "Desconhecido"

    # fallback
    return "Outros"

def criar_dim_forma_farmaceutica(df: pd.DataFrame,
                                 col_original: str = "FORMA_FARMACEUTICA",
                                 col_norm: str = "FORMA_FARMACEUTICA_NORM",
                                 pk_col: str = "PK_FORMA_FARMACEUTICA"):
    """
    - Normaliza a coluna de forma farmacêutica
    - Cria uma dimensão com ID
    - Devolve (df_atualizado, dim_forma)
    """
    df = df.copy()

    # coluna normalizada
    df[col_norm] = df[col_original].apply(normalizar_forma_farmaceutica_raw)

    # dimensão (uma linha por forma normalizada)
    dim_forma = (
        df[[col_norm]]
        .drop_duplicates()
        .reset_index(drop=True)
        .rename(columns={col_norm: "FORMA_FARMACEUTICA"})
    )
    dim_forma[pk_col] = dim_forma.index + 1  # 1,2,3,...

    # traz o PK de volta pro fato (FK)
    df = df.merge(
        dim_forma.rename(columns={"FORMA_FARMACEUTICA": col_norm}),
        on=col_norm,
        how="left"
    )

    return df, dim_forma
