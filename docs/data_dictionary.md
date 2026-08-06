# Data Dictionary / Dicionário de Dados
## VigiMed Dataset — camada Gold

---

## Project Description / Descrição do Projeto

**[EN]**  
This dataset contains Individual Case Safety Reports (ICSRs) from VigiMed, Brazil's national pharmacovigilance system. The gold layer is organized as a fact constellation (star-like) schema to support drug safety analysis and data mining.

**[PT]**  
Este dataset contém notificações de eventos adversos (ICSRs) do VigiMed, o sistema nacional de farmacovigilância do Brasil. A camada gold está organizada em um esquema de constelação de fatos (estilo estrela) para facilitar análises de segurança de medicamentos e mineração de dados.

**Public release / Publicação:** [Harvard Dataverse — doi:10.7910/DVN/DRWDMU](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DRWDMU)

**ERD (Mermaid, todas as colunas):** [`erd.md`](erd.md)

---

## Technical Specifications / Especificações Técnicas

- **Format / Formato:** Parquet (também CSV em algumas dimensões)
- **Main key / Chave principal:** `IDENTIFICACAO_NOTIFICACAO`
- **Tools / Ferramentas:** Python, SQL, DuckDB, Jupyter
- **Source code / Código:** https://github.com/mlab-inf-ufrgs/vigimed

### Primary keys (gold) / Chaves primárias

| Table / Tabela | PK |
| --- | --- |
| `dim_notificacoes` | `IDENTIFICACAO_NOTIFICACAO` |
| `dim_atc` | `ATC_CODE_LEVEL_4` |
| `dim_soc_llt` | `REACAO_CHAVE` |
| `dim_detentor_registro` | `DETENTOR_REGISTRO_CHAVE` |
| `dim_concentracao` | `CONCENTRACAO_TIPO_CHAVE` |
| `dim_dose` | `DOSE_TIPO_CHAVE` |
| `dim_dose_frequencia` | `FREQUENCIA_DOSE_INTERVALO_TIPO_CHAVE` |
| `dim_duracao` | `DURACAO_TIPO_CHAVE` |
| `dim_forma_farmaceutica` | `FORMA_FARMACEUTICA_CHAVE` |
| `dim_via_adm` | `VIA_ADMINISTRACAO_CHAVE` |
| `fat_medicamentos` | (grain: notificação × medicamento; FK → `IDENTIFICACAO_NOTIFICACAO`) |
| `fat_reacoes` | (grain: notificação × reação; FK → `IDENTIFICACAO_NOTIFICACAO`, `REACAO_CHAVE`) |

---

## 1. Fact Tables / Tabelas de Fatos

### `fat_reacoes` (Adverse Reactions / Reações)

| Column / Coluna | Type / Tipo | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- |
| IDENTIFICACAO_NOTIFICACAO | string | Report identifier (FK → `dim_notificacoes`) | Identificador da notificação (FK) |
| DATA_INICIO_HORA | datetime | Reaction start | Início da reação |
| DATA_FINAL_HORA | datetime | Reaction end | Fim da reação |
| REACAO_CHAVE | string | MedDRA LLT key (FK → `dim_soc_llt`) | Chave MedDRA LLT (FK) |
| GRAVE_CHAVE | integer | Seriousness code | Código de gravidade |
| GRAVE_VALOR | string | Seriousness label | Rótulo de gravidade |
| DESFECHO_CHAVE | integer | Outcome code | Código do desfecho |
| DESFECHO_VALOR | string | Outcome label | Rótulo do desfecho |
| DURACAO_TIPO_CHAVE | integer | Duration unit code (FK → `dim_duracao`) | Código da unidade de duração (FK) |
| DURACAO_TIPO_VALOR | string | Duration unit label | Unidade de duração |
| DURACAO_VALOR | float | Duration value | Valor da duração |
| GRAVIDADE_RESULTADO_OBITO | integer | Death criterion (flag) | Critério óbito (flag) |
| GRAVIDADE_AMEACA_VIDA | integer | Life-threatening (flag) | Ameaça à vida (flag) |
| GRAVIDADE_INCAPACIDADE | integer | Disability (flag) | Incapacidade (flag) |
| GRAVIDADE_HOSPITALIZACAO | integer | Hospitalization (flag) | Hospitalização (flag) |
| GRAVIDADE_OUTRO_EFEITO | integer | Other medically important (flag) | Outro efeito clinicamente importante (flag) |
| GRAVIDADE_ANOMALIA_CONGENITA | integer | Congenital anomaly (flag) | Anomalia congênita (flag) |
| ATUALIZADO | string | Pipeline refresh date | Data de atualização do pipeline |
| HASH_BRONZE | string | Row hash at bronze | Hash na camada bronze |
| HASH_SILVER | string | Row hash at silver | Hash na camada silver |
| HASH_GOLD | string | Row hash at gold | Hash na camada gold |

