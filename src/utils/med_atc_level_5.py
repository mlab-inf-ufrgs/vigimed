"""Inferência de ATC nível 5 a partir de `fat_medicamentos` + `dim_atc`.

Estratégia:
1. Candidatos `dim_atc` com ``ATC_LEVEL == 5`` no mesmo ``ATC_CODE_LEVEL_4``.
2. Match do princípio ativo WHO-Drug (PT ou EN) contra ``ATC_NAME_LEVEL`` /
   ``ATC_CODE_LEVEL_5_LEVEL_NAME``, com normalização de acentos, sais e
   terminações PT→EN (ex.: rituximabe→rituximab, tofacitinibe→tofacitinib).
3. Fallback opcional: match exato do nome normalizado em toda a `dim_atc`
   (nível 5), útil quando o ATC4 da fat está desatualizado (ex.: L01XC vs L01FA).

Saídas típicas:
- ``ATC_CODE_LEVEL_5``: código de 7 caracteres (ou NA)
- ``ATC_LEVEL_5``: ``{código}_{nome}`` (ou missing / ``None`` se não mapear)
- ``ATC_LEVEL_5_SCORE``: 0–100
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Hashable, Optional

import pandas as pd
from rapidfuzz import fuzz, process

# Sem match → missing (None / NaN no DataFrame), não "Outros".
ATC_LEVEL_5_DEFAULT = None

# Terminações frequentes PT → stem EN da ATC / WHO-Drug.
_PT_TO_EN_ENDINGS: tuple[tuple[str, str], ...] = (
    ("QUINUMABE", "KINUMAB"),
    ("ZUMABE", "ZUMAB"),
    ("MABE", "MAB"),
    ("CEPTE", "CEPT"),
    ("TINIBE", "TINIB"),
    ("CICLIBE", "CICLIB"),
    ("PARIBE", "PARIB"),
    ("NIBIE", "NIB"),
)

# Prefixo PT / biosimilar (não incluir SODIUM/POTASSIUM soltos — quebram
# "SODIUM CHLORIDE" / "POTASSIUM CHLORIDE").
_SALT_PREFIX = re.compile(
    r"\b("
    r"BIOSIMILAR(\s+\d+)?|"
    r"CITRATO\s+DE|CLORETO\s+DE|SULFATO\s+DE|CLORIDRATO\s+DE|SUCCINATO\s+DE|"
    r"ACIDO\s+DE"
    r")\b",
    flags=re.IGNORECASE,
)
# Sal / ânion no final do nome EN (ex.: DICLOFENAC SODIUM → DICLOFENAC).
_TRAILING_SALT = re.compile(
    r"\s+("
    r"SODIUM|POTASSIUM|MAGNESIUM|CALCIUM|"
    r"CITRATE|ASPARTATE|HYDROCHLORIDE|SULFATE|SULPHATE|"
    r"FUMARATE|MALEATE|MESYLATE|SUCCINATE|ACETATE|"
    r"BESILATE|BESYLATE|PHOSPHATE|CARBONATE|SESQUIHYDRATE|TRIHYDRATE|MESILATE|MESYLATE"
    r")$",
    flags=re.IGNORECASE,
)
# Formas de sal em PT no meio/fim (ex.: CEFAZOLINA SODICA).
_PT_SALT_FORM = re.compile(
    r"\b(SODICA|SODICO|POTASSICA|POTASSICO|MAGNESIO|CALCICA|CALCICO)\b",
    flags=re.IGNORECASE,
)

# Frases PT / nomes comerciais / vacinas → texto alinhado à dim_atc (após upper/sem acento).
_PHRASE_SYNONYMS: tuple[tuple[str, str], ...] = (
    ("BUTILBROMETO DE ESCOPOLAMINA", "BUTYLSCOPOLAMINE"),
    ("BUTILBROMETO ESCOPOLAMINA", "BUTYLSCOPOLAMINE"),
    ("BROMETO DE N BUTIL ESCOPOLAMONIO", "BUTYLSCOPOLAMINE"),
    ("ACIDO ACETILSALICILICO", "ACETYLSALICYLIC ACID"),
    ("CLORETO DE SODIO", "SODIUM CHLORIDE"),
    ("CLORETO DE POTASSIO", "POTASSIUM CHLORIDE"),
    ("SULFATO DE MORFINA", "MORPHINE"),
    ("LOSARTANA POTASSICA", "LOSARTAN"),
    ("PIPERACILINA SODICA", "PIPERACILLIN"),
    ("TAZOBACTAM SODICO", "TAZOBACTAM"),
    ("PIPERACILINA", "PIPERACILLIN"),
    ("METAMIZOL DE MAGNESIO", "METAMIZOLE SODIUM"),
    ("FOLINATO DE CALCIO", "CALCIUM FOLINATE"),
    ("BESILATO DE ANLODIPINO", "AMLODIPINE"),
    ("IMUNOGLOBULINA HUMANA", "IMMUNOGLOBULINS NORMAL HUMAN FOR INTRAVASCULAR ADM"),
    ("IMMUNOGLOBULIN HUMAN NORMAL", "IMMUNOGLOBULINS NORMAL HUMAN FOR INTRAVASCULAR ADM"),
    ("FOSFATO DE DEXAMETASONA", "DEXAMETHASONE"),
    ("SIMETICONE", "SILICONES"),
    ("SIMETICONA", "SILICONES"),
    # Vacinas COVID (INN / descrições VigiMed → nomes ATC J07BN*)
    ("TOZINAMERAN", "COVID 19 RNA BASED VACCINE"),
    ("ELASOMERAN", "COVID 19 RNA BASED VACCINE"),
    ("COVID 19 VACCINE NRVV AD CHADOX1 NCOV 19", "COVID 19 VIRAL VECTOR NON REPLICATING"),
    ("COVID 19 VACCINE NRVV AD26 JNJ 78436735", "COVID 19 VIRAL VECTOR NON REPLICATING"),
    ("COVID 19 VACCINE INACT VERO CZ02", "COVID 19 INACTIVATED VIRUS"),
    ("COVID 19 VACCINE INACT VERO", "COVID 19 INACTIVATED VIRUS"),
    ("VACINA COVID 19 INATIVADA VERO CZ02", "COVID 19 INACTIVATED VIRUS"),
    ("VACINA COVID 19 INATIVADA VERO", "COVID 19 INACTIVATED VIRUS"),
    ("HYOSCINE BUTYLBROMIDE", "BUTYLSCOPOLAMINE"),
)

# Token PT / variante → forma canônica EN usada na dim_atc.
_TOKEN_CANONICAL: dict[str, str] = {
    "DIPIRONA": "METAMIZOLE",
    "METAMIZOL": "METAMIZOLE",
    "ESCOPOLAMINA": "SCOPOLAMINE",
    "CETOPROFENO": "KETOPROFEN",
    "DOCETAXOL": "DOCETAXEL",
    "FENTANILA": "FENTANYL",
    "MORFINA": "MORPHINE",
    "LOSARTANA": "LOSARTAN",
    "DIFENIDRAMINA": "DIPHENHYDRAMINE",
    "CICLOFOSFAMIDA": "CYCLOPHOSPHAMIDE",
    "VANCOMICINA": "VANCOMYCIN",
    "RIBOCICLIBE": "RIBOCICLIB",
    "ONDANSETRONA": "ONDANSETRON",
    "DEXAMETASONA": "DEXAMETHASONE",
    "PREDNISONA": "PREDNISONE",
    "HEPARINA": "HEPARIN",
    "ENOXAPARINA": "ENOXAPARIN",
    "TRAMADOL": "TRAMADOL",
    "GABAPENTINA": "GABAPENTIN",
    "CLONAZEPAM": "CLONAZEPAM",
    "MIDAZOLAM": "MIDAZOLAM",
    "PROPOFOL": "PROPOFOL",
    "CEFTRIAXONA": "CEFTRIAXONE",
    "CEFAZOLINA": "CEFAZOLIN",
    "AMOXICILINA": "AMOXICILLIN",
    "AZITROMICINA": "AZITHROMYCIN",
    "MEROPENEM": "MEROPENEM",
    "OMEPRAZOL": "OMEPRAZOLE",
    "PANTOPRAZOL": "PANTOPRAZOLE",
    "METFORMINA": "METFORMIN",
    "PARACETAMOL": "PARACETAMOL",
    "LEVOTIROXINA": "LEVOTHYROXINE",
    "SINVASTATINA": "SIMVASTATIN",
    "ANLODIPINO": "AMLODIPINE",
    "AMLODIPINO": "AMLODIPINE",
    "LENALIDOMIDA": "LENALIDOMIDE",
    "SIMETICONE": "DIMETICONE",
    "SIMETICONA": "DIMETICONE",
    "SEMAGLUTIDA": "SEMAGLUTIDE",
    "VARFARINA": "WARFARIN",
    "MESSALAZINA": "MESALAZINE",
    "MESALAZINA": "MESALAZINE",
    "FENITOINA": "PHENYTOIN",
    "OCITOCINA": "OXYTOCIN",
}

_TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    "DIPIRONA": ("METAMIZOLE", "METAMIZOLE SODIUM"),
    "METAMIZOLE": ("METAMIZOLE SODIUM",),
    "LEVOTHYROXINE": ("LEVOTHYROXINE SODIUM",),
    "AMLODIPINE": ("AMLODIPINE",),
    "CALCIUM FOLINATE": ("CALCIUM FOLINATE",),
    "IMMUNOGLOBULINS NORMAL HUMAN FOR INTRAVASCULAR ADM": (
        "IMMUNOGLOBULINS NORMAL HUMAN FOR INTRAVASCULAR ADM",
        "IMMUNOGLOBULINS NORMAL HUMAN FOR EXTRAVASCULAR ADM",
    ),
    "LENALIDOMIDE": ("LENALIDOMIDE",),
    "DIMETICONE": ("DIMETICONE",),
    "BUTYLSCOPOLAMINE": ("SCOPOLAMINE", "BUTYLSCOPOLAMINE AND ANALGESICS"),
    "ESCOPOLAMINA": ("SCOPOLAMINE", "BUTYLSCOPOLAMINE"),
    "SCOPOLAMINE": ("BUTYLSCOPOLAMINE",),
    "COVID 19 RNA BASED VACCINE": ("COVID 19 RNA BASED VACCINE",),
    "COVID 19 VIRAL VECTOR NON REPLICATING": ("COVID 19 VIRAL VECTOR NON REPLICATING",),
    "COVID 19 INACTIVATED VIRUS": ("COVID 19 INACTIVATED VIRUS",),
    "INSULIN NOS": ("INSULIN HUMAN", "INSULIN"),
    "INSULIN": ("INSULIN HUMAN",),
    "ACETYLSALICYLIC ACID": ("ACETYLSALICYLIC ACID",),
    "PIPERACILLIN": ("PIPERACILLIN AND BETA LACTAMASE INHIBITOR", "PIPERACILLIN"),
    "KETOPROFEN": ("KETOPROFEN",),
    "DOCETAXEL": ("DOCETAXEL",),
    "RIBOCICLIB": ("RIBOCICLIB",),
}


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_drug_name(value: Any) -> str:
    """Normaliza nome de substância para comparação PT/EN com a `dim_atc`."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = _strip_accents(str(value)).upper()
    text = re.sub(r"_X000[DA9]_", " ", text)
    text = text.replace("|", " ")
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Frases longas antes de remover sais (ex.: CLORETO DE SODIO → SODIUM CHLORIDE).
    for src, dst in sorted(_PHRASE_SYNONYMS, key=lambda x: len(x[0]), reverse=True):
        if src in text:
            text = text.replace(src, dst)

    text = _SALT_PREFIX.sub(" ", text)
    text = _PT_SALT_FORM.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Não cortar sais quando o nome inteiro é o eletrólito (B05XA*).
    if text not in {"SODIUM CHLORIDE", "POTASSIUM CHLORIDE"}:
        # Pode haver vários sufixos (ex.: PANTOPRAZOLE SODIUM SESQUIHYDRATE).
        for _ in range(4):
            nxt = _TRAILING_SALT.sub("", text)
            nxt = re.sub(r"\s+", " ", nxt).strip()
            if nxt == text:
                break
            text = nxt

    tokens: list[str] = []
    for token in text.split():
        normalized = token
        for pt_end, en_end in _PT_TO_EN_ENDINGS:
            if normalized.endswith(pt_end):
                normalized = normalized[: -len(pt_end)] + en_end
                break
        normalized = _TOKEN_CANONICAL.get(normalized, normalized)
        tokens.append(normalized)
    return " ".join(tokens)


