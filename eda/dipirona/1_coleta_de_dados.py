"""Coleta de dados da dipirona, exportada de eda/dipirona/1_coleta_de_dados.ipynb.

Arquivo para leitura (NotebookLM). Células %%sql não são Python executável.
Outputs das células já executadas estão nos blocos comentados.
As células da seção 6 em diante não tinham output no notebook.
"""

# # **Coleta de dados**

# %% célula 2  (execução 1)
#Bases de Dados 
from pathlib import Path
import pandas as pd
#import duckdb

# Visualização
import plotly.express as px

# Modelagem 
import numpy as np 
from typing import List, Optional

# %% célula 3  (execução 2)
# Configurações de exibição
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 200)

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.displaylimit = 100
%config SqlMagic.named_parameters = "enabled"
%config SqlMagic.autocommit = True

# Se preferir memória: 
%sql duckdb:///:memory:

# --- output ---
# Connecting to 'duckdb:///:memory:'

# %% célula 4  (execução 3)
# download dos files https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DRWDMU
#path = Path("sua_pasta/data/")
path = Path(r"/Users/silmarabarnabe/Desktop/Projetos/vigimed/data/03_gold")
# Caminhos completos para o DuckDB (parâmetros nomeados não expandem expressões)
path_atc = str(path / 'dim_atc/dim_atc.parquet')
path_fat_medicamentos = str(path / 'fat_medicamentos/fat_medicamentos.parquet')
path_dim_notificacoes = str(path / 'dim_notificacoes/dim_notificacoes.parquet')
path_fat_reacoes = str(path / 'fat_reacoes/fat_reacoes.parquet')
path_dim_soc_llt = str(path / 'dim_soc_llt/dim_soc_llt.parquet')

# %% célula 5  (execução 4)
%sql ROLLBACK;

# --- output ---
# Empty DataFrame
# Columns: [Success]
# Index: []

# %% célula 6  (execução 5)
%%sql
DROP TABLE IF EXISTS dim_atc;
CREATE TABLE dim_atc AS
SELECT * FROM read_parquet(:path_atc);

DROP TABLE IF EXISTS fat_medicamentos;
CREATE TABLE fat_medicamentos AS
SELECT *
FROM read_parquet(:path_fat_medicamentos);

DROP TABLE IF EXISTS dim_notificacoes;
CREATE TABLE dim_notificacoes AS
SELECT *
FROM read_parquet(:path_dim_notificacoes);

DROP TABLE IF EXISTS fat_reacoes;
CREATE TABLE fat_reacoes AS
SELECT *
FROM read_parquet(:path_fat_reacoes);

DROP TABLE IF EXISTS dim_soc_llt;
CREATE TABLE dim_soc_llt AS
SELECT *
FROM read_parquet(:path_dim_soc_llt);

# --- output ---
# Empty DataFrame
# Columns: [Success]
# Index: []

# # **5️⃣ Entendimento dos dados**

# ### dim_notificacoes

# %% célula 9  (execução 6)
%%sql 
select * from dim_notificacoes limit 2

