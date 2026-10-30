# Dipirona e associações no VigiMed, 2019–2025

Análise ad hoc descritiva e exploratória para o TCC de Farmácia de Isabel Giovana Fetter Schuch, da UFCSPA. Consome a Gold do VigiMed sem alterar o pipeline ou os Parquet originais.

## Para Isabel

O pacote de entrega contém a base detalhada em CSV, o dicionário das colunas, três resumos e um [guia de uso no Excel](LEIA_ME_ISABEL.txt). É possível trabalhar com esses arquivos sem instalar ferramentas de programação ou usar o GitHub.

Os CSVs usam UTF-8 com BOM e ponto e vírgula. São arquivos compatíveis com Excel, e não pastas de trabalho `.xlsx`. O código neste diretório serve para documentar e reproduzir a preparação dos dados.

## Arquivos versionados

| Arquivo | Finalidade |
| --- | --- |
| `base_analitica.py` | Leitura da Gold, diagnóstico, identificação, classificação, junções, verificações e exportação. |
| `2_base_analitica_dipirona.ipynb` | As dez etapas do estudo, usando as mesmas funções do script. Salvo sem saídas para não publicar linhas de dados no Git. |
| `test_base_analitica.py` | Testes de aliases, ambiguidades, limiares, datas, papéis e cardinalidade do build real. |
| `requirements.txt` | Versões de DuckDB e pandas usadas na execução de referência. |
| `METODOLOGIA.md` | Relatório de QA da execução de referência, decisões, resultados e limitações. |
| `proveniencia/manifesto.json` | Parâmetros e SHA-256 dos cinco arquivos Gold, da implementação e do CSV de referência. |
| `LEIA_ME_ISABEL.txt` | Orientações para a pesquisadora. |
| `preparar_entrega.py` | Montagem do ZIP com os arquivos destinados à pesquisadora, após conferir o manifesto. |

A [coleta preliminar em `eda/dipirona`](https://github.com/mlab-inf-ufrgs/vigimed/tree/9d04d156a3a60ed3ef83ff1d0c01335102a462b3/eda/dipirona) permanece preservada na branch original como histórico da investigação. Esta análise pode ser executada independentemente dela.

## Reprodução técnica

Executar os comandos a partir da raiz do repositório. Requer Python 3.9 ou superior.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r ad-hoc-analysis/dipirona/requirements.txt
.venv/bin/python ad-hoc-analysis/dipirona/base_analitica.py
.venv/bin/python -m unittest discover -s ad-hoc-analysis/dipirona -p 'test_*.py' -v
.venv/bin/python ad-hoc-analysis/dipirona/preparar_entrega.py
```

Disponibilizar os cinco Parquet do estudo nos caminhos `data/03_gold/<tabela>/<tabela>.parquet`: `dim_notificacoes`, `fat_medicamentos`, `fat_reacoes`, `dim_soc_llt` e `dim_atc`. A fonte publicada está indicada no [README do projeto](../../README.pt-BR.md). Comparar seus hashes com o manifesto; uma versão diferente pode produzir outros totais.

Para executar o notebook, usar o ambiente Jupyter do projeto com o kernel `.venv`. O script não depende de Jupyter. O notebook foi verificado célula a célula no mesmo processo IPython, pois o ambiente de execução não permitiu iniciar um kernel separado por sockets.

O resultado é gravado em `ad-hoc-analysis/dipirona/output/`. Não é necessário versionar esse diretório. O pacote para envio fica em `ad-hoc-analysis/dipirona/entrega/`.

### Parâmetros

O padrão agrupa associações com menos de **50 notificações distintas**, contadas no período inteiro. É possível testar outro limite em um diretório independente:

```sh
.venv/bin/python ad-hoc-analysis/dipirona/base_analitica.py --threshold 30 --output /tmp/dipirona-limiar-30
```

A referência temporal padrão é `DATA_NOTIFICACAO`, sem preenchimento por outra data. Uma análise de ingresso no sistema deve usar outro diretório e documentar a mudança de referência:

```sh
.venv/bin/python ad-hoc-analysis/dipirona/base_analitica.py --date-field DATA_INCLUSAO_SISTEMA --output /tmp/dipirona-por-inclusao
```

## Interpretação

O grão é notificação × composição suspeita × assinatura de reação. Contar notificações distintas por `id_notificacao` e registros de reação distintos por `id_reacao`, excluindo vazios. A contagem de linhas não representa nenhum desses totais. Uma notificação pode aparecer em mais de um grupo.

O recorte por data da notificação exclui casos sem essa data. A extração utilizada não comprova cobertura integral de dezembro de 2025. Os critérios de agrupamento, os registros sem codificação MedDRA e as exclusões por integridade estão detalhados na [metodologia](METODOLOGIA.md).

## Atualização da referência

Após alterar o código ou atualizar a Gold, executar o script e os testes, revisar os resultados e atualizar `METODOLOGIA.md` a partir de `output/qa_relatorio.md` e `proveniencia/manifesto.json` a partir de `output/manifesto.json`. Esses arquivos identificam uma execução de referência; os resultados gerados não entram no Git. Gerar um novo ZIP somente após revisar a mudança metodológica com a pesquisadora quando aplicável.