---

### `fat_medicamentos` (Medications / Medicamentos)

| Column / Coluna | Type / Tipo | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- |
| IDENTIFICACAO_NOTIFICACAO | string | Report identifier (FK → `dim_notificacoes`) | Identificador da notificação (FK) |
| RELACAO_MEDICAMENTO_EVENTO_CHAVE | integer | Drug–event role code | Código da relação medicamento–evento |
| RELACAO_MEDICAMENTO_EVENTO_VALOR | string | Drug–event role label | Rótulo da relação medicamento–evento |
| NOME_MEDICAMENTO_WHODRUG | string | WHO Drug product name | Nome do medicamento (WHO Drug) |
| PRINCIPIOS_ATIVOS_WHODRUG | string | Active substance(s) | Princípio(s) ativo(s) |
| ATC_CODE_LEVEL_4 | string | ATC level 4 (FK → `dim_atc`) | Código ATC nível 4 (FK) |
| DETENTOR_REGISTRO | string | Marketing authorization holder (raw/matched text) | Detentor do registro (texto) |
| DETENTOR_REGISTRO_SCORE | float | Fuzzy match score | Score do match fuzzy |
| DETENTOR_REGISTRO_CHAVE | integer | Holder key (FK → `dim_detentor_registro`) | Chave do detentor (FK) |
| CONCENTRACAO_TIPO_CHAVE | integer | Concentration unit key (FK → `dim_concentracao`) | Chave do tipo de concentração (FK) |
| CONCENTRACAO_TIPO_VALOR | string | Concentration unit label | Unidade de concentração |
| CONCENTRACAO_VALOR | float | Concentration value | Valor da concentração |
| CONCENTRACAO_VALOR_NUMERADOR | float | Concentration numerator | Numerador da concentração |
| CONCENTRACAO_VALOR_DENOMINADOR | float | Concentration denominator | Denominador da concentração |
| COMPONENTE_SUSPEITO_CHAVE | integer | Suspected component code | Código do componente suspeito |
| COMPONENTE_SUSPEITO_VALOR | string | Suspected component label | Rótulo do componente suspeito |
| ACAO_ADOTADA_CHAVE | integer | Action taken code | Código da ação adotada |
| ACAO_ADOTADA_VALOR | string | Action taken label | Rótulo da ação adotada |
| PROB_ADIC_* | integer | Additional drug-related problem flags (wide) | Flags de problemas adicionais (wide) |
| INDICACAO_MEDDRA_REACAO_CHAVE | integer | Indication MedDRA key | Chave MedDRA da indicação |
| INDICACAO_RELATADA_NOTIFICADOR_INICIAL_REACAO_CHAVE | integer | Reporter-stated indication MedDRA key | Chave MedDRA da indicação relatada |
| DOSE_TIPO_CHAVE | integer | Dose unit key (FK → `dim_dose`) | Chave do tipo de dose (FK) |
| DOSE_TIPO_VALOR | string | Dose unit label | Unidade da dose |
| DOSE_VALOR | float | Dose value | Valor da dose |
| FREQUENCIA_DOSE | string | Dose frequency (text) | Frequência da dose (texto) |
| POSOLOGIA | string | Posology text | Posologia |
| DURACAO_TIPO_CHAVE | integer | Duration unit key (FK → `dim_duracao`) | Chave da unidade de duração (FK) |
| DURACAO_TIPO_VALOR | string | Duration unit label | Unidade de duração |
| DURACAO_VALOR | float | Duration value | Valor da duração |
| INICIO_ADMINISTRACAO | datetime | Treatment start | Início da administração |
| FIM_ADMINISTRACAO | datetime | Treatment end | Fim da administração |
| FORMA_FARMACEUTICA_CHAVE | integer | Dosage form key (FK → `dim_forma_farmaceutica`) | Chave da forma farmacêutica (FK) |
| VIA_ADMINISTRACAO_CHAVE | integer | Route key (FK → `dim_via_adm`) | Chave da via de administração (FK) |
| VIA_ADMINISTRACAO_MAE_PAI_CHAVE | integer | Parent route key (FK → `dim_via_adm`) | Chave da via (mãe/pai) (FK) |
| NUMELO_LOTE | string | Batch/lot number | Número do lote |
| ATUALIZADO | string | Pipeline refresh date | Data de atualização do pipeline |
| HASH_BRONZE / HASH_SILVER / HASH_GOLD | string | Row hashes by layer | Hashes por camada |