def _split_principio_tokens(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    raw = str(value)
    parts = re.split(r"\||_X000D_", raw, flags=re.IGNORECASE)
    tokens: list[str] = []
    for part in parts:
        base = normalize_drug_name(part)
        if not base:
            continue
        tokens.append(base)
        # Aliases extras para match na dim_atc (ex.: dipirona→metamizole sodium)
        for tok in base.split():
            for alias in _TOKEN_ALIASES.get(tok, ()):
                if alias not in tokens:
                    tokens.append(alias)
        for alias in _TOKEN_ALIASES.get(base, ()):
            if alias not in tokens:
                tokens.append(alias)
    if tokens:
        return tokens
    whole = normalize_drug_name(raw)
    return [whole] if whole else []


def _build_level5_catalog(dim_atc: pd.DataFrame) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    required = {"ATC_LEVEL", "ATC_CODE_LEVEL_4", "ATC_CODE_LEVEL_5", "ATC_NAME_LEVEL"}
    missing = required - set(dim_atc.columns)
    if missing:
        raise KeyError(f"dim_atc sem colunas obrigatórias: {sorted(missing)}")

    level5 = dim_atc.loc[dim_atc["ATC_LEVEL"].astype("Int64") == 5].copy()
    name_col = (
        "ATC_CODE_LEVEL_5_LEVEL_NAME"
        if "ATC_CODE_LEVEL_5_LEVEL_NAME" in level5.columns
        else "ATC_NAME_LEVEL"
    )

    by_level4: dict[str, list[dict]] = defaultdict(list)
    by_name: dict[str, list[dict]] = defaultdict(list)

    for row in level5.itertuples(index=False):
        code4 = getattr(row, "ATC_CODE_LEVEL_4")
        code5 = getattr(row, "ATC_CODE_LEVEL_5")
        name = getattr(row, "ATC_NAME_LEVEL")
        name_alt = getattr(row, name_col) if name_col != "ATC_NAME_LEVEL" else name
        if pd.isna(code5) or pd.isna(name):
            continue
        code4_s = "" if pd.isna(code4) else str(code4).strip()
        entry = {
            "code4": code4_s,
            "code5": str(code5).strip(),
            "name": str(name).strip(),
            "name_norm": normalize_drug_name(name),
            "name_alt_norm": normalize_drug_name(name_alt),
        }
        if not entry["name_norm"]:
            continue
        if code4_s:
            by_level4[code4_s].append(entry)
        by_name[entry["name_norm"]].append(entry)
        if entry["name_alt_norm"] and entry["name_alt_norm"] != entry["name_norm"]:
            by_name[entry["name_alt_norm"]].append(entry)

    return by_level4, by_name


def _score_token_against_name(token: str, name_norm: str) -> float:
    if not token or not name_norm:
        return 0.0
    if token == name_norm:
        return 100.0
    if name_norm in token or token in name_norm:
        # Contenção tipicamente cobre "ADALIMUMAB ADAZ", "INFLIXIMAB BIOSIMILAR 1".
        shorter = min(len(token), len(name_norm))
        longer = max(len(token), len(name_norm), 1)
        return 95.0 * (shorter / longer) + 5.0
    return float(fuzz.token_set_ratio(token, name_norm))


def _pick_best_in_candidates(
    tokens: list[str],
    candidates: list[dict],
    *,
    fuzzy_threshold: float,
) -> Optional[tuple[dict, float, str]]:
    best: Optional[tuple[dict, float, str]] = None
    for token in tokens:
        for entry in candidates:
            for key in ("name_norm", "name_alt_norm"):
                score = _score_token_against_name(token, entry.get(key) or "")
                if score < fuzzy_threshold:
                    continue
                if best is None or score > best[1]:
                    best = (entry, score, token)
    return best


def _format_atc_level_5(code5: str, display_name: str) -> str:
    nice = " ".join(str(display_name).strip().split()).title()
    return f"{code5}_{nice}" if nice else code5


def match_atc_level_5_row(
    atc_code_level_4: Any,
    principio_ativo: Any,
    *,
    by_level4: dict[str, list[dict]],
    by_name: dict[str, list[dict]],
    fuzzy_threshold: float = 90.0,
    allow_global_name_fallback: bool = True,
    default: Optional[str] = ATC_LEVEL_5_DEFAULT,
) -> tuple[Optional[str], Optional[str], float]:
    """Retorna ``(ATC_CODE_LEVEL_5, ATC_LEVEL_5, score)`` para uma linha."""
    tokens = _split_principio_tokens(principio_ativo)
    if not tokens:
        return None, default, 0.0

    code4 = "" if atc_code_level_4 is None or pd.isna(atc_code_level_4) else str(atc_code_level_4).strip()
    candidates = by_level4.get(code4, []) if code4 else []

    picked = _pick_best_in_candidates(tokens, candidates, fuzzy_threshold=fuzzy_threshold)
    if picked is not None:
        entry, score, token = picked
        display = token.title() if token else entry["name"]
        return entry["code5"], _format_atc_level_5(entry["code5"], display), float(score)

    if allow_global_name_fallback:
        global_candidates: list[dict] = []
        for token in tokens:
            global_candidates.extend(by_name.get(token, []))
        # Preferir mesmo ATC4 quando o nome existir em vários ramos.
        if code4:
            same = [e for e in global_candidates if e["code4"] == code4]
            if same:
                global_candidates = same
        # Deduplicar por code5
        uniq: dict[str, dict] = {e["code5"]: e for e in global_candidates}
        picked = _pick_best_in_candidates(
            tokens, list(uniq.values()), fuzzy_threshold=max(fuzzy_threshold, 99.0)
        )
        # Para fallback global exigimos igualdade/contenção forte (≥99 após norm).
        if picked is not None:
            entry, score, token = picked
            display = token.title() if token else entry["name"]
            return entry["code5"], _format_atc_level_5(entry["code5"], display), float(score)

    return None, default, 0.0


def add_atc_level_5(
    df: pd.DataFrame,
    dim_atc: pd.DataFrame,
    *,
    atc_col: str = "ATC_CODE_LEVEL_4",
    principio_col: str = "PRINCIPIOS_ATIVOS_WHODRUG",
    out_col: str = "ATC_LEVEL_5",
    code_out_col: str = "ATC_CODE_LEVEL_5",
    score_out_col: str = "ATC_LEVEL_5_SCORE",
    fuzzy_threshold: float = 90.0,
    allow_global_name_fallback: bool = True,
    default: Optional[str] = ATC_LEVEL_5_DEFAULT,
    inplace: bool = False,
) -> pd.DataFrame:
    """Adiciona ``ATC_CODE_LEVEL_5`` / ``ATC_LEVEL_5`` inferidos via `dim_atc`."""
    missing = {atc_col, principio_col} - set(df.columns)
    if missing:
        raise KeyError(f"Colunas obrigatórias ausentes na fat: {sorted(missing)}")

    target = df if inplace else df.copy()
    by_level4, by_name = _build_level5_catalog(dim_atc)

    # Cache por pares únicos — fat_medicamentos tem centenas de milhares de linhas.
    cache: dict[tuple[Hashable, Hashable], tuple[Optional[str], Optional[str], float]] = {}
    codes: list[Optional[str]] = []
    labels: list[Optional[str]] = []
    scores: list[float] = []

    atc_values = target[atc_col].tolist()
    principio_values = target[principio_col].tolist()

    for atc_value, principio_value in zip(atc_values, principio_values):
        key = (
            None if atc_value is None or (isinstance(atc_value, float) and pd.isna(atc_value)) else str(atc_value),
            None
            if principio_value is None or (isinstance(principio_value, float) and pd.isna(principio_value))
            else str(principio_value),
        )
        if key not in cache:
            cache[key] = match_atc_level_5_row(
                key[0],
                key[1],
                by_level4=by_level4,
                by_name=by_name,
                fuzzy_threshold=fuzzy_threshold,
                allow_global_name_fallback=allow_global_name_fallback,
                default=default,
            )
        code5, label, score = cache[key]
        codes.append(code5)
        labels.append(label)
        scores.append(score)

    target[code_out_col] = pd.Series(codes, index=target.index, dtype="object")
    target[out_col] = pd.Series(labels, index=target.index, dtype="object")
    target[score_out_col] = pd.Series(scores, index=target.index, dtype="float64")
    return target


def summarize_atc_level_5_quality(
    df: pd.DataFrame,
    *,
    out_col: str = "ATC_LEVEL_5",
    score_out_col: str = "ATC_LEVEL_5_SCORE",
    default: Optional[str] = ATC_LEVEL_5_DEFAULT,
) -> dict:
    """Resumo de cobertura e scores de ``ATC_LEVEL_5`` (para QA no notebook)."""
    if out_col not in df.columns:
        raise KeyError(f"Coluna ausente: {out_col}")
    n = len(df)
    filled_mask = df[out_col].notna() & (df[out_col].astype(str) != str(default))
    n_filled = int(filled_mask.sum())
    n_missing = n - n_filled
    scores = df.loc[filled_mask, score_out_col].astype(float) if score_out_col in df.columns else pd.Series(dtype=float)
    summary = {
        "n_rows": n,
        "n_filled": n_filled,
        "n_missing": n_missing,
        "pct_filled": round(100.0 * n_filled / n, 2) if n else 0.0,
        "pct_missing": round(100.0 * n_missing / n, 2) if n else 0.0,
    }
    if len(scores):
        summary.update(
            {
                "score_mean": round(float(scores.mean()), 2),
                "score_p10": round(float(scores.quantile(0.10)), 2),
                "score_p50": round(float(scores.quantile(0.50)), 2),
                "score_p90": round(float(scores.quantile(0.90)), 2),
                "score_p99": round(float(scores.quantile(0.99)), 2),
                "score_min": round(float(scores.min()), 2),
                "pct_score_100": round(100.0 * (scores >= 99.999).mean(), 2),
            }
        )
    return summary


# Compat: chamadas antigas sem dim_atc não são mais válidas.
def map_atc_level_5(*_args, **_kwargs):
    raise TypeError(
        "map_atc_level_5 legado (regras fixas) foi substituído. "
        "Use add_atc_level_5(df, dim_atc) / match_atc_level_5_row."
    )

