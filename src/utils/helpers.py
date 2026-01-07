# Definindo o caminho do projeto
from pathlib import Path

def get_project_root(markers=(".git", "config", "pyproject.toml")):
    """
    Returns the root path of the project by looking for a marker file/directory.

    Args:
        markers (tuple): List of filenames or folder names that identify the root.

    Returns:
        Path: A pathlib.Path object pointing to the root directory.

    Raises:
        FileNotFoundError: If no project root is found in any parent.
    """
    current = Path().resolve()

    for parent in [current] + list(current.parents):
        # Verifica se o diretório tem 'config' E 'src' (estrutura do projeto)
        has_config = (parent / "config").exists()
        has_src = (parent / "src").exists()
        if has_config and has_src:
            return parent
        # Fallback para .git ou pyproject.toml
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent

    raise FileNotFoundError("Could not locate project root. Ensure the project has config/ and src/ directories, or .git folder.")


# Dataframe display settings
import pandas as pd

# Mostrar todas as colunas
pd.set_option('display.max_columns', None)

# Mostrar todas as linhas
pd.set_option('display.max_rows', None)

# Ajustar largura de colunas para evitar corte
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 0)  # permite que o notebook ajuste automaticamente

import pandas as pd

def add_key_value_columns(
    df: pd.DataFrame,
    base_col: str,
    normalized_col: str,
    prefix: str = None,
) -> pd.DataFrame:
    """
    Cria colunas `<prefix>_CHAVE` e `<prefix>_VALOR` a partir de um campo
    normalizado (ex.: DETENTOR_REGISTRO_PADRONIZADO).

    - `_VALOR` recebe o próprio texto normalizado.
    - `_CHAVE` é um código inteiro (1..N) por valor distinto, preservando a
      ordem em que aparece.
    """
    prefix = prefix or base_col

    valor_col = f"{prefix}_VALOR"
    chave_col = f"{prefix}_CHAVE"

    df = df.copy()
    df[valor_col] = df[normalized_col]

    keys, _ = pd.factorize(df[normalized_col], sort=True)
    df[chave_col] = pd.Series(keys + 1, index=df.index).astype("Int64")  # começa em 1
    return df