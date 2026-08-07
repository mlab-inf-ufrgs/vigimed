"""Versionamento por snapshot de tabelas (hist) com VERSION_ID + CURRENT_FLAG."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

import pandas as pd


def _as_date_str(value: Optional[Union[str, datetime, date]] = None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def stamp_snapshot_version(
    df: pd.DataFrame,
    version_id: Union[int, str],
    *,
    current: bool = True,
    version_col: str = "VERSION_ID",
    current_flag_col: str = "CURRENT_FLAG",
    date_update_col: str = "DATE_UPDATE",
    date_update: Optional[Union[str, datetime, date]] = None,
) -> pd.DataFrame:
    """Copia o DataFrame e carimba VERSION_ID / CURRENT_FLAG / DATE_UPDATE."""
    out = df.copy()
    out[version_col] = version_id
    out[current_flag_col] = bool(current)
    out[date_update_col] = _as_date_str(date_update)
    return out


def publish_snapshot_version(
    df_new: pd.DataFrame,
    hist_path: Union[str, Path],
    version_id: Union[int, str],
    *,
    version_col: str = "VERSION_ID",
    current_flag_col: str = "CURRENT_FLAG",
    date_update_col: str = "DATE_UPDATE",
    date_update: Optional[Union[str, datetime, date]] = None,
    archive_unversioned_as: Optional[Union[int, str]] = None,
) -> pd.DataFrame:
    """Publica ``df_new`` como versão atual e concatena ao histórico Parquet.

    - Se o hist existir **sem** ``VERSION_ID``:
      - com ``archive_unversioned_as`` → arquiva o arquivo atual com esse id e
        ``CURRENT_FLAG=False``, depois anexa a nova versão;
      - sem ``archive_unversioned_as`` → **substitui** o arquivo pela nova versão
        carimbada (evita duplicar a carga recém-gerada sem versionamento).
    - Se já houver versionamento, fecha ``CURRENT_FLAG=True`` e anexa a nova
      ``version_id`` (republicar o mesmo id substitui essa versão).
    """
    hist_path = Path(hist_path)
    stamped = stamp_snapshot_version(
        df_new,
        version_id,
        current=True,
        version_col=version_col,
        current_flag_col=current_flag_col,
        date_update_col=date_update_col,
        date_update=date_update,
    )

    hist_path.parent.mkdir(parents=True, exist_ok=True)

    if not hist_path.exists():
        stamped.to_parquet(hist_path, index=False)
        return stamped

    hist_old = pd.read_parquet(hist_path)

    if version_col not in hist_old.columns:
        if archive_unversioned_as is None:
            stamped.to_parquet(hist_path, index=False)
            return stamped
        hist_old = stamp_snapshot_version(
            hist_old,
            archive_unversioned_as,
            current=False,
            version_col=version_col,
            current_flag_col=current_flag_col,
            date_update_col=date_update_col,
            date_update=date_update,
        )
    else:
        hist_old = hist_old.copy()
        if current_flag_col in hist_old.columns:
            hist_old.loc[hist_old[current_flag_col].astype(bool), current_flag_col] = False
        else:
            hist_old[current_flag_col] = False
        hist_old = hist_old.loc[hist_old[version_col] != version_id].copy()

    hist = pd.concat([hist_old, stamped], ignore_index=True)
    hist.to_parquet(hist_path, index=False)
    return hist


def load_current_version(
    hist_path: Union[str, Path],
    *,
    current_flag_col: str = "CURRENT_FLAG",
    version_col: str = "VERSION_ID",
) -> pd.DataFrame:
    """Lê o hist e devolve apenas a versão atual (CURRENT_FLAG)."""
    hist = pd.read_parquet(hist_path)
    if current_flag_col in hist.columns:
        cur = hist.loc[hist[current_flag_col].astype(bool)].copy()
        if len(cur):
            return cur.reset_index(drop=True)
    if version_col in hist.columns:
        latest = hist[version_col].max()
        return hist.loc[hist[version_col] == latest].copy().reset_index(drop=True)
    return hist.copy()