---

## 2. Dimension Tables / Tabelas de Dimensões

### `dim_notificacoes` (Case / Notificação)

| Column / Coluna | Type / Tipo | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- |
| IDENTIFICACAO_NOTIFICACAO | string | Unique report ID (PK) | Identificador único da notificação (PK) |
| UF_CHAVE / UF_VALOR | integer / string | Brazilian state | Unidade federativa |
| TIPO_ENTRADA_VIGIMED_CHAVE / _VALOR | integer / string | VigiMed entry type | Tipo de entrada no VigiMed |
| RECEBIDO_DE_CHAVE / _VALOR | integer / string | Received from | Recebido de |
| DATA_INCLUSAO_SISTEMA | datetime | System inclusion date | Data de inclusão no sistema |
| DATA_ULTIMA_ATUALIZACAO | datetime | Last update | Última atualização |
| DATA_NOTIFICACAO | datetime | Notification date | Data da notificação |
| TIPO_NOTIFICACAO_CHAVE / _VALOR | integer / string | Notification type | Tipo de notificação |
| NOTIFICACAO_PARENT_CHILD_CHAVE / _VALOR | integer / string | Parent/child case flag | Notificação parent/child |
| DATA_NASCIMENTO | datetime | Date of birth | Data de nascimento |
| IDADE_MOMENTO_REACAO_* | mixed | Age at reaction (type + value) | Idade no momento da reação |
| GRUPO_IDADE_CHAVE / _VALOR | integer / string | Age group | Grupo etário |
| IDADE_GESTACIONAL_MOMENTO_REACAO_* | mixed | Gestational age at reaction | Idade gestacional no evento |
| SEXO_CHAVE / _VALOR | integer / string | Sex | Sexo |
| GESTANTE_CHAVE / _VALOR | integer / string | Pregnant | Gestante |
| LACTANTE_CHAVE / _VALOR | integer / string | Lactating | Lactante |
| PESO_KG | string | Weight (kg) | Peso (kg) |
| ALTURA_CM | string | Height (cm) | Altura (cm) |
| REACAO_EVENTO_ADVERSO_MEDDRA | string | Adverse event text (MedDRA-related) | Texto do evento adverso |
| GRAVE_CHAVE / _VALOR | integer / string | Case seriousness | Gravidade do caso |
| GRAVIDADE_CHAVE / _VALOR | integer / string | Seriousness criteria | Critérios de gravidade |
| DESFECHO_CHAVE / _VALOR | integer / string | Case outcome | Desfecho |
| DATA_INICIO_HORA / DATA_FINAL_HORA | datetime | Event start/end | Início/fim do evento |
| DURACAO_* | mixed | Event duration | Duração do evento |
| RELACAO_MEDICAMENTO_EVENTO_* | mixed | Drug–event relation (case level) | Relação medicamento–evento |
| NOME_MEDICAMENTO_WHODRUG | string | Drug name (case level) | Nome do medicamento |
| ACAO_ADOTADA_* | mixed | Action taken | Ação adotada |
| NOTIFICADOR_CHAVE / _VALOR | integer / string | Notifier profile | Perfil do notificador |
| ATUALIZADO | string | Pipeline refresh date | Data de atualização |
| HASH_BRONZE / HASH_SILVER / HASH_GOLD | string | Row hashes by layer | Hashes por camada |

---

