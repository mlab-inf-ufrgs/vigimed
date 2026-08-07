# Start Here / Comece por aqui

## English

Guide to setting up the development environment and getting started with the VigiMed repository.

**Navigation:** Back to [`README.md`](../README.md) · Data Dictionary: [`data_dictionary.md`](data_dictionary.md) · ERD: [`erd.md`](erd.md)

---

## Setup

Requirements: Python 3.9+ and `pip`.

### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/mlab-inf-ufrgs/vigimed.git
cd vigimed

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

Project dependencies are listed in [`src/requirements.txt`](../src/requirements.txt) (pandas, DuckDB, Jupyter, visualization libraries, etc.):

```bash
pip install -r src/requirements.txt
```

Alternatively, open [`src/libs.ipynb`](../src/libs.ipynb) and run:

```python
%pip install -r requirements.txt
```

(The notebook assumes `src/` as the working directory.)

### 3. Verify the installation

With the virtual environment activated, run:

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

print("OK — core dependencies imported successfully")
print(f"  pandas {pd.__version__}")
print(f"  duckdb {duckdb.__version__}")
PY
```

If the message `OK — core dependencies imported successfully` appears, the environment is ready.

To use the notebooks in Jupyter or VS Code, register the virtual environment as a kernel:

```bash
python -m ipykernel install --user --name=vigimed --display-name="Python (vigimed)"
```

---

## Repository Structure

```text
vigimed/
├── config/                 # Bootstrap (sys.path / project root)
├── data/                   # Bronze → Silver → Gold data layers
│   ├── 01_bronze/
│   ├── 02_silver/
│   └── 03_gold/
├── docs/                   # Documentation (this guide, data dictionary, ERD)
├── eda/                    # Disproportionality analysis and supporting materials
├── src/
│   ├── analytical/         # Analytical dataset generation and metrics (stubs)
│   ├── etl/                # ELT/ETL notebooks (medications, notifications, reactions)
│   ├── utils/              # Helper functions for normalization and merging
│   ├── libs.ipynb          # Install dependencies from a notebook
│   └── requirements.txt    # Python dependencies
├── tests/                  # Exploratory analyses, dashboard and Silver/Gold validation
│   ├── eda_*.ipynb / analytics.ipynb
│   ├── vigimed_dash.pbix
│   ├── validacao_medicamentos/
│   ├── validacao_notificacao/
│   └── validacao_reacoes/
```

---

## Getting Started

1. **Use the published Gold dataset** — Download the dataset from the Dataverse (**V2**) and consult the `data_dictionary.md` and `erd.md`.
2. **Run or extend the ETL pipeline** — ETL notebooks are available in [`src/etl/`](../src/etl/) (organized by domain: `medicamentos/`, `notificacoes/`, and `reacoes/`). Use `%run` with [`config/bootstrap.py`](../config/bootstrap.py) to configure the `project_root` and import utilities.
3. **Disproportionality analysis** — Starter modules are available in [`src/analytical/`](../src/analytical/) and notebooks in [`eda/disproportionality_analysis/`](../eda/disproportionality_analysis/).
4. **Explore and validate** — EDA notebooks and validation notebooks are available in [`tests/`](../tests/) (`eda_*`, `analytics.ipynb`, and `validacao_*`).

---

## Pipeline Overview

Data sources (ANVISA CSV + ATC + MedDRA) → **Bronze** → **Silver** (`hist_*`) → **Gold** (dimensions + fact tables) → `fat_analytical` → disproportionality metrics (ROR, PRR, IC, EBGM).

The complete Mermaid diagram is available in [`README.md`](../README.md#pipeline-elt).

---

# Português

Guia para configurar o ambiente e começar a trabalhar no repositório VigiMed.

**Navegação:** Voltar ao [`README.md`](../README.md) · Dicionário de Dados: [`data_dictionary.md`](data_dictionary.md) · ERD: [`erd.md`](erd.md)

---

## Configuração

Requisitos: Python 3.9+ e `pip`.

### 1. Clone o repositório e crie um ambiente virtual

```bash
git clone https://github.com/mlab-inf-ufrgs/vigimed.git
cd vigimed

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Instale as dependências

As dependências do projeto estão em [`src/requirements.txt`](../src/requirements.txt) (pandas, DuckDB, Jupyter, bibliotecas de visualização etc.):

```bash
pip install -r src/requirements.txt
```

Alternativamente, abra [`src/libs.ipynb`](../src/libs.ipynb) e execute:

```python
%pip install -r requirements.txt
```

(O notebook assume `src/` como diretório de trabalho.)

### 3. Verifique a instalação

Com o ambiente virtual ativado, execute:

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

Se aparecer a mensagem `OK — dependências principais importadas com sucesso`, o ambiente está pronto.

Para utilizar os notebooks no Jupyter ou VS Code, registre o ambiente virtual como um kernel:

```bash
python -m ipykernel install --user --name=vigimed --display-name="Python (vigimed)"
```

---

## Estrutura do Repositório

```text
vigimed/
├── config/                 # Bootstrap (sys.path / raiz do projeto)
├── data/                   # Camadas Bronze → Silver → Gold
│   ├── 01_bronze/
│   ├── 02_silver/
│   └── 03_gold/
├── docs/                   # Documentação (este guia, dicionário de dados e ERD)
├── eda/                    # Análise de desproporcionalidade e materiais auxiliares
├── src/
│   ├── analytical/         # Geração do dataset analítico e métricas (stubs)
│   ├── etl/                # Notebooks ELT/ETL (medicamentos, notificações e reações)
│   ├── utils/              # Funções auxiliares para normalização e merge
│   ├── libs.ipynb          # Instalação das dependências via notebook
│   └── requirements.txt    # Dependências Python
├── tests/                  # Análises exploratórias, dashboard e validações Silver/Gold
│   ├── eda_*.ipynb / analytics.ipynb
│   ├── vigimed_dash.pbix
│   ├── validacao_medicamentos/
│   ├── validacao_notificacao/
│   └── validacao_reacoes/
```

---

## Por onde começar

1. **Consumir a camada Gold publicada** — Baixe o dataset no Dataverse (versão **V2**) e utilize o `data_dictionary.md` e o `erd.md`.
2. **Executar ou estender o pipeline ETL** — Os notebooks estão em [`src/etl/`](../src/etl/) (organizados por domínio: `medicamentos/`, `notificacoes/` e `reacoes/`). Utilize `%run` com [`config/bootstrap.py`](../config/bootstrap.py) para configurar o `project_root` e importar as funções de `utils`.
3. **Análise de desproporcionalidade** — Os módulos iniciais estão em [`src/analytical/`](../src/analytical/) e os notebooks em [`eda/disproportionality_analysis/`](../eda/disproportionality_analysis/).
4. **Explorar e validar** — Os notebooks de EDA e validação estão disponíveis em [`tests/`](../tests/) (`eda_*`, `analytics.ipynb` e `validacao_*`).

---

## Resumo do Pipeline

Fontes de dados (CSV da ANVISA + ATC + MedDRA) → **Bronze** → **Silver** (`hist_*`) → **Gold** (dimensões + tabelas fato) → `fat_analytical` → métricas de desproporcionalidade (ROR, PRR, IC, EBGM).

O diagrama completo em Mermaid está disponível em [`README.md`](../README.md#pipeline-elt).
