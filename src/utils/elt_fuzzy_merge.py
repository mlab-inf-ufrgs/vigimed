from typing import Optional, Tuple

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
    canonical_df: pd.DataFrame,
    bronze: pd.DataFrame,
    *,
    on: str = "DETENTOR_REGISTRO",
    threshold: int = 90,
    suffix: str = "_MATCH",
    dedupe_on: bool = False,
) -> pd.DataFrame:
    """
    Faz um merge aproximado entre canonical_df e bronze usando similaridade textual.
    Quando canonical_df[on] ~= bronze[on], traz as colunas de bronze para canonical_df.

    Retorna um DataFrame com as colunas originais de bronze, seguido
    das colunas de canonical_df com sufixo (default '_MATCH'), o campo `<coluna>_FUZZY`
    com o texto original encontrado no lado canônico e a coluna `<coluna>_SCORE`
    com o score (0-100) da correspondência.
    """

    matched_col_name = f"{on}_FUZZY"
    score_col = f"{on}_SCORE"
    normalized_col = "__normalized_on"

    left = bronze.copy().reset_index(drop=True)
    left["__original_order"] = np.arange(len(left))
    right = canonical_df.copy()

    left[normalized_col] = _normalize_text(left[on])
    right[normalized_col] = _normalize_text(right[on])

    matches = left[normalized_col].apply(
        lambda text: _fuzzy_match_index(
            text,
            right[normalized_col],
            threshold=threshold,
        )
    )

    left["__match_idx"] = matches.apply(lambda x: x[0])
    left[score_col] = matches.apply(lambda x: x[1])

    right_with_suffix = right.add_suffix(suffix)
    norm_suffix_col = f"{normalized_col}{suffix}"
    if norm_suffix_col in right_with_suffix.columns:
        right_with_suffix = right_with_suffix.drop(columns=[norm_suffix_col])

    original_right_on = f"{on}{suffix}"
    if original_right_on in right_with_suffix.columns:
        right_with_suffix = right_with_suffix.rename(
            columns={original_right_on: matched_col_name}
        )

    merged = left.merge(
        right_with_suffix,
        how="left",
        left_on="__match_idx",
        right_index=True,
    )

    merged = merged.drop(columns=[normalized_col, "__match_idx"], errors="ignore")

    object_cols = merged.select_dtypes(include="object").columns
    merged[object_cols] = merged[object_cols].apply(lambda col: col.str.upper())

    if dedupe_on and on in merged.columns:
        merged = (
            merged.sort_values(
                by=[score_col, "__original_order"],
                ascending=[False, True],
            )
            .drop_duplicates(subset=[on], keep="first")
            .sort_values("__original_order")
        )

    return merged.drop(columns="__original_order")

