# Start here

Guia para configurar o ambiente e começar a trabalhar no repositório VigiMed.

Voltar ao [`README.md`](../README.md) · Dicionário: [`data_dictionary.md`](data_dictionary.md) · ERD: [`erd.md`](erd.md)

## Setup

Requisitos: Python 3.9+ e `pip`.

### 1. Clone e ambiente virtual

```bash
git clone https://github.com/mlab-inf-ufrgs/vigimed.git
cd vigimed

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Instalar dependências

As libs do projeto estão em [`src/requirements.txt`](../src/requirements.txt) (pandas, DuckDB, Jupyter, visualização, etc.):

```bash
pip install -r src/requirements.txt
```

Alternativa via notebook: abra [`src/libs.ipynb`](../src/libs.ipynb) e execute a célula

```python
%pip install -r requirements.txt
```

(o notebook assume o working directory em `src/`).

### 3. Verificar a instalação

No terminal, com o `.venv` ativado:

```bash
python - <<'PY'
import pandas as pd
import pyarrow
import duckdb
import rapidfuzz
import scipy
import matplotlib
import seaborn
import plotly

print("OK — dependências principais importadas com sucesso")
print(f"  pandas {pd.__version__}")
print(f"  duckdb {duckdb.__version__}")
PY
```

Se aparecer `OK — dependências principais importadas com sucesso`, o ambiente está pronto.

Para usar os notebooks no Jupyter/VS Code, registre o kernel do venv:

```bash
python -m ipykernel install --user --name=vigimed --display-name="Python (vigimed)"
```

## Estrutura do repositório

```bash
vigimed/
├── config/                 # Bootstrap (sys.path / project root)
├── data/                   # Camadas Bronze → Silver → Gold
│   ├── 01_bronze/
│   ├── 02_silver/
│   └── 03_gold/
├── docs/                   # Documentação (este guia, dicionário, ERD)
├── eda/                    # Análise de desproporcionalidade e materiais auxiliares
├── src/
│   ├── analytical/         # Build do DF analítico e métricas (stubs)
│   ├── etl/                # Notebooks ELT/ETL (medicamentos, notificações, reações)
│   ├── utils/              # Funções auxiliares de normalização e merge
│   ├── libs.ipynb          # Instalação das libs via notebook
│   └── requirements.txt    # Dependências Python
├── tests/                  # EDA exploratória, dashboard e validações silver/gold
│   ├── eda_*.ipynb / analytics.ipynb
│   ├── vigimed_dash.pbix
│   ├── validacao_medicamentos/
│   ├── validacao_notificacao/
│   └── validacao_reacoes/
```

## Por onde começar

1. **Só consumir a gold publicada** — baixe o dataset no [Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DRWDMU) (versão **V2**) e use o [`data_dictionary.md`](data_dictionary.md) / [`erd.md`](erd.md).
2. **Rodar / estender o ETL** — notebooks em [`src/etl/`](../src/etl/) (por domínio: `medicamentos/`, `notificacoes/`, `reacoes/`). Use `%run` do [`config/bootstrap.py`](../config/bootstrap.py) para resolver o `project_root` e imports de `utils`.
3. **Análise de desproporcionalidade** — stubs em [`src/analytical/`](../src/analytical/) e notebooks em [`eda/disproportionality_analysis/`](../eda/disproportionality_analysis/).
4. **Explorar / validar** — notebooks de EDA e validações em [`tests/`](../tests/) (`eda_*`, `analytics.ipynb`, `validacao_*`).

## Pipeline (resumo)

Fontes (Anvisa CSV + ATC + MedDRA) → **bronze** → **silver** (`hist_*`) → **gold** (dims + facts) → `fat_analytical` → métricas (ROR, PRR, IC, EBGM).

O diagrama Mermaid completo está no [`README.md`](../README.md#pipeline-elt).
