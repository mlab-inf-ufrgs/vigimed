import pandas as pd
from unidecode import unidecode
from rapidfuzz import process, fuzz

# 1. Palavras canônicas -> códigos finais
CANONICAL_KEYWORDS = {
    "Implant": [
        "implant",
        "intrauterine delivery system",
        "intrauterino",
        "intra-uterino","braço"
    ],
    "Inhal": [
        "inhalacao", "inhalation", "inalatorio", "inalatoria",
        "aerosol", "nebulizacao", "respiratoria", "uso inalatorio",
    ],
    "Instill": [
        "oftalmica", "oftalmico", "ophthalmic",
        "colirio", "ocular", "otologica", "auricular","ocular"
    ],
    "N": [
        "nasal", "intranasal", "spray nasal",
    ],
    "O": [
        "via oral", "oral", "uso oral",
        "oral use",
        "enteral", "gastroenteral", "gastroenterica",
        "sonda nasogastrica", "nasogastric tube",
        "sonda nasoenteral", "gastrostomia", "jejunostomia","nasoenteral"
    ],
    "P": [
        "intravenosa", "intravenoso", "endovenosa", "endovenoso","ev / iv",
        "intravenous"
        "ev", "iv", "infusao", "bolus", "bomba de infusao",
        "intramuscular", "im",
        "subcutanea", "subcutaneo", "sc",
        "hipodermoclise",
        "intratecal", "intrathecal", "raquidiana", "epidural", "peridural",
        "intraperitoneal", "intracavitaria", "intravesical",
        "hemodialise", "extracorporea",
        "parenteral",
        "intravitreal", "intravitre",
        "dental",
        "transplacental", "transmamaria", "transmammary","intramuscular",
        "tranplacental"
    ],
    "R": [
        "retal", "via retal", "rectal",
    ],
    "SL": [
        "sublingual", "buccal", "bucal", "oromucosal", "oromucosa",
    ],
    "TD": [
        "topica", "topico", "tópica", "tópico",
        "cutanea", "cutaneo", "cutaneous",
        "dermatologica",
        "transdermica", "transdermico", "transdermal",
        "percutanea",
    ],
    "V": [
        "vaginal", "intravaginal",
    ],
}

# 2. Lista auxiliar para fuzzy: (palavra_canonica_normalizada, codigo)
CANONICAL_FLAT = []
for code, words in CANONICAL_KEYWORDS.items():
    for w in words:
        CANONICAL_FLAT.append(
            (unidecode(w).lower().strip(), code)
        )

UNKNOWN_TOKENS = [
    "unknown", "desconhecid", "e2b r2 code: 065", "e2b r2 code: 050",
    "nao informado", "não informado", "nao informada", "não informada",
    "nao perguntado", "não perguntado",
    "nao questionado", "não questionado",
    "via desconhecida", "rota desconhecida",
    "via de administracao nao informada",
    "via de administracao nao especificada",
    "route of administration not applicable",
]


def _preprocess(text: str) -> str:
    return " ".join(unidecode(str(text)).lower().strip().split())


def _is_unknown(s: str) -> bool:
    if s in {"", "none", "nan", "na", "n/a"}:
        return True
    return any(tok in s for tok in UNKNOWN_TOKENS)


def normalizar_via_fuzzy(value: str,
                         score_threshold: int = 80) -> str:
    """
    Normaliza via de administração usando fuzzy matching
    contra palavras canônicas definidas em CANONICAL_KEYWORDS.
    Retorna um dos códigos:
      Implant, Inhal, Instill, N, O, P, R, SL, TD, V
    ou 'desconhecido'.
    """
    if pd.isna(value):
        return "desconhecido"

    s = _preprocess(value)

    # 1) Desconhecido explícito
    if _is_unknown(s):
        return "desconhecido"

    # 2) Tratamento simples de combinações claras:
    #    se tiver oral + venoso/subcutâneo, prioriza P
    has_oral = "oral" in s
    has_parenteral_token = any(
        t in s
        for t in ("intraven", "endoven", "venos", "intramus", "subcut", "hipodermoclise")
    )
    if has_oral and has_parenteral_token:
        return "P"

    # 3) Fuzzy: compara a string s com todas as palavras canônicas
    candidates = [w for (w, _) in CANONICAL_FLAT]
    best, score, idx = process.extractOne(
        s,
        candidates,
        scorer=fuzz.partial_ratio
    )

    if score < score_threshold:
        return "desconhecido"

    # recupera o código associado à palavra canônica escolhida
    canon_word, code = CANONICAL_FLAT[idx]
    return code
