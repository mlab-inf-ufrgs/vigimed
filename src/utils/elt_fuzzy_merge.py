from typing import Any, Optional, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process


def _normalize_text(series: pd.Series) -> pd.Series:
    cleaned = (
        series.fillna("")
        .astype(str)
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
        .str.upper()
    )

    replacement_patterns = [
        r"_X000D_",
        r"_X000A_",
        r"_X0009_",
        r"\|",
    ]

    for pattern in replacement_patterns:
        cleaned = cleaned.str.replace(pattern, " ", case=False, regex=True)

    cleaned = cleaned.str.replace(r"\s+", " ", regex=True).str.strip()
    return cleaned


def _fuzzy_match_index(
    text: str,
    choices: pd.Series,
    *,
    threshold: int,
    scorer=fuzz.WRatio,
    min_length_ratio: float = 0.5,
) -> Tuple[Optional[int], float]:
    if not text:
        return (None, 0.0)

    match = process.extractOne(text, choices, scorer=scorer)
    if not match:
        return (None, 0.0)

    matched_text = match[0] if match[0] is not None else ""
    choice_index = match[2]
    score = float(match[1])

    if score < threshold:
        return (None, score)

    candidate_text = str(matched_text)
    max_len = max(len(text), len(candidate_text), 1)
    length_ratio = min(len(text), len(candidate_text)) / max_len

    if length_ratio < min_length_ratio:
        return (None, score)

    return (choice_index, score)


def fuzzy_merge(
    dim_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    *,
    dim_id_col: str = "ID",
    dim_text_col: str = "COL_A_LIMPA",
    fact_text_col: str = "COL_A_SUJA",
    threshold: int = 90,
    scorer=fuzz.WRatio,
    suffix: str = "_MATCH",
    dedupe_on: bool = False,
) -> pd.DataFrame:
    """
    Similar ao hungarian_text_link, mas usa match independente (não 1:1).
    Para cada linha da fato, traz o `dim_id_col` cuja `dim_text_col`
    é mais similar a `fact_text_col`.

    Retorna o DataFrame de fato com colunas:
    - `<dim_id_col><suffix>` (ID da dimensão, dtype Int64)
    - `<fact_text_col><suffix>` (texto da dimensão correspondente)
    - `<fact_text_col>_SCORE` (0-100)
    """

    id_match_col = f"{dim_id_col}{suffix}"
    text_match_col = f"{fact_text_col}{suffix}"
    score_col = f"{fact_text_col}_SCORE"

    fact_work = fact_df.copy().reset_index(drop=True)
    fact_work["__original_order"] = np.arange(len(fact_work))
    dim_work = dim_df.copy().reset_index(drop=True)

    fact_work["__normalized_text"] = _normalize_text(fact_work[fact_text_col])
    dim_work["__normalized_text"] = _normalize_text(dim_work[dim_text_col])

    matches = fact_work["__normalized_text"].apply(
        lambda text: _fuzzy_match_index(
            text,
            dim_work["__normalized_text"],
            threshold=threshold,
            scorer=scorer,
        )
    )

    fact_work["__match_idx"] = matches.apply(lambda x: x[0]).astype("object")
    fact_work[score_col] = matches.apply(lambda x: x[1])

    def _safe_lookup(idx, col):
        if idx is None or pd.isna(idx):
            return None
        return dim_work.loc[idx, col]

    fact_work[id_match_col] = fact_work["__match_idx"].apply(
        lambda idx: _safe_lookup(idx, dim_id_col)
    )
    fact_work[text_match_col] = fact_work["__match_idx"].apply(
        lambda idx: _safe_lookup(idx, dim_text_col)
    )

    fact_work[id_match_col] = (
        pd.to_numeric(fact_work[id_match_col], errors="coerce").astype("Int64")
    )

    fact_work = fact_work.drop(columns=["__normalized_text", "__match_idx"])

    object_cols = fact_work.select_dtypes(include="object").columns
    fact_work[object_cols] = fact_work[object_cols].apply(lambda col: col.str.upper())

    if dedupe_on and fact_text_col in fact_work.columns:
        fact_work = (
            fact_work.sort_values(
                by=[score_col, "__original_order"],
                ascending=[False, True],
            )
            .drop_duplicates(subset=[fact_text_col], keep="first")
            .sort_values("__original_order")
        )

    return fact_work.drop(columns="__original_order")


def hungarian_text_link(
    dim_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    *,
    dim_id_col: str = "ID",
    dim_text_col: str = "COL_A_LIMPA",
    fact_text_col: str = "COL_A_SUJA",
    threshold: int = 85,
    scorer=fuzz.WRatio,
) -> pd.DataFrame:
    """
    Usa o algoritmo Húngaro (atribuição ótima) para ligar fato→dimensão
    maximizando similaridade textual entre `dim_text_col` e `fact_text_col`.

    Retorna o DataFrame de fato com três novas colunas:
    - `<dim_id_col>_MATCH`: id da dimensão escolhido (ou None se não bateu).
    - `<fact_text_col>_MATCH`: texto da dimensão utilizado.
    - `<fact_text_col>_SCORE`: score de similaridade (0-100).

    Observação: o algoritmo gera correspondência 1:1 (cada linha da dimensão
    pode ser usada no máximo uma vez). Se `fact_df` tiver mais linhas que
    `dim_df`, as linhas excedentes podem ficar sem correspondência.
    """

    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError as exc:  # pragma: no cover - dependência opcional
        raise ImportError(
            "Para usar hungarian_text_link instale scipy (pip install scipy)."
        ) from exc

    dim_work = dim_df.copy().reset_index(drop=True)
    fact_work = fact_df.copy().reset_index(drop=True)

    dim_work["__normalized_text"] = _normalize_text(dim_work[dim_text_col])
    fact_work["__normalized_text"] = _normalize_text(fact_work[fact_text_col])

    n_fact = len(fact_work)
    n_dim = len(dim_work)
    if n_fact == 0 or n_dim == 0:
        return fact_df.assign(
            **{
                f"{dim_id_col}_MATCH": None,
                f"{fact_text_col}_MATCH": None,
                f"{fact_text_col}_SCORE": np.nan,
            }
        )

    scores = np.zeros((n_fact, n_dim), dtype=float)
    for i, fact_text in enumerate[Any](fact_work["__normalized_text"]):
        if not fact_text:
            continue
        for j, dim_text in enumerate(dim_work["__normalized_text"]):
            if not dim_text:
                continue
            scores[i, j] = float(scorer(fact_text, dim_text))

    cost_matrix = 100.0 - scores
    row_idx, col_idx = linear_sum_assignment(cost_matrix)

    matched_ids = pd.Series([None] * n_fact, dtype=object)
    matched_texts = pd.Series([None] * n_fact, dtype=object)
    matched_scores = pd.Series([np.nan] * n_fact, dtype=float)

    for r, c in zip(row_idx, col_idx):
        score = scores[r, c]
        if score < threshold:
            continue
        matched_ids.iloc[r] = dim_work.loc[c, dim_id_col]
        matched_texts.iloc[r] = dim_work.loc[c, dim_text_col]
        matched_scores.iloc[r] = score

    fact_work = fact_work.drop(columns="__normalized_text")
    dim_work = dim_work.drop(columns="__normalized_text")

    fact_work[f"{dim_id_col}_MATCH"] = matched_ids
    fact_work[f"{fact_text_col}_MATCH"] = matched_texts
    fact_work[f"{fact_text_col}_SCORE"] = matched_scores

    return fact_work
