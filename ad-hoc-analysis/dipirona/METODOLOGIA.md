# Base de dipirona 2019–2025 — QA e instruções de uso

## Decisão temporal e limitações
Referência: **DATA_NOTIFICACAO**, de 2019-01-01 a 2025-12-31 inclusive, sem hierarquia de substituição.
O padrão DATA_NOTIFICACAO corresponde ao campo homônimo no dicionário do projeto.
DATA_INCLUSAO_SISTEMA e DATA_ULTIMA_ATUALIZACAO representam processos diferentes e não substituem datas ausentes.
O protocolo detalhado do TCC não foi fornecido: esta escolha conservadora deve constar da metodologia.
Há exclusões relevantes por ausência de DATA_NOTIFICACAO. Não interpretar a base como todas as notificações registradas no sistema no período.
O último ingresso observado na Gold é 2025-12-07: o intervalo solicitado vai até 31/12/2025, mas esta extração não comprova cobertura completa de dezembro de 2025.
Para estudar ingresso no sistema, executar separadamente com --date-field DATA_INCLUSAO_SISTEMA --output <outro diretório> e documentar a mudança de estimando.
A documentação oficial de dados abertos foi localizada, mas seu conteúdo não pôde ser recuperado nesta execução; não se presume equivalência oficial entre os campos.
O manual da Anvisa distingue campos de recebimento e informação mais recente, sem demonstrar o mapeamento exato à Gold.

```text
 notificacoes_dipirona_suspeita  sem_data_notificacao  por_data_notificacao  por_data_inclusao  por_ultima_atualizacao  divergencia_universo  datas_divergentes  anos_divergentes
                           6832                  2008                  4797               6822                    6821                  2025               4027               410
```

```text
                  campo  total  ausentes  invalidas  no_periodo     minima     maxima
       DATA_NOTIFICACAO 311134    152174          0      158022 1922-09-04 2211-01-01
  DATA_INCLUSAO_SISTEMA 311134         0          0      311017 2018-12-01 2025-12-07
DATA_ULTIMA_ATUALIZACAO 311134        70          0      310948 2018-12-01 2025-12-11
```


## Diagnóstico anterior à correção
A consulta antiga não exige dipirona no ramo Outros e esse ramo também não exige SUSPEITO.
Seu NOT IN exclui pelo identificador se houver qualquer código-alvo, inclusive concomitante.
O join por notificação multiplica medicamentos por reações, enquanto DISTINCT apaga diferenças clínicas não selecionadas.
DATA_INCLUSAO_SISTEMA era renomeada como DATA_NOTIFICACAO e o período não era filtrado.
Contagens abaixo reproduzem a seleção antiga antes do DISTINCT final, em toda a Gold; não são estimativas do TCC.
```text
 medicamentos_selecionados  notificacoes  sem_evidencia_textual  nao_suspeitos  linhas_join_reacoes
                    731542        308227                 724239         241075              2846683
```


## Identificação e classificação
ATC, nome e texto de princípios ativos geram candidatos. Somente princípio ativo com token reconhecido de dipirona/metamizol confirma inclusão.
Nenhum produto é incluído só porque compartilha notificação. Apenas SUSPEITO é elegível; INTERAÇÃO, CONCOMITANTE, DESCONHECIDO e MEDICAMENTO NÃO ADMINISTRADO permanecem fora e são auditados.
Novalgin/Novamin e outros nomes comerciais não são dicionário de composição: evidência exige o campo de princípios ativos.
Aliases e regras estão em base_analitica.py, com equivalências PT/EN observadas nos dados. Metamizol magnésico tem composição específica preservada; não é confundido com sal sódico.
Escopolamina com sal ausente mantém descrição própria. Termos não mapeados geram Revisar, não uma composição inventada.
As normalizações removem caixa/acentos, espaços e separadores | e _X000D_. Campos originais são preservados.
Limiar parametrizado: **50 notificações distintas por composição no período inteiro**.
Somente associações com frequência estritamente menor entram em Outras associações. Isolada nunca entra nesse grupo.
```text
tipo_dipirona                                                                              associacao_detalhada  notificacoes_distintas       grupo_medicamento
      Isolada                                                                                          Dipirona                    3395        Dipirona isolada
      Isolada                                                                    Dipirona (metamizol magnésico)                     738        Dipirona isolada
   Associação                                                           Dipirona + butilbrometo de escopolamina                     634 Dipirona + escopolamina
   Associação                                                                  Dipirona + cafeína + orfenadrina                      22      Outras associações
   Associação                                                                 Dipirona + cafeína + isometepteno                       9      Outras associações
   Associação                                                               Dipirona + cafeína + clorfeniramina                       6      Outras associações
   Associação                                                           Dipirona + cafeína + di-hidroergotamina                       5      Outras associações
   Associação                                                                Dipirona + adifenina + prometazina                       4      Outras associações
   Associação                                                       Dipirona + escopolamina (sal não informado)                       3      Outras associações
   Associação Dipirona + bromidrato de hiosciamina + butilbrometo de escopolamina + metilbrometo de homatropina                       1      Outras associações
   Associação                                                       Dipirona + clorfeniramina + ácido ascórbico                       1      Outras associações
```