# --- output ---
#   IDENTIFICACAO_NOTIFICACAO  UF_CHAVE UF_VALOR  TIPO_ENTRADA_VIGIMED_CHAVE TIPO_ENTRADA_VIGIMED_VALOR  RECEBIDO_DE_CHAVE     RECEBIDO_DE_VALOR DATA_INCLUSAO_SISTEMA DATA_ULTIMA_ATUALIZACAO  \
# 0       BR-ANVISA-300212656        25       SP                           2     EMPRESAS FARMACEUTICAS                  5  EMPRESA FARMACEUTICA            2023-09-28              2023-09-28   
# 1       BR-ANVISA-300208322        25       SP                           2     EMPRESAS FARMACEUTICAS                  5  EMPRESA FARMACEUTICA            2023-09-01              2023-09-01   
#
#   DATA_NOTIFICACAO  TIPO_NOTIFICACAO_CHAVE  TIPO_NOTIFICACAO_VALOR  NOTIFICACAO_PARENT_CHILD_CHAVE NOTIFICACAO_PARENT_CHILD_VALOR DATA_NASCIMENTO  IDADE_MOMENTO_REACAO_TIPO_CHAVE  \
# 0              NaT                       1  NOTIFICACAO ESPONTANEA                               0                   DESCONHECIDO      1990-01-31                                1   
# 1              NaT                       1  NOTIFICACAO ESPONTANEA                               0                   DESCONHECIDO             NaT                                0   
#
#   IDADE_MOMENTO_REACAO_TIPO_VALOR  IDADE_MOMENTO_REACAO_VALOR  GRUPO_IDADE_CHAVE GRUPO_IDADE_VALOR  IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_CHAVE IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_VALOR  \
# 0                             ANO                        30.0                  0      DESCONHECIDO                                            0                                DESCONHECIDO   
# 1                    DESCONHECIDO                         NaN                  0      DESCONHECIDO                                            0                                DESCONHECIDO   
#
#    IDADE_GESTACIONAL_MOMENTO_REACAO_VALOR  SEXO_CHAVE SEXO_VALOR  GESTANTE_CHAVE GESTANTE_VALOR  LACTANTE_CHAVE LACTANTE_VALOR PESO_KG ALTURA_CM REACAO_EVENTO_ADVERSO_MEDDRA  GRAVE_CHAVE  \
# 0                                     NaN           1   FEMININO               2           NĂO                2           NĂO     68.0       165                  Hemiparesia            1   
# 1                                     NaN           1   FEMININO               2           NĂO                2           NĂO     None      None                     Cefaleia            2   
#
#   GRAVE_VALOR  GRAVIDADE_CHAVE                          GRAVIDADE_VALOR  DESFECHO_CHAVE DESFECHO_VALOR DATA_INICIO_HORA DATA_FINAL_HORA  DURACAO_TIPO_CHAVE DURACAO_TIPO_VALOR  DURACAO_VALOR  \
# 0         SIM                1  OUTRO EFEITO CLINICAMENTE SIGNIFICATIVO               1     RECUPERADO       2021-01-25      2021-02-06                   4                DIA           12.0   
# 1         NĂO                1  OUTRO EFEITO CLINICAMENTE SIGNIFICATIVO               0   DESCONHECIDO       2021-01-22             NaT                   0       DESCONHECIDO            NaN   
#
#    RELACAO_MEDICAMENTO_EVENTO_CHAVE RELACAO_MEDICAMENTO_EVENTO_VALOR NOME_MEDICAMENTO_WHODRUG  ACAO_ADOTADA_CHAVE ACAO_ADOTADA_VALOR  NOTIFICADOR_CHAVE  \
# 0                                 2                     CONCOMITANTE                   Tamisa                   2      NAO APLICAVEL                  4   
# 1                                 1                         SUSPEITO                CoronaVac                   2      NAO APLICAVEL                  2   
#
#                                NOTIFICADOR_VALOR  ATUALIZADO                                        HASH_BRONZE                                        HASH_SILVER  \
# 0                                         MEDICO  2026-01-15  c540f6f2873cded948f9a6156d6a92cf9f59b7e110f84e...  3c04663c8c6a69bba2510ab19fa043d1d6670b81e42857...   
# 1  CONSUMIDOR OU OUTRO NAO PROFISSIONAL DE SAUDE  2026-01-15  1f6805d588f843fe6f27dc43ae2026701e8d0400f3a101...  716905c5a2cc460902e5682c94bd1379f674208b0c6ef5...   
#
#                                            HASH_GOLD  
# 0  95ef1ec6b9f7b04d5d423f561ef99f6fe7ea4ce5f916a9...  
# 1  8db30198a3122b4ee42039e05a0d958d0caa1efd8f2ece...

# %% célula 10  (execução 7)
%%sql 
select IDENTIFICACAO_NOTIFICACAO,count(1) as qt
from dim_notificacoes 
group by 1
having qt > 1
limit 10

# --- output ---
# Empty DataFrame
# Columns: [IDENTIFICACAO_NOTIFICACAO, qt]
# Index: []

# %% célula 11  (execução 8)
%%sql 
select * from dim_notificacoes 
where IDENTIFICACAO_NOTIFICACAO = 'BR-ANVISA-300171130'