### `dim_atc` (ATC Classification / Classificação ATC)

| Column / Coluna | Type / Tipo | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- |
| ATC_CODE_LEVEL_1 … _5 | string | ATC codes by level | Códigos ATC por nível |
| ATC_LEVEL | integer | Level of the row (1–5) | Nível da linha (1–5) |
| ATC_CODE_LEVEL_*_LEVEL_NAME | string | Level names | Nomes dos níveis ATC |
| ATC_CODE_LEVEL / ATC_NAME_LEVEL | string | Code/name at row level | Código/nome no nível da linha |
| ATC_CODE_LEVEL_4 | string | Level 4 code (join key / PK for joins) | Código nível 4 (chave de junção) |
| DDD_VALUE | float | Defined Daily Dose | Dose Diária Definida (OMS) |
| UNIT | string | DDD unit | Unidade do DDD |
| ADM_R | string | Administration route (DDD) | Via de administração (DDD) |
| COMMENT | string | Notes | Comentários |

---

### `dim_soc_llt` (MedDRA Hierarchy / Hierarquia MedDRA)

| Column / Coluna | Type / Tipo | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- |
| REACAO_CHAVE | string | Reaction key (PK; LLT-based) | Chave da reação (PK) |
| PRIMARY_FLAG | string | Primary path flag | Flag de caminho primário |
| SOC_CODE / SOC_NAME / SOC_ABBREV | string | System Organ Class | Classe de Órgão/Sistema |
| PRIMARY_SOC | string | Primary SOC indicator | SOC primário |
| HLGT_CODE / HLGT_NAME | string | High Level Group Term | Termo de grupo de alto nível |
| HLT_CODE / HLT_NAME | string | High Level Term | Termo de alto nível |
| PT_CODE / PT_NAME | string | Preferred Term | Termo preferencial |
| LLT_CODE / LLT_NAME | string | Lowest Level Term | Termo de nível mais baixo |

---

### Lookup dimensions / Dimensões de domínio

| Table / Tabela | PK | Value column / Coluna de valor | Description (EN) | Descrição (PT) |
| --- | --- | --- | --- | --- |
| `dim_detentor_registro` | `DETENTOR_REGISTRO_CHAVE` | `DETENTOR_REGISTRO_VALOR` | MAH / registration holder | Detentor do registro |
| `dim_concentracao` | `CONCENTRACAO_TIPO_CHAVE` | `CONCENTRACAO_TIPO_VALOR` | Concentration unit | Unidade de concentração |
| `dim_dose` | `DOSE_TIPO_CHAVE` | `DOSE_TIPO_VALOR` | Dose unit | Unidade de dose |
| `dim_dose_frequencia` | `FREQUENCIA_DOSE_INTERVALO_TIPO_CHAVE` | `FREQUENCIA_DOSE_INTERVALO_TIPO_VALOR` | Dose frequency interval | Intervalo de frequência da dose |
| `dim_duracao` | `DURACAO_TIPO_CHAVE` | `DURACAO_TIPO_VALOR` | Duration unit | Unidade de duração |
| `dim_forma_farmaceutica` | `FORMA_FARMACEUTICA_CHAVE` | `FORMA_FARMACEUTICA_VALOR` | Pharmaceutical form | Forma farmacêutica |
| `dim_via_adm` | `VIA_ADMINISTRACAO_CHAVE` | `VIA_ADMINISTRACAO_VALOR` (+ EN/PT descriptions) | Route of administration | Via de administração |

---

## Data Integrity / Integridade de Dados

**[EN]**  
Fact and case tables include HASH columns (`HASH_BRONZE`, `HASH_SILVER`, `HASH_GOLD`) for traceability across the Bronze → Silver → Gold ETL.

**[PT]**  
As tabelas de fatos e de notificação incluem colunas de HASH (`HASH_BRONZE`, `HASH_SILVER`, `HASH_GOLD`) para rastreabilidade no ETL Bronze → Silver → Gold.

---

## Source Code / Código Fonte

**[EN]**  
Extraction, transformation, and analysis notebooks: https://github.com/mlab-inf-ufrgs/vigimed  

**[PT]**  
Notebooks de extração, transformação e análise: https://github.com/mlab-inf-ufrgs/vigimed  

---