## Grão, reações repetidas e junções
Uma linha = notificação × composição suspeita × assinatura de reação. Produtos diferentes da mesma composição são agregados antes do join.
Assinatura = chave LLT no SOC primário, datas/horas originais de início/fim, gravidade (código e valor), desfecho (código e valor), duração (código, unidade, valor) e seis flags individuais.
A chave MedDRA original contém SOC/HLGT/HLT/PT/LLT. Cada LLT tem um caminho primário único validado. Caminhos secundários são mapeados ao primário, sem apagar a proveniência.
Assinaturas clínicas diferentes do mesmo LLT são preservadas. Linhas indistinguíveis são agregadas explicitamente e sua multiplicidade permanece em n_reacoes_fonte.
Sem identificador de episódio clínico na fonte, não é possível afirmar se linhas indistinguíveis são duplicatas ou episódios repetidos. Os totais descrevem registros de reação agrupados, não episódios confirmados.
As datas são exibidas em ISO; a assinatura mantém a precisão temporal original.
Notificações sem reação são preservadas por left join com id_reacao vazio e tem_registro_reacao=False.
Gravidade/desfecho vêm exclusivamente da reação. Não se preenchem esses campos a partir da notificação.
Não há ligação produto–reação específica: cada composição suspeita se relaciona com as reações da notificação para descrição, sem atribuição causal individual.

## Como contar no Excel
Abrir o CSV UTF-8 com BOM, delimitador ponto e vírgula. Campo vazio representa ausência, nunca zero ou Não automaticamente.
Para tabela dinâmica, importar pelo Excel e adicionar ao Modelo de Dados para usar Contagem Distinta.
- Notificações: contagem distinta de id_notificacao.
- Reações: contagem distinta de id_reacao, excluindo vazios. Não somar n_reacoes_fonte na base principal.
- Notificações por grupo: contagem distinta de id_notificacao filtrada por grupo_medicamento.
- Múltiplas composições: a mesma notificação/reação pode aparecer em grupos diferentes. Totais por grupo podem se sobrepor.
- Total anual: notificações distintas por ano; anos são aditivos porque cada notificação tem uma data de referência.
- PT/SOC: uma notificação pode ter vários termos; notificações por termo não são aditivas. Reações por PT/SOC primário são aditivas ao usar id_reacao distinto e incluir sem codificação.
- Contagem de linhas mede combinações composição–reação, não notificações nem episódios clínicos.
Os resumos usam exatamente os identificadores da base principal, incluindo notificações sem reações quando aplicável.
Dados não permitem calcular incidência, risco ou confirmação de causalidade. O estudo é descritivo/exploratório.

## Auditoria do universo
```text
                                      etapa  registros  notificacoes
                                    01 Gold     311134        311134
                         02 Data no período     158022        158022
03 Dipirona confirmada (todos papéis/datas)      13129         12730
         04 Dipirona suspeita (todas datas)       7015          6845
                  05 Medicamentos elegíveis       4910          4797
                  06 Notificação/composição       4818          4797
                       07 Reações agrupadas       6801          4797
                           08 Linhas finais       6829          4797
```