# --- output ---
#   IDENTIFICACAO_NOTIFICACAO  UF_CHAVE UF_VALOR  TIPO_ENTRADA_VIGIMED_CHAVE TIPO_ENTRADA_VIGIMED_VALOR  RECEBIDO_DE_CHAVE                     RECEBIDO_DE_VALOR DATA_INCLUSAO_SISTEMA  \
# 0       BR-ANVISA-300171130        25       SP                           1          SERVICOS DE SAUDE                  4  CENTRO REGIONAL DE FARMACOVIGILANCIA            2023-01-10   
#
#   DATA_ULTIMA_ATUALIZACAO DATA_NOTIFICACAO  TIPO_NOTIFICACAO_CHAVE  TIPO_NOTIFICACAO_VALOR  NOTIFICACAO_PARENT_CHILD_CHAVE NOTIFICACAO_PARENT_CHILD_VALOR DATA_NASCIMENTO  \
# 0              2023-01-10       2023-01-10                       1  NOTIFICACAO ESPONTANEA                               0                   DESCONHECIDO             NaT   
#
#    IDADE_MOMENTO_REACAO_TIPO_CHAVE IDADE_MOMENTO_REACAO_TIPO_VALOR  IDADE_MOMENTO_REACAO_VALOR  GRUPO_IDADE_CHAVE GRUPO_IDADE_VALOR  IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_CHAVE  \
# 0                                1                             ANO                        58.0                  6            ADULTO                                            0   
#
#   IDADE_GESTACIONAL_MOMENTO_REACAO_TIPO_VALOR  IDADE_GESTACIONAL_MOMENTO_REACAO_VALOR  SEXO_CHAVE SEXO_VALOR  GESTANTE_CHAVE GESTANTE_VALOR  LACTANTE_CHAVE LACTANTE_VALOR PESO_KG ALTURA_CM  \
# 0                                DESCONHECIDO                                     NaN           2  MASCULINO               0   DESCONHECIDO               0   DESCONHECIDO    None      None   
#
#   REACAO_EVENTO_ADVERSO_MEDDRA  GRAVE_CHAVE GRAVE_VALOR  GRAVIDADE_CHAVE GRAVIDADE_VALOR  DESFECHO_CHAVE DESFECHO_VALOR DATA_INICIO_HORA DATA_FINAL_HORA  DURACAO_TIPO_CHAVE DURACAO_TIPO_VALOR  \
# 0                 Prurido oral            2         NĂO                0    DESCONHECIDO               1     RECUPERADO       2023-01-10      2023-01-10                   0       DESCONHECIDO   
#
#    DURACAO_VALOR  RELACAO_MEDICAMENTO_EVENTO_CHAVE RELACAO_MEDICAMENTO_EVENTO_VALOR NOME_MEDICAMENTO_WHODRUG  ACAO_ADOTADA_CHAVE ACAO_ADOTADA_VALOR  NOTIFICADOR_CHAVE NOTIFICADOR_VALOR  ATUALIZADO  \
# 0            NaN                                 1                         SUSPEITO                  Henetix                   0       DESCONHECIDO                  3      FARMACEUTICO  2026-01-15   
#
#                                          HASH_BRONZE                                        HASH_SILVER                                          HASH_GOLD  
# 0  0a98b73bf675dcce6bfbe0a7e08333c2bd6dad4a7ea962...  6c94238fcb1543d2c24c3036169c67658af91aa5c58794...  c1a24670cc84b3b40cdfaa01d5fa0f7b5a8b75b7113813...

# ### fat_medicamentos

# %% célula 13  (execução 9)
%%sql 
select * from fat_medicamentos 
where IDENTIFICACAO_NOTIFICACAO = 'BR-ANVISA-300171130'

