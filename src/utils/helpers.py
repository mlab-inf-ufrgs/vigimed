# Definindo o caminho do projeto
from pathlib import Path

def get_project_root(markers=(".git", "README.md", "pyproject.toml")):
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
        if any((parent / marker).exists() for marker in markers):
            return parent

    raise FileNotFoundError("Could not locate project root. Ensure a marker file like .git or README.md exists.")


# Dataframe display settings
import pandas as pd

# Mostrar todas as colunas
pd.set_option('display.max_columns', None)

# Mostrar todas as linhas
pd.set_option('display.max_rows', None)

# Ajustar largura de colunas para evitar corte
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 0)  # permite que o notebook ajuste automaticamente