Linhas de medicamentos sem correspondência na dimensão de notificações são excluídas, pois não têm atributos/data verificáveis. Por isso a etapa 04 pode superar o universo da auditoria temporal.
```text
           tabela  registros  notificacoes
     Medicamentos      12671          2614
          Reações      66821         27657
Dipirona suspeita         16            13
```

```text
 notificacoes_multiplos_suspeitos  notificacoes_multiplas_composicoes  notificacoes_multiplas_reacoes  assinaturas_reacao_repetidas  linhas_reacao_agregadas  reacoes_sem_meddra  notificacoes_sem_reacao  composicoes_para_revisao  composicoes_agrupadas
                             1338                                  21                            1359                             3                      9.0                   7                        0                         0                      8
```

```text
 ano_notificacao  notificacoes_distintas  reacoes_distintas
            2019                     309                484
            2020                     627                854
            2021                     731                988
            2022                     778               1113
            2023                     869               1178
            2024                     790               1093
            2025                     693               1091
```

```text
      grupo_medicamento  notificacoes_distintas  composicoes  reacoes_distintas
       Dipirona isolada                    4133            2               5807
Dipirona + escopolamina                     634            1                927
     Outras associações                      51            8                 95
```


## Verificações executadas
```text
                                                        teste resultado
                              PK notificação única e não nula        OK
                                Chave MedDRA única e não nula        OK
                                  Um caminho primário por LLT        OK
                            Snapshot de medicamentos corrente        OK
                      Datas dentro de 2019–2025, sem fallback        OK
       Todo incluído tem evidência na composição e é suspeito        OK
Todos os candidatos textuais de composição foram reconhecidos        OK
                          Nenhuma associação excluída por ATC        OK
                        Exclusividade de tipos por composição        OK
                            Limiar usa notificações distintas        OK
      Outras associações respeita limiar e não inclui isolada        OK
                                         Grão principal único        OK
                              Join tem cardinalidade prevista        OK
                       SOC/PT preservados do caminho primário        OK
                               Consistência soc_code/soc_name        OK
                                 Consistência pt_code/pt_name        OK
                                           ID de reação único        OK
                 Chaves MedDRA não nulas encontram a dimensão        OK
                       Caso de dipirona concomitante excluído        OK
                  Totais anuais contam notificações distintas        OK
       CSV relido: todas as células não temporais preservadas        OK
                            CSV relido: datas ISO preservadas        OK
                                            CSV UTF-8 com BOM        OK
```


## Reprodutibilidade e arquivos
Executar da raiz: `.venv/bin/python ad-hoc-analysis/dipirona/base_analitica.py`.
O notebook 2_base_analitica_dipirona.ipynb contém as dez etapas e chama as mesmas funções.
O notebook original e seus exports anteriores são preservados.
CSV principal: fat_analytical_dipirona_2019_2025.csv. Dicionário: dicionario_dados.csv.
Auditorias: fontes, esquemas, legado, datas, sensibilidade_datas, excluidos_data, papeis, papeis_dipirona,
mapa_composicoes, candidatos_revisao, associacoes_fora_n02bb, frequencias_associacao,
auditoria_medicamentos (uma linha fonte elegível), auditoria_reacoes (uma assinatura por linha), fluxo, órfãos, multiplicidades, testes.
Manifesto inclui parâmetros e SHA-256 dos cinco Parquet e do CSV. Fontes não são modificadas.
Não se exportam nome, data de nascimento ou identificador de paciente; apenas identificadores técnicos públicos.

## Referências
- Dicionário local: docs/data_dictionary.md; ERD: docs/erd.md, lidos antes da implementação.
- [Documentação de dados abertos da Anvisa](https://dados.anvisa.gov.br/dados/Documentacao_e_Dicionario_de_Dados_Farmacovigilancia.pdf) (localizada; conteúdo não recuperado).
- [Manual VigiMed Empresas](https://www.gov.br/anvisa/pt-br/assuntos/fiscalizacao-e-monitoramento/notificacoes/vigimed/manual-de-uso-do-vigimed-empresa.pdf).