# --- output ---
#   IDENTIFICACAO_NOTIFICACAO  RELACAO_MEDICAMENTO_EVENTO_CHAVE RELACAO_MEDICAMENTO_EVENTO_VALOR NOME_MEDICAMENTO_WHODRUG PRINCIPIOS_ATIVOS_WHODRUG ATC_CODE_LEVEL_4 ATC_CODE_LEVEL_5  \
# 0       BR-ANVISA-300171130                                 2                     CONCOMITANTE                NOVALGINA         METAMIZOLE SODIUM            N02BB          N02BB02   
# 1       BR-ANVISA-300171130                                 2                     CONCOMITANTE                 BUSCOPAN     HYOSCINE BUTYLBROMIDE            A03BB          A03BB01   
# 2       BR-ANVISA-300171130                                 1                         SUSPEITO                  HENETIX                IOBITRIDOL            V08AB          V08AB11   
#
#                 ATC_LEVEL_5  ATC_LEVEL_5_SCORE TIPO_PRODUTO  VACINA_FLAG DETENTOR_REGISTRO  DETENTOR_REGISTRO_SCORE  DETENTOR_REGISTRO_CHAVE  CONCENTRACAO_TIPO_CHAVE CONCENTRACAO_TIPO_VALOR  \
# 0        N02BB02_Metamizole              100.0  MEDICAMENTO            0              None                      0.0                        0                        0            DESCONHECIDO   
# 1  A03BB01_Butylscopolamine              100.0  MEDICAMENTO            0              None                      0.0                        0                        0            DESCONHECIDO   
# 2        V08AB11_Iobitridol              100.0  MEDICAMENTO            0              None                      0.0                        0                        0            DESCONHECIDO   
#
#    CONCENTRACAO_VALOR  CONCENTRACAO_VALOR_NUMERADOR  CONCENTRACAO_VALOR_DENOMINADOR  COMPONENTE_SUSPEITO_CHAVE COMPONENTE_SUSPEITO_VALOR  ACAO_ADOTADA_CHAVE ACAO_ADOTADA_VALOR  PROB_ADIC_ABUSO  \
# 0                 NaN                           NaN                             NaN                          0              DESCONHECIDO                   0       DESCONHECIDO                0   
# 1                 NaN                           NaN                             NaN                          0              DESCONHECIDO                   0       DESCONHECIDO                0   
# 2                 NaN                           NaN                             NaN                          0              DESCONHECIDO                   0       DESCONHECIDO                0   
#
#    PROB_ADIC_ERRO_DE_MEDICACAO  PROB_ADIC_EXPOSICAO_OCUPACIONAL  PROB_ADIC_FALSIFICACAO  PROB_ADIC_LOTES_TESTADOS_E_DENTRO_DAS_ESPECIFICACOES  PROB_ADIC_LOTES_TESTADOS_E_FORA_DAS_ESPECIFICACOES  \
# 0                            0                                0                       0                                                  0                                                     0    
# 1                            0                                0                       0                                                  0                                                     0    
# 2                            0                                0                       0                                                  0                                                     0    
#
#    PROB_ADIC_MEDICAMENTO_TOMADO_FORA_DA_DATA_DE_VALIDADE  PROB_ADIC_MEDICAMENTO_TOMADO_PELO_PAI  PROB_ADIC_SUPERDOSE  PROB_ADIC_USO_INCORRETO  PROB_ADIC_USO_OFF_LABEL_USO_SEM_REGISTRO  \
# 0                                                  0                                          0                    0                        0                                         0   
# 1                                                  0                                          0                    0                        0                                         0   
# 2                                                  0                                          0                    0                        0                                         0   
#
#    INDICACAO_MEDDRA_REACAO_CHAVE  INDICACAO_RELATADA_NOTIFICADOR_INICIAL_REACAO_CHAVE  DOSE_TIPO_CHAVE  DOSE_TIPO_VALOR  DOSE_VALOR FREQUENCIA_DOSE POSOLOGIA  DURACAO_TIPO_CHAVE DURACAO_TIPO_VALOR  \
# 0                              0                                                  0                  1   MILLIGRAM (MG)      1000.0                      None                   0       DESCONHECIDO   
# 1                              0                                                  0                  1   MILLIGRAM (MG)        20.0                      None                   0       DESCONHECIDO   
# 2                              0                                                  0                  2  MILLILITRE (ML)       106.0                      None                   0       DESCONHECIDO   
#
#    DURACAO_VALOR INICIO_ADMINISTRACAO FIM_ADMINISTRACAO  FORMA_FARMACEUTICA_CHAVE  VIA_ADMINISTRACAO_CHAVE  VIA_ADMINISTRACAO_MAE_PAI_CHAVE NUMELO_LOTE  ATUALIZADO  \
# 0            NaN           2023-01-10        2023-01-10                        14                        6                                5        None  2026-01-15   
# 1            NaN           2023-01-10        2023-01-10                        14                        6                                5        None  2026-01-15   
# 2            NaN           2023-01-10        2023-01-10                        16                        6                                5    22WC366B  2026-01-15   
#
#                                          HASH_BRONZE                                        HASH_SILVER  VERSION_ID  CURRENT_FLAG DATE_UPDATE                                          HASH_GOLD  
# 0  E8421CD05C810683B262026252DF85A8CB234025058ECE...  9343912bc6c30ced359a274ee48a1de9529194b812975b...           4          True  2026-08-07  64e1a72230a91f3c27d9865b347e2b4a3a5bb51cef1263...  
# 1  4AD3B12C405DB5047BDAF8B3178C11665390EA4407B788...  25d3a0c07204c5cfdd9c2340f816caa669f8ac34cf5d7e...           4          True  2026-08-07  9880b5a7698dc97cc6eac7f8e38cf3529fb5ed64f883ff...  
# 2  C2F0D1941A6EB562A55B581E0F847EAB15244D0E276E9A...  bbfba38c2def8d2420cc414be9e237568c95135a5d8e35...           4          True  2026-08-07  aa8fd90cf4adf58bc823b37554f1e9a9caca4644269b2a...

