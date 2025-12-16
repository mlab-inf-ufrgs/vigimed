import re

import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz

def build_atc_lookup(bronze_atc: pd.DataFrame):
    catalog = (
        bronze_atc[["CODIGO_ATC_LEVEL", "NIVEL_NOME_ATC"]]
        .dropna(subset=["CODIGO_ATC_LEVEL", "NIVEL_NOME_ATC"])
        .drop_duplicates()
        .reset_index(drop=True)
    )
    catalog["NIVEL_NOME_ATC_NORM"] = normalize_text(catalog["NIVEL_NOME_ATC"])
    catalog["CODIGO_ATC_LEVEL_NORM"] = normalize_text(
        catalog["CODIGO_ATC_LEVEL"].astype(str)
    )
    return catalog

def guess_atc_level(
    principios_text: str,
    codigo_text: str,
    choices,
    *,
    threshold=80,
    peso_principios=0.35,
    peso_codigo=0.65,
):
    candidatos = set()

    if principios_text:
        matches = process.extract(
            principios_text,
            choices["NIVEL_NOME_ATC_NORM"],
            scorer=fuzz.token_set_ratio,
            limit=10,
        )
        candidatos.update(match[2] for match in matches if match is not None)

    if codigo_text:
        matches = process.extract(
            codigo_text,
            choices["CODIGO_ATC_LEVEL_NORM"],
            scorer=fuzz.ratio,
            limit=10,
        )
        candidatos.update(match[2] for match in matches if match is not None)

    if not candidatos:
        return ("desconhecido", 0)

    melhor_codigo = "desconhecido"
    melhor_score = 0.0

    for idx in candidatos:
        linha = choices.iloc[idx]
        score_principios = (
            fuzz.token_set_ratio(principios_text, linha["NIVEL_NOME_ATC_NORM"])
            if principios_text
            else 0.0
        )
        score_codigo = (
            fuzz.ratio(codigo_text, linha["CODIGO_ATC_LEVEL_NORM"])
            if codigo_text
            else 0.0
        )
        score_final = peso_principios * score_principios + peso_codigo * score_codigo

        if score_final > melhor_score:
            melhor_score = score_final
            melhor_codigo = linha["CODIGO_ATC_LEVEL"]

    if melhor_score < threshold:
        return ("desconhecido", melhor_score)

    return (melhor_codigo, melhor_score)

def normalize_text(series):
    return (
        series.fillna("")
        .astype(str)
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

STOP_WORDS = {"biosimilar"," abbs", " pvvr","Acetato de ","Fosfato sódico de ","Acetónido de ","Cloridrato de ","hydrochloride","Tartarato de ","Sulfato de ","monoidratado","monoidratada","monohydrate","succinate"}
STOP_REGEXES = [
    re.compile(r"\b\d+\b"),  # números isolados
    re.compile(r"_x000d_\|", re.IGNORECASE),  # artefatos comuns
]


def clean_principios_codigo(series):
    normalized = normalize_text(series)

    def _clean(text: str) -> str:
        if not text:
            return ""

        cleaned = text
        for pattern in STOP_REGEXES:
            cleaned = pattern.sub(" ", cleaned)

        for word in STOP_WORDS:
            cleaned = re.sub(rf"\b{re.escape(word)}\b", " ", cleaned)

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    return normalized.apply(_clean)

def normalize_atc(bronze: pd.DataFrame, bronze_atc: pd.DataFrame, threshold=80):
    catalog = build_atc_lookup(bronze_atc)

    principios = clean_principios_codigo(bronze["PRINCIPIOS_ATIVOS_WHODRUG_LIMPO"])
    codigos = clean_principios_codigo(bronze["CODIGO_ATC_5DIGITOS"])

    guesses = pd.Series(
        [
            guess_atc_level(
                principios.iloc[i], codigos.iloc[i], catalog, threshold=threshold
            )
            for i in range(len(bronze))
        ],
        index=bronze.index,
    )

    bronze["CODIGO_ATC_LEVEL"] = guesses.apply(lambda x: x[0])
    bronze["CODIGO_ATC_LEVEL_SCORE"] = guesses.apply(lambda x: x[1])
    bronze.loc[bronze["CODIGO_ATC_LEVEL"] == "desconhecido", "CODIGO_ATC_LEVEL_SCORE"] = np.nan

    return bronze

# uso
#bronze = normalize_atc(bronze, bronze_atc, threshold=82)