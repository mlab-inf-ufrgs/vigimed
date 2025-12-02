import re
import pandas as pd
from unidecode import unidecode
from rapidfuzz import process, fuzz

# lista de formas "canônicas" para fuzzy decidir
CANONICAS = [
    "Comprimido",
    "Capsula",
    "Solucao injetavel",
    "Po para solucao injetavel",
    "Solucao para infusao",
    "Solucao oral",
    "Suspensao oral",
    "Suspensao injetavel",
    "Gotas orais",
    "Colirio",
    "Xarope",
    "Inalacao / spray",
    "Pomada",
    "Creme",
    "Gel",
    "Topico (solucao/locao)",
    "Adesivo transdermico",
    "Supositorio",
    "Implante",
    "Forma vaginal",
    "Desconhecida",
    "Outros",
]


def _normalizar_basico(txt: str) -> str:
    """Regras simples (sem fuzzy)."""
    if pd.isna(txt) or not str(txt).strip():
        return "Desconhecida"

    t = str(txt)
    t = unidecode(t).lower()
    t = re.sub(r'\s+', ' ', t).strip()

    # comprimidos / tablets / drágeas
    if ("tablet" in t or "comprim" in t or "drage" in t):
        return "Comprimido"

    # cápsulas
    if "capsul" in t:
        return "Capsula"

    # injetáveis
    if ("injet" in t or "inject" in t or re.search(r"\binj\b", t)):
        if "po" in t or "powder" in t or "liofil" in t:
            return "Po para solucao injetavel"
        return "Solucao injetavel"

    # soluções para infusão
    if "infus" in t:
        return "Solucao para infusao"

    # soluções orais / via oral
    if "oral" in t or "via oral" in t or re.fullmatch(r"vo", t):
        return "Solucao oral"

    # suspensões
    if "suspens" in t:
        if "injet" in t or "inject" in t:
            return "Suspensao injetavel"
        return "Suspensao oral"

    # gotas orais
    if ("gota" in t or "drops" in t) and "eye" not in t and "ocul" not in t:
        return "Gotas orais"

    # colírio / eye drops
    if "eye drops" in t or "colirio" in t or "colírio" in t:
        return "Colirio"

    # xarope
    if "xarope" in t or "syrup" in t:
        return "Xarope"

    # spray / aerossol / inalador
    if ("spray" in t or "aerosol" in t or "aerossol" in t
        or "inhal" in t or "inala" in t or "nebul" in t):
        return "Inalacao / spray"

    # tópicos
    if "pomada" in t or "ointment" in t:
        return "Pomada"
    if "cream" in t or "creme" in t:
        return "Creme"
    if "gel" in t:
        return "Gel"
    if "locao" in t or "lotion" in t or "cutaneous" in t:
        return "Topico (solucao/locao)"

    # adesivo / patch
    if "patch" in t or "adesivo" in t:
        return "Adesivo transdermico"

    # supositório
    if "supositor" in t or "suppository" in t:
        return "Supositorio"

    # implante
    if "implant" in t or "implante" in t:
        return "Implante"

    # vaginais
    if "vaginal" in t:
        return "Forma vaginal"

    # desconhecido explícito
    if "desconhec" in t or "unknown" in t:
        return "Desconhecida"

    return "Outros"


def normalizar_forma_farmaceutica_raw(txt: str, use_fuzzy: bool = True, threshold: int = 80) -> str:
    """
    Normaliza a forma farmacêutica:
      1) Aplica regras básicas.
      2) Se resultado for 'Outros' ou 'Desconhecida' e use_fuzzy=True,
         usa fuzzy para aproximar a uma forma canônica.

    threshold: score mínimo (0–100) para aceitar a sugestão fuzzy.
    """
    base = _normalizar_basico(txt)

    if not use_fuzzy:
        return base

    # só tenta fuzzy se base não for claramente boa
    if base not in ("Outros", "Desconhecida"):
        return base

    # texto normalizado pra comparar
    t = str(txt)
    t = unidecode(t).lower()
    t = re.sub(r'\s+', ' ', t).strip()

    if not t:
        return base

    # fuzzy: compara o texto com as formas CANONICAS
    best_label, score, _ = process.extractOne(
        t,
        CANONICAS,
        scorer=fuzz.token_set_ratio
    )

    if score >= threshold:
        return best_label

    return base

def criar_dim_forma_farmaceutica(df: pd.DataFrame,
                                 col_original: str = "FORMA_FARMACEUTICA",
                                 col_norm: str = "FORMA_FARMACEUTICA_CHAVE",
                                 pk_col: str = "FORMA_FARMACEUTICA_VALOR"):
    df = df.copy()

    df[col_norm] = df[col_original].apply(normalizar_forma_farmaceutica_raw)

    dim_forma = (
        df[[col_norm]]
        .drop_duplicates()
        .reset_index(drop=True)
        .rename(columns={col_norm: "FORMA_FARMACEUTICA"})
    )
    dim_forma[pk_col] = dim_forma.index + 1

    df = df.merge(
        dim_forma.rename(columns={"FORMA_FARMACEUTICA": col_norm}),
        on=col_norm,
        how="left"
    )

    return df, dim_forma