# ### fat_reacoes

# %% célula 15  (execução 10)
%%sql 
select * from fat_reacoes limit 2

# --- output ---
#   IDENTIFICACAO_NOTIFICACAO DATA_INICIO_HORA DATA_FINAL_HORA                                       REACAO_CHAVE  GRAVE_CHAVE GRAVE_VALOR  DESFECHO_CHAVE        DESFECHO_VALOR  DURACAO_TIPO_CHAVE  \
# 0       BR-ANVISA-300000004              NaT             NaT  SOC_10040785_HLGT_10014982_HLT_10049293_PT_100...            2         Não               3  Recuperado/Resolvido                   4   
# 1       BR-ANVISA-300000005       2018-11-22      2018-11-22  SOC_10015919_HLGT_10015917_HLT_10030032_PT_100...            1         Sim               3  Recuperado/Resolvido                   0   
#
#   DURACAO_TIPO_VALOR  DURACAO_VALOR  GRAVIDADE_RESULTADO_OBITO  GRAVIDADE_AMEACA_VIDA  GRAVIDADE_INCAPACIDADE  GRAVIDADE_HOSPITALIZACAO  GRAVIDADE_OUTRO_EFEITO  GRAVIDADE_ANOMALIA_CONGENITA  \
# 0                DIA            3.0                          0                      0                       0                         0                       0                             0   
# 1       DESCONHECIDO            NaN                          0                      0                       0                         0                       1                             0   
#
#    ATUALIZADO                                        HASH_BRONZE                                        HASH_SILVER                                          HASH_GOLD  
# 0  2026-01-15  e0102770fa7fe4e3e3f58fe5a3675e13fffd3dc4721c0b...  8c2bd3985ba5d5c3c38c928ced3769124a9f33ef2ff3f1...  31c44de9604bad343edd29f25f1317be500fc6836be77b...  
# 1  2026-01-15  21a5c47062a6ba174af4058e70e681ff97ba91db760676...  056c972fd2c77ca0bfdae5b5950379182d491a356c52dc...  a270a06c9ee9c3fc99b9f5b794a28c5768943f93594ab7...

# %% célula 16  (execução 11)
%%sql 
select * from fat_reacoes 
left join dim_soc_llt using (REACAO_CHAVE)
where IDENTIFICACAO_NOTIFICACAO = 'BR-ANVISA-300171130'

