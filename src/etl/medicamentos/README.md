## Pipeline `fat_medicamentos`

Resumo do fluxo a partir do Parquet bronze (`data/01_bronze/anvisa/Medicamentos/Medicamentos.parquet`), passando pelo `hist_silver` no notebook `elt_fat_medicamentos_new.ipynb` e chegando ao conjunto gold.

### Conjuntos
- **Bronze**: colunas cruas conforme arquivo original.
- **Silver (`hist_silver`)**: bronze copiado, campos textuais normalizados, colunas enriquecidas com chaves/valores, parsing de datas/medidas e harmonizações via mapeamentos e fuzzy matching.
- **Gold**: `hist_silver_dedup` após expansões, deduplicações e renomeações finais, com hash consolidado.

### Normalizações iniciais (silver)
- `normalize_rows` aplicado a todas as colunas `object`: `strip`, converte `nan/None/NaT/NULL` para `NaN`, remove acentos, caixa alta.
- Datas (`INICIO_ADMINISTRACAO`, `FIM_ADMINISTRACAO`): `normalize_date_column` para `datetime64[ns]` no formato `%Y%m%d`, arredondado para dia.
- `HASH_BRONZE`: hash SHA256 das colunas brutas principais.

### Mapeamentos declarativos (`apply_mappings`)
Para cada coluna mapeada, são criadas `<COL>_VALOR` (texto upper) e `<COL>_CHAVE` (código Int64, `fillna_chave=0`, `fillna_valor="DESCONHECIDO"`) com normalização de acentos/caixa.
- `RELACAO_MEDICAMENTO_EVENTO`: SUSPEITO→1, CONCOMITANTE→2, MEDICAMENTO NAO ADMINISTRADO→3, INTERACAO→4.
- `COMPONENTE_SUSPEITO`: PRINCÍPIO ATIVO→1, EXCIPIENTE, NÃO CLASSIFICADO→2, SOLVENTE→3, CORANTE→4, CONSERVANTE→5, AGENTE FLAVORIZADOR→6, EXCESSO PERCENTUAL→7, ANTIOXIDANTE→8, ESTABILIZANTE→9.
- `ACAO_ADOTADA`: RETIRADA DO MEDICAMENTO→1, SEM ALTERACAO DA DOSE→2, NAO APLICAVEL→3, REDUCAO DA DOSE→4, AUMENTO DA DOSE→5.

### Parsing de duração (`normalize_duracao`)
- Entrada `DURACAO` como número + unidade (ex.: `4 dia`, `30 minuto`, `1 hora`), normalizada para caixa alta sem acento.
- Saída:
  - `DURACAO_TIPO_CHAVE`: unidade em texto upper.
  - `DURACAO_TIPO_VALOR`: código numérico (segundo=1, minuto=2, hora=3, dia=4, semana=5, mes=6, ano=7, decada=8, ciclico=9; desconhecido=0).
  - `DURACAO_VALOR`: valor numérico (float).
  - Valores inválidos/ausentes → chave "DESCONHECIDO", valor `0`, medida `NaN`.

### Parsing de concentração (`normalize_concentracao`)
- Normaliza texto (acentos, caixa, espaços, `por`→`/`) e tenta:
  - Formatos razão `NUM UNIT / (NUM) UNIT` (ex.: `10 mg/5 ml`), calculando razão `NUM/denom`.
  - Formatos simples `NUM UNIT` (ex.: `500 mg`, `1 g`).
  - Números sem unidade ficam como desconhecido.
- Saída:
  - `CONCENTRACAO_TIPO_CHAVE`: código Int64 do tipo de unidade (ex.: mg=1, g=2, etc.; desconhecido=code de `CONCENTRACAO_METADATA["desconhecido"]`).
  - `CONCENTRACAO_TIPO_VALOR`: rótulo textual da unidade (ex.: `milligram (mg)`, `gram (g)`, ou `desconhecido`).
  - `CONCENTRACAO_VALOR`: valor final (razão ou simples).
  - `CONCENTRACAO_VALOR_NUMERADOR`: numerador original.
  - `CONCENTRACAO_VALOR_DENOMINADOR`: denominador (1.0 se omitido).

### Outras transformações (silver)
- `VIA_ADMINISTRACAO`, `VIA_ADMINISTRACAO_MAE_PAI`: fuzzy match (`normalizar_via_fuzzy`) para dimensão de vias, produzindo `<COL>_CHAVE` numérico; faltantes recebem código padrão (ex.: 5 ou 0 conforme dimensão).
- `DETENTOR_REGISTRO`, `FORMA_FARMACEUTICA`: `fuzzy_merge` com dimensões pré-calculadas, gera `<COL>_CHAVE` e `<COL>_SCORE`; chaves faltantes preenchidas com 0.
- `INDICACAO_MEDDRA` e `INDICACAO_RELATADA_NOTIFICADOR_INICIAL`: fuzzy merge com `dim_soc_llt` (MedDRA LLT), produzindo `PK_LLT_*` e scores.
- `PROBLEMAS_ADICIONAIS_RELCIONADOS_MEDICAMENTO`: `expandir_lista_wide` cria dummies `PROB_ADIC_*` para cada ocorrência.
- `CODIGO_ATC`: renomeado para `ATC_CODE_LEVEL_4` e desagregado quando há múltiplos valores (`desagrupar_colunas_pipe`), gerando `hist_silver_dedup`.
- Hashes adicionais: `HASH_SILVER` e, ao final, `HASH_GOLD` com colunas selecionadas.

### Colunas finais (gold)
- Seleção e renomeações aplicadas sobre `hist_silver_dedup`, incluindo:
  - Identificadores e textos principais (`IDENTIFICACAO_NOTIFICACAO`, `NOME_MEDICAMENTO_WHODRUG`, `PRINCIPIOS_ATIVOS_WHODRUG`, `ATC_CODE_LEVEL_4`).
  - Chaves/scores fuzzy (`DETENTOR_REGISTRO_CHAVE`, `DETENTOR_REGISTRO_SCORE`, `FORMA_FARMACEUTICA_CHAVE`, `FORMA_FARMACEUTICA_SCORE`).
  - Medidas normalizadas (`CONCENTRACAO_*`, `DOSE_*`, `DURACAO_*`).
  - Via de administração (`VIA_ADMINISTRACAO[_MAE_PAI]` e chaves).
  - Indicações MedDRA (`PK_LLT_INDICACAO_MEDDRA`, `PK_LLT_INDICACAO_RELATADA_NOTIFICADOR_INICIAL` após renomear de `PK_LLT_LK`/`PK_LLT_MATCH`).
  - Expansões de problemas adicionais (`PROB_ADIC_*`).
  - Mapeamentos categóricos (`RELACAO_MEDICAMENTO_EVENTO_*`, `COMPONENTE_SUSPEITO_*`, `ACAO_ADOTADA_*`).
  - Datas normalizadas, número de lote, hashes.

### Observações rápidas
- Todos os campos textuais intermediários são upper/sem acento para garantir match e consistência; valores apresentados (_VALOR) permanecem em upper.
- Chaves categóricas são `Int64` com fallback `0` para desconhecidos/ausentes.
- Ajustes de parsing (duração/concentração) preservam o valor original em colunas de texto e expõem campos derivados para consumo analítico.