# --- output ---
#   IDENTIFICACAO_NOTIFICACAO DATA_INICIO_HORA DATA_FINAL_HORA                                       REACAO_CHAVE  GRAVE_CHAVE GRAVE_VALOR  DESFECHO_CHAVE        DESFECHO_VALOR  DURACAO_TIPO_CHAVE  \
# 0       BR-ANVISA-300171130       2023-01-10      2023-01-10  SOC_10017947_HLGT_10031013_HLT_10031021_PT_100...            2         Não               3  Recuperado/Resolvido                   0   
# 1       BR-ANVISA-300171130       2023-01-10      2023-01-10  SOC_10038738_HLGT_10046304_HLT_10028736_PT_100...            2         Não               3  Recuperado/Resolvido                   0   
# 2       BR-ANVISA-300171130       2023-01-10      2023-01-10  SOC_10038738_HLGT_10079101_HLT_10046313_PT_100...            2         Não               3  Recuperado/Resolvido                   0   
#
#   DURACAO_TIPO_VALOR  DURACAO_VALOR  GRAVIDADE_RESULTADO_OBITO  GRAVIDADE_AMEACA_VIDA  GRAVIDADE_INCAPACIDADE  GRAVIDADE_HOSPITALIZACAO  GRAVIDADE_OUTRO_EFEITO  GRAVIDADE_ANOMALIA_CONGENITA  \
# 0       DESCONHECIDO            NaN                          0                      0                       0                         0                       0                             0   
# 1       DESCONHECIDO            NaN                          0                      0                       0                         0                       0                             0   
# 2       DESCONHECIDO            NaN                          0                      0                       0                         0                       0                             0   
#
#    ATUALIZADO                                        HASH_BRONZE                                        HASH_SILVER                                          HASH_GOLD PRIMARY_FLAG  SOC_CODE  \
# 0  2026-01-15  bc80540a7cbefd2aca595577b9eefb0b73bc6ecac48230...  7d21ef0b502c7bd709fc861d93e0c85ca914102ce072fe...  f9391ca3f8e4727802351af46704d4dd3c54cfe25be672...            Y  10017947   
# 1  2026-01-15  33cda90c040b2714862d636436c2f0105c1307a9b593d5...  2b5248a44f91e424536763f2b5b8b5bf7c487473ccf6cf...  9bd9cc8cca01201eaa92960d4019701a573d2a08d4bbee...            Y  10038738   
# 2  2026-01-15  8d89edb6a4354411417b35144154c636741cce9c0dc40f...  39211221f089be0ed8d56477b01240c96ba18fb8112d9c...  515bec7e4db47ec59691c1dd6830483334b2f8055a23d9...            Y  10038738   
#
#                                             SOC_NAME SOC_ABBREV PRIMARY_SOC HLGT_CODE                                          HLGT_NAME  HLT_CODE                                      HLT_NAME  \
# 0                       Distúrbios gastrointestinais      Gastr    10017947  10031013               Quadros clínicos de tecido mole oral  10031021         Sinais e sintomas em tecido mole oral   
# 1  Distúrbios respiratórios, torácicos e do media...       Resp    10038738  10046304  Distúrbios das vias aéreas superiores (excl. i...  10028736                Inflamações e congestão nasais   
# 2  Distúrbios respiratórios, torácicos e do media...       Resp    10038738  10079101            Sinais e sintomas do trato respiratório  10046313  Sinais e sintomas das vias aéreas superiores   
#
#     PT_CODE          PT_NAME  LLT_CODE             LLT_NAME  
# 0  10052894     Prurido oral  10052894         Prurido oral  
# 1  10028735  Congestão nasal  10028735      Congestão nasal  
# 2  10041232         Espirros  10041233  Espirros excessivos

# ### dim_soc_llt

# %% célula 18  (execução 12)
%%sql 
select * from dim_soc_llt limit 2

# --- output ---
#                                         REACAO_CHAVE PRIMARY_FLAG  SOC_CODE                                          SOC_NAME SOC_ABBREV PRIMARY_SOC HLGT_CODE  \
# 0  SOC_10005329_HLGT_10002086_HLT_10002042_PT_100...            Y  10005329  Distúrbios dos sistemas hematológico e linfático      Blood    10005329  10002086   
# 1  SOC_10005329_HLGT_10002086_HLT_10002042_PT_100...            Y  10005329  Distúrbios dos sistemas hematológico e linfático      Blood    10005329  10002086   
#
#                                      HLGT_NAME  HLT_CODE             HLT_NAME   PT_CODE                           PT_NAME  LLT_CODE                                LLT_NAME  
# 0  Anemias não hemolíticas e depressão medular  10002042  Anemiais carenciais  10002043  Anemia por deficiência de folato  10002043        Anemia por deficiência de folato  
# 1  Anemias não hemolíticas e depressão medular  10002042  Anemiais carenciais  10002043  Anemia por deficiência de folato  10002044  Anemia por deficiência de ácido fólico

# %% célula 19  (execução 13)
%%sql 
select COUNT(1),COUNT(DISTINCT REACAO_CHAVE) from dim_soc_llt limit 2

# --- output ---
#    count(1)  count(DISTINCT REACAO_CHAVE)
# 0    142785                        142785

# %% célula 20  (execução 15)
%%sql 
select ATC_CODE_LEVEL_4,ATC_CODE_LEVEL_5,min(PRINCIPIOS_ATIVOS_WHODRUG),max(PRINCIPIOS_ATIVOS_WHODRUG),count(1) as qt,max(IDENTIFICACAO_NOTIFICACAO)
FROM fat_medicamentos f
where (lower(PRINCIPIOS_ATIVOS_WHODRUG) like '%dipirona%'
or lower(PRINCIPIOS_ATIVOS_WHODRUG) like '%metamizol%'
or lower(NOME_MEDICAMENTO_WHODRUG) like '%dipirona%'
or lower(NOME_MEDICAMENTO_WHODRUG) like '%metamizol%') --and PRINCIPIOS_ATIVOS_WHODRUG like '%X000%'
group by 1,2
order by 1,2 desc
limit 20

# --- output ---
#   ATC_CODE_LEVEL_4 ATC_CODE_LEVEL_5                     min(PRINCIPIOS_ATIVOS_WHODRUG)                     max(PRINCIPIOS_ATIVOS_WHODRUG)     qt max(IDENTIFICACAO_NOTIFICACAO)
# 0            A03DB          A03DB04       BUTILBROMETO DE ESCOPOLAMINA_X000D_|DIPIRONA  HYOSCINE BUTYLBROMIDE|METAMIZOLE SODIUM MONOHY...   1033            BR-ANVISA-300411210
# 1            A03ED          N02BB02  CLORIDRATO DE ADIFENINA|DIPIRONA|CLORIDRATO DE...  CLORIDRATO DE ADIFENINA|DIPIRONA|CLORIDRATO DE...      1            BR-ANVISA-300333236
# 2            A04AD          A04AD01       BUTILBROMETO DE ESCOPOLAMINA_X000D_|DIPIRONA       BUTILBROMETO DE ESCOPOLAMINA_X000D_|DIPIRONA      2            BR-ANVISA-300294241
# 3            H02BX          H02AB02  DEXAMETHASONE SODIUM PHOSPHATE|HYDROXOCOBALAMI...  DEXAMETHASONE SODIUM PHOSPHATE|HYDROXOCOBALAMI...     24            BR-ANVISA-300160134
# 4            J01CE          J01CE09          DIPIRONA_X000D_|BENZILPENICILINA PROCAÍNA          DIPIRONA_X000D_|BENZILPENICILINA PROCAÍNA      1            BR-ANVISA-300268541
# 5            M03BA          M03BA02  CARISOPRODOL_X000D_|CIANOCOBALAMINA_X000D_|MET...  CARISOPRODOL|CYANOCOBALAMIN|METAMIZOLE|PYRIDOX...      7            BR-ANVISA-300205828
# 6            M03BB          M03BB02                      CHLORMEZANONE_X000D_|DIPIRONA                    CHLORMEZANONE|METAMIZOLE SODIUM      2            BR-ANVISA-300222380
# 7            M03BC          M03BC01  CAFEÍNA ANIDRA_X000D_|DIPIRONA_X000D_|CITRATO ...    CAFFEINE|METAMIZOLE SODIUM|ORPHENADRINE CITRATE    264            BR-ANVISA-300406972
# 8            N02BB          N02BB02  ADIPHENINE HYDROCHLORIDE|METAMIZOLE SODIUM|PRO...  ÁCIDO ASCÓRBICO_X000D_|MALEATO DE CLORFENIRAMI...  11766            BR-ANVISA-300411381
# 9            N02CA          N02CA01  CAFEÍNA ANIDRA_X000D_|MESILATO DE DI-HIDROERGO...  CAFFEINE|DIHYDROERGOTAMINE MESILATE|METAMIZOLE...     29            BR-ANVISA-300345515

# %% célula 21  (execução 18)
%%sql 
select ATC_CODE_LEVEL_4,ATC_CODE_LEVEL_5,ATC_LEVEL_5,count(1) as qt
FROM fat_medicamentos f
where (lower(PRINCIPIOS_ATIVOS_WHODRUG) like '%dipirona%'
or lower(PRINCIPIOS_ATIVOS_WHODRUG) like '%metamizol%'
or lower(NOME_MEDICAMENTO_WHODRUG) like '%dipirona%'
or lower(NOME_MEDICAMENTO_WHODRUG) like '%metamizol%') --and PRINCIPIOS_ATIVOS_WHODRUG like '%X000%'
group by 1,2,3
order by 3 desc
limit 20

# --- output ---
#    ATC_CODE_LEVEL_4 ATC_CODE_LEVEL_5                              ATC_LEVEL_5     qt
# 0             N02CA          N02CA01                N02CA01_Dihydroergotamine     17
# 1             N02CA          N02CA01               N02CA01_Di Hidroergotamine     12
# 2             N02BB          N02BB02                       N02BB02_Metamizole  11766
# 3             A03ED          N02BB02                       N02BB02_Metamizole      1
# 4             M03BC          M03BC01                     M03BC01_Orphenadrine    264
# 5             M03BB          M03BB02                    M03BB02_Chlormezanone      2
# 6             M03BA          M03BA02                     M03BA02_Carisoprodol      7
# 7             J01CE          J01CE09        J01CE09_Benzylpenicillin Procaine      1
# 8             H02BX          H02AB02                    H02AB02_Dexamethasone     24
# 9             A04AD          A04AD01                      A04AD01_Scopolamine      2
# 10            A03DB          A03DB04  A03DB04_Butylscopolamine And Analgesics   1033

# ### 6.1 Aplicacao de regras de negócio

# %% célula 23
%%sql
DROP TABLE IF EXISTS fat_analytics;

CREATE TABLE fat_analytics AS
WITH fat_med AS (
    SELECT
        f.IDENTIFICACAO_NOTIFICACAO,
        f.RELACAO_MEDICAMENTO_EVENTO_VALOR AS RELACAO_MEDICAMENTO_EVENTO,
        atc.ATC_CODE_LEVEL_4_LEVEL_NAME,
        CASE
            WHEN f.ATC_CODE_LEVEL_5 IN ('N02BB02', 'N02BB52', 'N02BB72')
            THEN f.ATC_LEVEL_5
            ELSE 'Outros'
        END AS ATC_LEVEL_5
    FROM fat_medicamentos f
    LEFT JOIN dim_atc AS atc
        ON f.ATC_CODE_LEVEL_4 = atc.ATC_CODE_LEVEL_4
       AND atc.ATC_LEVEL = 4
),
fat AS (
    SELECT
        strftime(TRY_CAST(dim.DATA_INCLUSAO_SISTEMA AS DATE), '%Y-%m') AS DATA_NOTIFICACAO,
        dim.IDENTIFICACAO_NOTIFICACAO AS ID,
        dim.UF_VALOR AS UF,
        dim.SEXO_VALOR AS SEXO,
        fat_med.ATC_LEVEL_5,
        fat_med.RELACAO_MEDICAMENTO_EVENTO,
        ds.LLT_NAME AS REACAO_LLT,
        ds.PT_NAME AS REACAO_PT
    FROM dim_notificacoes AS dim
    INNER JOIN fat_med
        ON dim.IDENTIFICACAO_NOTIFICACAO = fat_med.IDENTIFICACAO_NOTIFICACAO
    INNER JOIN fat_reacoes fr
        ON dim.IDENTIFICACAO_NOTIFICACAO = fr.IDENTIFICACAO_NOTIFICACAO
    LEFT JOIN dim_soc_llt ds
        ON ds.REACAO_CHAVE = fr.REACAO_CHAVE
)
SELECT DISTINCT *
FROM (
    SELECT *
    FROM fat
    WHERE ATC_LEVEL_5 <> 'Outros'
      AND RELACAO_MEDICAMENTO_EVENTO = 'SUSPEITO'

    UNION ALL

    SELECT *
    FROM fat AS a
    WHERE a.ATC_LEVEL_5 = 'Outros'
      AND a.ID NOT IN (
          SELECT b.ID
          FROM fat AS b
          WHERE b.ATC_LEVEL_5 <> 'Outros'
      )
);

# ### 6.2 Checagens

# %% célula 25
%%sql
select * from fat_analytics limit 5

# %% célula 26
%%sql
select ATC_LEVEL_5,count(*) as qt,count(distinct ID) as qt_notificacoes 
from fat_analytics 
group by ATC_LEVEL_5 
order by 1

# %% célula 27
%%sql
select id,count(1) from fat_analytics group by 1 having count(1) > 1 limit 2

# %% célula 28
%%sql 
select * from fat_analytics 
where id ='BR-ANVISA-300315256'

# ### 6.3 Persistindo a Base

# %% célula 30
%%sql df <<
select * from fat_analytics

# %% célula 31
from pathlib import Path

out_dir = Path('fat_analytical')
out_dir.mkdir(parents=True, exist_ok=True)
df.to_parquet(out_dir / 'fat_analytical.parquet', index=False)
