"""Base descritiva de dipirona. Executar com o Python do ambiente do projeto.

Não modifica a camada Gold. DuckDB executa filtros e joins; pandas exporta CSV.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import unicodedata

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES = ('dim_notificacoes', 'fat_medicamentos', 'fat_reacoes', 'dim_soc_llt', 'dim_atc')
FLAGS = {
    'GRAVIDADE_RESULTADO_OBITO': ('gravidade_obito', 'Óbito'),
    'GRAVIDADE_AMEACA_VIDA': ('gravidade_ameaca_vida', 'Ameaça à vida'),
    'GRAVIDADE_INCAPACIDADE': ('gravidade_incapacidade', 'Incapacidade'),
    'GRAVIDADE_HOSPITALIZACAO': ('gravidade_hospitalizacao', 'Hospitalização'),
    'GRAVIDADE_OUTRO_EFEITO': ('gravidade_outro_efeito', 'Outro efeito clinicamente significativo'),
    'GRAVIDADE_ANOMALIA_CONGENITA': ('gravidade_anomalia_congenita', 'Anomalia congênita'),
}


def normalize(value):
    value = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', value.replace('_X000D_', '|')).strip()


DIPIRONA = {
    'DIPIRONA', 'DIPIRONA MONOIDRATADA', 'METAMIZOL', 'METAMIZOLE',
    'METAMIZOLE SODIUM', 'METAMIZOLE MONOHYDRATE', 'METAMIZOLE SODIUM MONOHYDRATE',
}
ALIASES = {}
for label, values in {
    'Dipirona': DIPIRONA,
    'Dipirona (metamizol magnésico)': {'METAMIZOL DE MAGNESIO', 'METAMIZOLE MAGNESIUM'},
    'butilbrometo de escopolamina': {'HYOSCINE BUTYLBROMIDE', 'BUTILBROMETO DE ESCOPOLAMINA'},
    'escopolamina (sal não informado)': {'HYOSCINE', 'HIOSCINA'},
    'cafeína': {'CAFFEINE', 'CAFEINA ANIDRA'},
    'orfenadrina': {'ORPHENADRINE CITRATE', 'CITRATO DE ORFENADRINA'},
    'adifenina': {'ADIPHENINE', 'ADIPHENINE HYDROCHLORIDE', 'CLORIDRATO DE ADIFENINA'},
    'prometazina': {'PROMETHAZINE', 'PROMETHAZINE HYDROCHLORIDE', 'CLORIDRATO DE PROMETAZINA'},
    'dexametasona': {'DEXAMETHASONE SODIUM PHOSPHATE'},
    'hidroxocobalamina': {'HYDROXOCOBALAMIN', 'HYDROXOCOBALAMIN HYDROCHLORIDE'},
    'di-hidroergotamina': {'DIHYDROERGOTAMINE MESILATE', 'MESILATO DE DI-HIDROERGOTAMINA'},
    'isometepteno': {'ISOMETHEPTENE', 'ISOMETHEPTENE MUCATE', 'ISOMETHEPTENE HYDROCHLORIDE', 'MUCATO DE ISOMETEPTENO', 'CLORIDRATO DE ISOMETEPTENO'},
    'clorfeniramina': {'CHLORPHENAMINE MALEATE', 'MALEATO DE CLORFENIRAMINA'},
    'carisoprodol': {'CARISOPRODOL'},
    'cianocobalamina': {'CYANOCOBALAMIN', 'CIANOCOBALAMINA'},
    'piridoxina': {'PYRIDOXINE', 'PYRIDOXINE HYDROCHLORIDE'},
    'tiamina': {'THIAMINE', 'THIAMINE HYDROCHLORIDE', 'TIAMINA'},
    'metilbrometo de homatropina': {'HOMATROPINE METHYLBROMIDE', 'METILBROMETO DE HOMATROPINA'},
    'bromidrato de hiosciamina': {'HYOSCYAMINE HYDROBROMIDE', 'BROMIDRATO DE HIOSCIAMINA'},
    'ácido ascórbico': {'ASCORBIC ACID', 'ACIDO ASCORBICO'},
    'benzilpenicilina procaína': {'BENZILPENICILINA PROCAINA'},
    'clordiazepóxido': {'CHLORDIAZEPOXIDE'},
    'nicotinato de teofilina': {'THEOPHYLLINE NICOTINATE'},
    'clormezanona': {'CHLORMEZANONE'},
}.items():
    ALIASES.update({normalize(v): label for v in values})


def classify(value):
    """Somente composição declarada confirma inclusão; ATC/nome geram candidatos."""
    tokens = sorted(set(t.strip() for t in re.split(r'[|;+]', normalize(value)) if t.strip()))
    has_dip = any(ALIASES.get(t, '').startswith('Dipirona') for t in tokens)
    unknown = [t for t in tokens if t not in ALIASES]
    ambiguous = bool(unknown) or not has_dip
    components = sorted({ALIASES.get(t, t) for t in tokens}, key=lambda s: (not s.startswith('Dipirona'), s))
    detail = ' + '.join(components) if has_dip else ''
    kind = ('Revisar' if ambiguous else ('Isolada' if len(components) == 1 else 'Associação'))
    return has_dip, kind, detail, ambiguous


def group_name(kind, detail, frequency, threshold):
    if kind == 'Revisar':
        return 'Revisar classificação'
    if kind == 'Isolada':
        return 'Dipirona isolada'
    if frequency < threshold:
        return 'Outras associações'
    if detail == 'Dipirona + butilbrometo de escopolamina':
        return 'Dipirona + escopolamina'
    return detail


class Study:
    def __init__(self, root=ROOT, threshold=50, date_field='DATA_NOTIFICACAO', output=None):
        if threshold < 1:
            raise ValueError('O limite deve ser positivo.')
        if date_field not in ('DATA_NOTIFICACAO', 'DATA_INCLUSAO_SISTEMA'):
            raise ValueError('Data de referência não autorizada.')
        self.root, self.threshold, self.date_field = Path(root), threshold, date_field
        self.output = Path(output) if output else self.root / 'ad-hoc-analysis/dipirona/output'
        self.c = duckdb.connect()
        self.checks = []
        self.reports = {}

    def df(self, sql):
        return self.c.sql(sql).df()

    def scalar(self, sql):
        return self.c.sql(sql).fetchone()[0]

    def check(self, name, condition):
        self.checks.append({'teste': name, 'resultado': 'OK' if condition else 'FALHOU'})
        if not condition:
            raise AssertionError(name)

    def load(self):
        for table in TABLES:
            path = self.root / f'data/03_gold/{table}/{table}.parquet'
            self.c.read_parquet(str(path)).create_view(table)
        self.c.execute("CREATE MACRO norm(x) AS trim(regexp_replace(upper(strip_accents(replace(coalesce(x,''),'_X000D_','|'))), '\\s+', ' ', 'g'))")
        self.c.execute("CREATE MACRO in_period(x) AS try_cast(x AS DATE) BETWEEN DATE '2019-01-01' AND DATE '2025-12-31'")
        self.check('PK notificação única e não nula', self.scalar('select count(*)=count(distinct IDENTIFICACAO_NOTIFICACAO) from dim_notificacoes'))
        self.check('Chave MedDRA única e não nula', self.scalar('select count(*)=count(distinct REACAO_CHAVE) from dim_soc_llt'))
        self.check('Um caminho primário por LLT', self.scalar("select count(*)=count(distinct LLT_CODE) from dim_soc_llt where PRIMARY_FLAG='Y'"))
        self.check('Snapshot de medicamentos corrente', self.scalar('select bool_and(CURRENT_FLAG) from fat_medicamentos'))

    def diagnose(self):
        self.reports['esquemas'] = pd.concat([self.df(f'describe {t}').assign(tabela=t) for t in TABLES])
        self.reports['fontes'] = pd.DataFrame([
            {'tabela': t, 'linhas': self.scalar(f'select count(*) from {t}'),
             'chaves_distintas': self.scalar(f"select count(distinct {'IDENTIFICACAO_NOTIFICACAO' if t in TABLES[:3] else 'REACAO_CHAVE' if t=='dim_soc_llt' else 'ATC_CODE_LEVEL_4'}) from {t}")}
            for t in TABLES])
        self.reports['datas'] = pd.concat([self.df(f"""select '{f}' campo, count(*) total,
            count(*) filter(where {f} is null) ausentes,
            count(*) filter(where {f} is not null and try_cast({f} as date) is null) invalidas,
            count(*) filter(where in_period({f})) no_periodo,
            min(try_cast({f} as date)) minima,max(try_cast({f} as date)) maxima
            from dim_notificacoes""") for f in ('DATA_NOTIFICACAO', 'DATA_INCLUSAO_SISTEMA', 'DATA_ULTIMA_ATUALIZACAO')])
        self.reports['papeis'] = self.df('select RELACAO_MEDICAMENTO_EVENTO_VALOR papel,count(*) registros,count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes from fat_medicamentos group by 1')
        # Reprodução literal da seleção antiga, antes do DISTINCT final e sem ler outputs salvos.
        self.c.execute("""create temp table legado as
            with med as (select *, ATC_CODE_LEVEL_5 in ('N02BB02','N02BB52','N02BB72') alvo from fat_medicamentos),
            ids as (select distinct IDENTIFICACAO_NOTIFICACAO from med where alvo)
            select m.* from med m where (alvo and RELACAO_MEDICAMENTO_EVENTO_VALOR='SUSPEITO')
                or (not coalesce(alvo,false) and not exists (select 1 from ids where ids.IDENTIFICACAO_NOTIFICACAO=m.IDENTIFICACAO_NOTIFICACAO))""")
        self.reports['legado'] = self.df("""select count(*) medicamentos_selecionados,
            count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes,
            count(*) filter(where not regexp_matches(norm(PRINCIPIOS_ATIVOS_WHODRUG),'DIPIRON|METAMIZ')) sem_evidencia_textual,
            count(*) filter(where RELACAO_MEDICAMENTO_EVENTO_VALOR<>'SUSPEITO') nao_suspeitos,
            (select count(*) from legado join fat_reacoes using(IDENTIFICACAO_NOTIFICACAO)) linhas_join_reacoes
            from legado""")

    def identify(self):
        self.c.execute("""create temp table candidatos as select *,
            regexp_matches(norm(PRINCIPIOS_ATIVOS_WHODRUG),'(^|[^A-Z])(DIPIRONA|METAMIZOLE?|METAMIZOL)([^A-Z]|$)') evidencia_textual
            from fat_medicamentos where regexp_matches(norm(concat_ws(' ',PRINCIPIOS_ATIVOS_WHODRUG,NOME_MEDICAMENTO_WHODRUG,ATC_LEVEL_5)), 'DIPIRON|METAMIZ')
            or ATC_CODE_LEVEL_5 in ('N02BB02','N02BB52','N02BB72') or ATC_CODE_LEVEL_4='N02BB'""")

    def normalize_actives(self):
        mapping = self.df('select distinct PRINCIPIOS_ATIVOS_WHODRUG from candidatos')
        rows = [classify(v) for v in mapping.PRINCIPIOS_ATIVOS_WHODRUG]
        for i, name in enumerate(['confirmado','tipo_dipirona','associacao_detalhada','revisar_classificacao']):
            mapping[name] = [r[i] for r in rows]
        self.c.register('mapa_composicoes', mapping)
        self.c.execute('''create temp table identificados as select m.*, p.* exclude(PRINCIPIOS_ATIVOS_WHODRUG)
            from candidatos m join mapa_composicoes p on m.PRINCIPIOS_ATIVOS_WHODRUG is not distinct from p.PRINCIPIOS_ATIVOS_WHODRUG''')
        self.reports['mapa_composicoes'] = mapping
        self.reports['candidatos_revisao'] = self.df('''select IDENTIFICACAO_NOTIFICACAO id_notificacao,HASH_GOLD id_medicamento_fonte,
            NOME_MEDICAMENTO_WHODRUG,PRINCIPIOS_ATIVOS_WHODRUG,ATC_CODE_LEVEL_4,ATC_CODE_LEVEL_5,ATC_LEVEL_5,
            RELACAO_MEDICAMENTO_EVENTO_VALOR,confirmado,tipo_dipirona,associacao_detalhada,revisar_classificacao
            from identificados where not confirmado or revisar_classificacao''')
        self.reports['papeis_dipirona'] = self.df('select RELACAO_MEDICAMENTO_EVENTO_VALOR papel,count(*) registros,count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes from identificados where confirmado group by 1')

    def classify_groups(self):
        self.c.execute(f'''create temp table elegiveis as select m.* from identificados m
            join dim_notificacoes n using(IDENTIFICACAO_NOTIFICACAO)
            where confirmado and norm(m.RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO'
            and in_period(n.{self.date_field})''')
        freq = self.df('''select tipo_dipirona,associacao_detalhada,
            count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes_distintas
            from elegiveis group by 1,2 order by 3 desc,2''')
        freq['grupo_medicamento'] = [group_name(r.tipo_dipirona,r.associacao_detalhada,r.notificacoes_distintas,self.threshold) for r in freq.itertuples()]
        self.c.register('frequencias',freq)
        self.reports['frequencias_associacao'] = freq

    def build(self):
        # Agrega produtos de mesma composição ANTES do join a reações.
        self.c.execute('''create temp table medicamentos as select IDENTIFICACAO_NOTIFICACAO id_notificacao,
            m.tipo_dipirona,m.associacao_detalhada,f.grupo_medicamento,f.notificacoes_distintas frequencia_associacao,
            bool_or(m.revisar_classificacao) revisar_classificacao,count(*) n_medicamentos_fonte,
            string_agg(distinct m.NOME_MEDICAMENTO_WHODRUG,' || ' order by m.NOME_MEDICAMENTO_WHODRUG) medicamento_original,
            string_agg(distinct m.PRINCIPIOS_ATIVOS_WHODRUG,' || ' order by m.PRINCIPIOS_ATIVOS_WHODRUG) principio_ativo_original,
            string_agg(distinct m.ATC_CODE_LEVEL_4,' || ' order by m.ATC_CODE_LEVEL_4) atc_code_level_4,
            string_agg(distinct m.ATC_CODE_LEVEL_5,' || ' order by m.ATC_CODE_LEVEL_5) atc_code_level_5,
            string_agg(distinct m.ATC_LEVEL_5,' || ' order by m.ATC_LEVEL_5) atc_level_5_original,
            string_agg(distinct m.HASH_GOLD,' || ' order by m.HASH_GOLD) ids_medicamentos_fonte
            from elegiveis m join frequencias f using(tipo_dipirona,associacao_detalhada) group by all''')
        clinical = ['DATA_INICIO_HORA','DATA_FINAL_HORA','GRAVE_CHAVE','GRAVE_VALOR','DESFECHO_CHAVE','DESFECHO_VALOR','DURACAO_TIPO_CHAVE','DURACAO_TIPO_VALOR','DURACAO_VALOR'] + list(FLAGS)
        cols = ','.join('r.'+x for x in clinical)
        # Só o SOC primário é usado, preservando a chave original em auditoria.
        self.c.execute(f'''create temp table reacoes as with agrupadas as (
            select r.IDENTIFICACAO_NOTIFICACAO id_notificacao,
            coalesce(p.REACAO_CHAVE,r.REACAO_CHAVE) reacao_chave,
            p.SOC_CODE soc_code,p.SOC_NAME soc_name,p.PT_CODE pt_code,p.PT_NAME pt_name,
            p.LLT_CODE llt_code,p.LLT_NAME llt_name,{cols},count(*) n_reacoes_fonte,
            string_agg(distinct r.HASH_GOLD,' || ' order by r.HASH_GOLD) ids_reacoes_fonte,
            string_agg(distinct r.REACAO_CHAVE,' || ' order by r.REACAO_CHAVE) chaves_reacoes_originais
            from fat_reacoes r left join dim_soc_llt d using(REACAO_CHAVE)
            left join dim_soc_llt p on p.LLT_CODE=d.LLT_CODE and p.PRIMARY_FLAG='Y'
            where exists(select 1 from medicamentos m where m.id_notificacao=r.IDENTIFICACAO_NOTIFICACAO)
            group by all)
            select md5(to_json(struct_pack(id:=id_notificacao,termo:=reacao_chave,
                {','.join(x+':='+x for x in clinical)}))) id_reacao, * from agrupadas''')
        flags = ','.join(f'r.{src} {alias}' for src,(alias,_) in FLAGS.items())
        criteria = ','.join(f"case when r.{src}=1 then '{label}' end" for src,(_,label) in FLAGS.items())
        self.c.execute(f'''create temp table analitica as select m.id_notificacao,
            year(n.{self.date_field})::integer ano_notificacao,cast(n.{self.date_field} as date) data_notificacao,
            '{self.date_field}' fonte_data_referencia,cast(n.DATA_NOTIFICACAO as date) data_notificacao_original,
            cast(n.DATA_INCLUSAO_SISTEMA as date) data_inclusao_sistema,
            cast(n.DATA_ULTIMA_ATUALIZACAO as date) data_ultima_atualizacao,
            n.UF_VALOR uf,n.SEXO_VALOR sexo,n.GRUPO_IDADE_VALOR faixa_etaria,
            n.TIPO_ENTRADA_VIGIMED_VALOR tipo_entrada_vigimed,n.NOTIFICADOR_VALOR tipo_notificador,
            m.* exclude(id_notificacao),m.medicamento_original medicamento_suspeito,
            m.principio_ativo_original principio_ativo,'SUSPEITO' relacao_medicamento_evento,
            r.id_reacao,r.reacao_chave,r.soc_code,r.soc_name,r.pt_code,r.pt_name,r.llt_code,r.llt_name,
            r.GRAVE_VALOR grave,nullif(concat_ws(' | ',{criteria}),'') criterio_gravidade,
            {flags},r.DESFECHO_VALOR desfecho_notificador,
            cast(r.DATA_INICIO_HORA as date) data_inicio_reacao,cast(r.DATA_FINAL_HORA as date) data_fim_reacao,
            r.DURACAO_TIPO_VALOR duracao_reacao_unidade,r.DURACAO_VALOR duracao_reacao_valor,
            r.n_reacoes_fonte,r.ids_reacoes_fonte,r.chaves_reacoes_originais,
            r.id_reacao is not null tem_registro_reacao
            from medicamentos m join dim_notificacoes n on n.IDENTIFICACAO_NOTIFICACAO=m.id_notificacao
            left join reacoes r on r.id_notificacao=m.id_notificacao''')

    def validate(self):
        self.check('Datas dentro de 2019–2025, sem fallback',self.scalar('select bool_and(in_period(data_notificacao)) from analitica'))
        self.check('Todo incluído tem evidência na composição e é suspeito', self.scalar("select bool_and(confirmado and evidencia_textual and norm(RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO') from elegiveis"))
        self.check('Todos os candidatos textuais de composição foram reconhecidos',self.scalar('select count(*)=0 from identificados where evidencia_textual and not confirmado'))
        self.check('Nenhuma associação excluída por ATC', self.scalar(f'''select count(*)=0 from identificados m join dim_notificacoes n using(IDENTIFICACAO_NOTIFICACAO)
            where confirmado and norm(m.RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO' and in_period(n.{self.date_field})
            and not exists(select 1 from elegiveis e where e.HASH_GOLD=m.HASH_GOLD)'''))
        self.check('Exclusividade de tipos por composição', self.scalar('select count(*)=0 from (select associacao_detalhada from medicamentos group by 1 having count(distinct tipo_dipirona)>1)'))
        self.check('Limiar usa notificações distintas', self.scalar('''select count(*)=0 from frequencias f where notificacoes_distintas <>
            (select count(distinct IDENTIFICACAO_NOTIFICACAO) from elegiveis e where e.associacao_detalhada=f.associacao_detalhada)'''))
        self.check('Outras associações respeita limiar e não inclui isolada', self.scalar(f"select count(*)=0 from medicamentos where (grupo_medicamento='Outras associações') <> (tipo_dipirona='Associação' and frequencia_associacao<{self.threshold})"))
        self.check('Grão principal único', self.scalar('''select count(*)=0 from (select id_notificacao,associacao_detalhada,id_reacao from analitica group by all having count(*)>1)'''))
        self.check('Join tem cardinalidade prevista', self.scalar('select count(*) from analitica') == self.scalar('''select sum(greatest(1,coalesce(r.n,0))) from medicamentos m left join (select id_notificacao,count(*) n from reacoes group by 1) r using(id_notificacao)'''))
        self.check('SOC/PT preservados do caminho primário', self.scalar('''select count(*)=0 from analitica a join dim_soc_llt d on a.reacao_chave=d.REACAO_CHAVE
            where a.soc_code is distinct from d.SOC_CODE or a.soc_name is distinct from d.SOC_NAME or a.pt_code is distinct from d.PT_CODE or a.pt_name is distinct from d.PT_NAME or d.PRIMARY_FLAG<>'Y' '''))
        for code,name in [('soc_code','soc_name'),('pt_code','pt_name')]:
            self.check(f'Consistência {code}/{name}', self.scalar(f'select count(*)=0 from (select {code} from analitica where {code} is not null group by 1 having count(distinct {name})>1)'))
        self.check('ID de reação único',self.scalar('select count(*)=count(distinct id_reacao) from reacoes'))
        self.check('Chaves MedDRA não nulas encontram a dimensão',self.scalar('''select count(*)=0 from reacoes r
            left join dim_soc_llt d on r.reacao_chave=d.REACAO_CHAVE where r.reacao_chave is not null and d.REACAO_CHAVE is null'''))
        self.check('Caso de dipirona concomitante excluído',self.scalar("select count(*)=0 from analitica where id_notificacao='BR-ANVISA-300171130'"))

    def summarize(self):
        self.reports['resumo_notificacoes_ano'] = self.df('''select y.ano ano_notificacao,count(distinct a.id_notificacao) notificacoes_distintas,
            count(distinct a.id_reacao) reacoes_distintas from range(2019,2026) y(ano)
            left join analitica a on a.ano_notificacao=y.ano group by 1 order by 1''')
        self.check('Totais anuais contam notificações distintas',int(self.reports['resumo_notificacoes_ano'].notificacoes_distintas.sum()) == self.scalar('select count(distinct id_notificacao) from medicamentos'))
        self.reports['resumo_medicamentos'] = self.df('''select grupo_medicamento,count(distinct id_notificacao) notificacoes_distintas,
            count(distinct associacao_detalhada) composicoes,count(distinct id_reacao) reacoes_distintas
            from analitica group by 1 order by 2 desc''')
        self.reports['resumo_eventos_adversos'] = self.df('''select soc_code,soc_name,pt_code,pt_name,
            count(distinct id_notificacao) notificacoes_distintas,count(distinct id_reacao) reacoes_distintas
            from analitica where tem_registro_reacao group by all order by notificacoes_distintas desc,pt_code''')
        self.reports['fluxo'] = self.df(f'''select '01 Gold' etapa,count(*) registros,count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes from dim_notificacoes
            union all select '02 Data no período',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from dim_notificacoes where in_period({self.date_field})
            union all select '03 Dipirona confirmada (todos papéis/datas)',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from identificados where confirmado
            union all select '04 Dipirona suspeita (todas datas)',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from identificados where confirmado and norm(RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO'
            union all select '05 Medicamentos elegíveis',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from elegiveis
            union all select '06 Notificação/composição',count(*),count(distinct id_notificacao) from medicamentos
            union all select '07 Reações agrupadas',count(*),count(distinct id_notificacao) from reacoes
            union all select '08 Linhas finais',count(*),count(distinct id_notificacao) from analitica order by etapa''')
        self.reports['sensibilidade_datas'] = self.df('''with ids as (select distinct IDENTIFICACAO_NOTIFICACAO from identificados where confirmado and norm(RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO')
            select count(*) notificacoes_dipirona_suspeita,
            count(*) filter(where n.DATA_NOTIFICACAO is null) sem_data_notificacao,
            count(*) filter(where in_period(n.DATA_NOTIFICACAO)) por_data_notificacao,
            count(*) filter(where in_period(n.DATA_INCLUSAO_SISTEMA)) por_data_inclusao,
            count(*) filter(where in_period(n.DATA_ULTIMA_ATUALIZACAO)) por_ultima_atualizacao,
            count(*) filter(where coalesce(in_period(n.DATA_NOTIFICACAO),false)<>coalesce(in_period(n.DATA_INCLUSAO_SISTEMA),false)) divergencia_universo,
            count(*) filter(where cast(n.DATA_NOTIFICACAO as date)<>cast(n.DATA_INCLUSAO_SISTEMA as date)) datas_divergentes,
            count(*) filter(where year(n.DATA_NOTIFICACAO)<>year(n.DATA_INCLUSAO_SISTEMA)) anos_divergentes
            from dim_notificacoes n join ids using(IDENTIFICACAO_NOTIFICACAO)''')
        self.reports['orfaos'] = self.df('''select 'Medicamentos' tabela,count(*) registros,count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes
            from fat_medicamentos m where not exists(select 1 from dim_notificacoes n where n.IDENTIFICACAO_NOTIFICACAO=m.IDENTIFICACAO_NOTIFICACAO)
            union all select 'Reações',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from fat_reacoes r
            where not exists(select 1 from dim_notificacoes n where n.IDENTIFICACAO_NOTIFICACAO=r.IDENTIFICACAO_NOTIFICACAO)
            union all select 'Dipirona suspeita',count(*),count(distinct IDENTIFICACAO_NOTIFICACAO) from identificados m
            where confirmado and norm(RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO'
            and not exists(select 1 from dim_notificacoes n where n.IDENTIFICACAO_NOTIFICACAO=m.IDENTIFICACAO_NOTIFICACAO)''')
        self.reports['excluidos_data'] = self.df(f'''select distinct n.IDENTIFICACAO_NOTIFICACAO id_notificacao,
            cast(n.DATA_NOTIFICACAO as date) data_notificacao_original,cast(n.DATA_INCLUSAO_SISTEMA as date) data_inclusao_sistema,
            case when n.{self.date_field} is null then 'Ausente' else 'Fora do período' end motivo
            from dim_notificacoes n join identificados m using(IDENTIFICACAO_NOTIFICACAO)
            where confirmado and norm(m.RELACAO_MEDICAMENTO_EVENTO_VALOR)='SUSPEITO' and not coalesce(in_period(n.{self.date_field}),false)''')
        self.reports['associacoes_fora_n02bb'] = self.df("select ATC_CODE_LEVEL_4,ATC_CODE_LEVEL_5,associacao_detalhada,count(*) medicamentos,count(distinct IDENTIFICACAO_NOTIFICACAO) notificacoes from elegiveis where not coalesce(ATC_CODE_LEVEL_4='N02BB',false) group by all")
        self.reports['multiplicidades'] = self.df('''select
            (select count(*) from (select IDENTIFICACAO_NOTIFICACAO from fat_medicamentos where RELACAO_MEDICAMENTO_EVENTO_VALOR='SUSPEITO' and IDENTIFICACAO_NOTIFICACAO in (select id_notificacao from medicamentos) group by 1 having count(*)>1)) notificacoes_multiplos_suspeitos,
            (select count(*) from (select id_notificacao from medicamentos group by 1 having count(*)>1)) notificacoes_multiplas_composicoes,
            (select count(*) from (select id_notificacao from reacoes group by 1 having count(*)>1)) notificacoes_multiplas_reacoes,
            (select count(*) from reacoes where n_reacoes_fonte>1) assinaturas_reacao_repetidas,
            (select coalesce(sum(n_reacoes_fonte-1),0) from reacoes) linhas_reacao_agregadas,
            (select count(*) from reacoes where reacao_chave is null) reacoes_sem_meddra,
            (select count(distinct id_notificacao) from analitica where not tem_registro_reacao) notificacoes_sem_reacao,
            (select count(*) from medicamentos where revisar_classificacao) composicoes_para_revisao,
            (select count(*) from frequencias where grupo_medicamento='Outras associações') composicoes_agrupadas''')
        self.reports['auditoria_medicamentos'] = self.df('''select IDENTIFICACAO_NOTIFICACAO id_notificacao,HASH_GOLD id_medicamento_fonte,
            NOME_MEDICAMENTO_WHODRUG medicamento_original,PRINCIPIOS_ATIVOS_WHODRUG principio_ativo_original,
            ATC_CODE_LEVEL_4,ATC_CODE_LEVEL_5,ATC_LEVEL_5,RELACAO_MEDICAMENTO_EVENTO_VALOR,
            tipo_dipirona,associacao_detalhada,revisar_classificacao from elegiveis order by 1,2''')
        self.reports['auditoria_reacoes'] = self.df('select * from reacoes order by id_notificacao,id_reacao')

    def export(self):
        self.output.mkdir(parents=True,exist_ok=True)
        main = self.df('select * from analitica order by id_notificacao,associacao_detalhada,id_reacao')
        name = 'fat_analytical_dipirona_2019_2025.csv'
        main.to_csv(self.output/name,sep=';',encoding='utf-8-sig',index=False,date_format='%Y-%m-%d',na_rep='')
        reread = pd.read_csv(self.output/name,sep=';',encoding='utf-8-sig',dtype=str,keep_default_na=False)
        expected = main.fillna('').astype(str)
        # Datas são exportadas explicitamente em ISO; comparar todos os outros campos.
        non_dates = [x for x in main if not pd.api.types.is_datetime64_any_dtype(main[x])]
        self.check('CSV relido: todas as células não temporais preservadas',reread[non_dates].equals(expected[non_dates]))
        self.check('CSV relido: datas ISO preservadas',all(reread[x].equals(main[x].dt.strftime('%Y-%m-%d').fillna('')) for x in main if pd.api.types.is_datetime64_any_dtype(main[x])))
        self.check('CSV UTF-8 com BOM', (self.output/name).read_bytes()[:3]==b'\xef\xbb\xbf')
        descriptions = dictionary()
        self.reports['dicionario_dados'] = pd.DataFrame([{'coluna':col,'tipo':str(main[col].dtype),'descricao':descriptions[col],
            'ausente':'Campo vazio; não equivale a Não/zero','nivel': 'Reação' if col in REACTION_COLUMNS else 'Notificação/composição' if col in MED_COLUMNS else 'Notificação'} for col in main])
        self.reports['testes'] = pd.DataFrame(self.checks)
        for key,frame in self.reports.items():
            frame.to_csv(self.output/f'{key}.csv',sep=';',encoding='utf-8-sig',index=False,date_format='%Y-%m-%d',na_rep='')
        manifest = {'data_referencia':self.date_field,'limiar_associacoes':self.threshold,'periodo':['2019-01-01','2025-12-31'],
            'fontes':{t:hashlib.sha256((self.root/f'data/03_gold/{t}/{t}.parquet').read_bytes()).hexdigest() for t in TABLES},
            'sha256_csv':hashlib.sha256((self.output/name).read_bytes()).hexdigest(),
            'sha256_implementacao':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        (self.output/'manifesto.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        report = methodology(self)
        (self.output/'qa_relatorio.md').write_text(report,encoding='utf-8')
        return self.output/name


MED_COLUMNS = set('tipo_dipirona associacao_detalhada grupo_medicamento frequencia_associacao revisar_classificacao n_medicamentos_fonte medicamento_original principio_ativo_original atc_code_level_4 atc_code_level_5 atc_level_5_original ids_medicamentos_fonte medicamento_suspeito principio_ativo relacao_medicamento_evento'.split())
REACTION_COLUMNS = set('id_reacao reacao_chave soc_code soc_name pt_code pt_name llt_code llt_name grave criterio_gravidade desfecho_notificador data_inicio_reacao data_fim_reacao duracao_reacao_unidade duracao_reacao_valor n_reacoes_fonte ids_reacoes_fonte chaves_reacoes_originais tem_registro_reacao'.split()) | {v[0] for v in FLAGS.values()}


def dictionary():
    d = {
        'id_notificacao':'IDENTIFICACAO_NOTIFICACAO: identificador técnico público; contar valores distintos.',
        'ano_notificacao':'Ano da data de referência adotada; não é um total anual.',
        'data_notificacao':'Data de referência adotada, sem fallback; consultar fonte_data_referencia.',
        'fonte_data_referencia':'Nome exato da coluna Gold usada para seleção temporal.',
        'data_notificacao_original':'DATA_NOTIFICACAO original, sem substituição.',
        'data_inclusao_sistema':'DATA_INCLUSAO_SISTEMA original; não equivale à data da notificação.',
        'data_ultima_atualizacao':'DATA_ULTIMA_ATUALIZACAO original.',
        'uf':'UF_VALOR original da notificação.', 'sexo':'SEXO_VALOR original da notificação.',
        'faixa_etaria':'GRUPO_IDADE_VALOR original; não foi inferida idade individual.',
        'tipo_entrada_vigimed':'TIPO_ENTRADA_VIGIMED_VALOR original.',
        'tipo_notificador':'NOTIFICADOR_VALOR original.',
        'tipo_dipirona':'Isolada, Associação ou Revisar, conforme a composição do produto.',
        'associacao_detalhada':'Composição normalizada anterior ao agrupamento de raras; magnésio preservado.',
        'grupo_medicamento':'Categoria do TCC; associações abaixo do limiar viram Outras associações.',
        'frequencia_associacao':'Notificações distintas desta composição no período; não somar esta coluna.',
        'revisar_classificacao':'True sinaliza composição ambígua ou componente não mapeado.',
        'n_medicamentos_fonte':'Número de linhas Gold de medicamentos agregadas nesta notificação/composição; repete por reação.',
        'medicamento_original':'NOME_MEDICAMENTO_WHODRUG, valores originais únicos separados por ||.',
        'principio_ativo_original':'PRINCIPIOS_ATIVOS_WHODRUG, valores originais únicos separados por ||.',
        'atc_code_level_4':'ATC_CODE_LEVEL_4 original, valores únicos separados por ||; não usado para decidir composição.',
        'atc_code_level_5':'ATC_CODE_LEVEL_5 original inferido pela Gold, valores únicos separados por ||; pode ser inconsistente.',
        'atc_level_5_original':'ATC_LEVEL_5 original, valores únicos separados por ||.',
        'ids_medicamentos_fonte':'HASH_GOLD das linhas de medicamentos, separados por ||. Pareamento original em auditoria_medicamentos.csv.',
        'medicamento_suspeito':'Alias de medicamento_original.', 'principio_ativo':'Alias de principio_ativo_original.',
        'relacao_medicamento_evento':'Papel SUSPEITO na linha do medicamento; concomitantes excluídos.',
        'id_reacao':'MD5 determinístico de notificação, chave MedDRA canônica e atributos clínicos; contar distintos, sem somar por composição.',
        'reacao_chave':'Chave canônica do caminho SOC primário do LLT; original preservado em chaves_reacoes_originais.',
        'soc_code':'Código SOC do caminho primário MedDRA.', 'soc_name':'Descrição SOC da dimensão Gold.',
        'pt_code':'Código PT MedDRA.', 'pt_name':'Termo preferido da dimensão Gold.',
        'llt_code':'Código LLT MedDRA.', 'llt_name':'Termo LLT da dimensão Gold.',
        'grave':'GRAVE_VALOR da reação; não substituído pela gravidade da notificação.',
        'criterio_gravidade':'Critérios simultâneos com flag 1 concatenados; vazio não prova ausência de gravidade.',
        'desfecho_notificador':'DESFECHO_VALOR da reação; relato não confirma causalidade.',
        'data_inicio_reacao':'DATA_INICIO_HORA da reação, apresentada como data ISO.',
        'data_fim_reacao':'DATA_FINAL_HORA da reação, apresentada como data ISO.',
        'duracao_reacao_unidade':'DURACAO_TIPO_VALOR da reação.', 'duracao_reacao_valor':'DURACAO_VALOR da reação.',
        'n_reacoes_fonte':'Linhas Gold agregadas na mesma assinatura clínica, incluindo duplicatas/caminhos; não é contagem confirmada de episódios.',
        'ids_reacoes_fonte':'Hashes Gold originais únicos separados por ||; detalhes em auditoria_reacoes.csv.',
        'chaves_reacoes_originais':'Chaves de caminhos MedDRA originais únicas separadas por ||.',
        'tem_registro_reacao':'True se há reação na fonte; False preserva notificação sem reação no left join.',
    }
    d.update({alias:f'{src} da reação: 1=critério presente; 0=flag não marcada na fonte; vazio=ausente.' for src,(alias,_) in FLAGS.items()})
    return d


def methodology(s):
    def block(name):
        return '```text\n'+s.reports[name].to_string(index=False)+'\n```\n'
    return f'''# Base de dipirona 2019–2025 — QA e instruções de uso

## Decisão temporal e limitações
Referência: **{s.date_field}**, de 2019-01-01 a 2025-12-31 inclusive, sem hierarquia de substituição.
O padrão DATA_NOTIFICACAO corresponde ao campo homônimo no dicionário do projeto.
DATA_INCLUSAO_SISTEMA e DATA_ULTIMA_ATUALIZACAO representam processos diferentes e não substituem datas ausentes.
O protocolo detalhado do TCC não foi fornecido: esta escolha conservadora deve constar da metodologia.
Há exclusões relevantes por ausência de DATA_NOTIFICACAO. Não interpretar a base como todas as notificações registradas no sistema no período.
O último ingresso observado na Gold é {s.scalar('select max(cast(DATA_INCLUSAO_SISTEMA as date)) from dim_notificacoes')}: o intervalo solicitado vai até 31/12/2025, mas esta extração não comprova cobertura completa de dezembro de 2025.
Para estudar ingresso no sistema, executar separadamente com --date-field DATA_INCLUSAO_SISTEMA --output <outro diretório> e documentar a mudança de estimando.
A documentação oficial de dados abertos foi localizada, mas seu conteúdo não pôde ser recuperado nesta execução; não se presume equivalência oficial entre os campos.
O manual da Anvisa distingue campos de recebimento e informação mais recente, sem demonstrar o mapeamento exato à Gold.

{block('sensibilidade_datas')}
{block('datas')}

## Diagnóstico anterior à correção
A consulta antiga não exige dipirona no ramo Outros e esse ramo também não exige SUSPEITO.
Seu NOT IN exclui pelo identificador se houver qualquer código-alvo, inclusive concomitante.
O join por notificação multiplica medicamentos por reações, enquanto DISTINCT apaga diferenças clínicas não selecionadas.
DATA_INCLUSAO_SISTEMA era renomeada como DATA_NOTIFICACAO e o período não era filtrado.
Contagens abaixo reproduzem a seleção antiga antes do DISTINCT final, em toda a Gold; não são estimativas do TCC.
{block('legado')}

## Identificação e classificação
ATC, nome e texto de princípios ativos geram candidatos. Somente princípio ativo com token reconhecido de dipirona/metamizol confirma inclusão.
Nenhum produto é incluído só porque compartilha notificação. Apenas SUSPEITO é elegível; INTERAÇÃO, CONCOMITANTE, DESCONHECIDO e MEDICAMENTO NÃO ADMINISTRADO permanecem fora e são auditados.
Novalgin/Novamin e outros nomes comerciais não são dicionário de composição: evidência exige o campo de princípios ativos.
Aliases e regras estão em base_analitica.py, com equivalências PT/EN observadas nos dados. Metamizol magnésico tem composição específica preservada; não é confundido com sal sódico.
Escopolamina com sal ausente mantém descrição própria. Termos não mapeados geram Revisar, não uma composição inventada.
As normalizações removem caixa/acentos, espaços e separadores | e _X000D_. Campos originais são preservados.
Limiar parametrizado: **{s.threshold} notificações distintas por composição no período inteiro**.
Somente associações com frequência estritamente menor entram em Outras associações. Isolada nunca entra nesse grupo.
{block('frequencias_associacao')}

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
{block('fluxo')}
Linhas de medicamentos sem correspondência na dimensão de notificações são excluídas, pois não têm atributos/data verificáveis. Por isso a etapa 04 pode superar o universo da auditoria temporal.
{block('orfaos')}
{block('multiplicidades')}
{block('resumo_notificacoes_ano')}
{block('resumo_medicamentos')}

## Verificações executadas
{block('testes')}

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
'''


def run(root=ROOT, threshold=50, date_field='DATA_NOTIFICACAO', output=None):
    s = Study(root,threshold,date_field,output)
    for step in ('load','diagnose','identify','normalize_actives','classify_groups','build','validate','summarize'):
        getattr(s,step)()
    path = s.export()
    print(s.reports['fluxo'].to_string(index=False))
    print(s.reports['resumo_medicamentos'].to_string(index=False))
    print(path)
    return s


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threshold',type=int,default=50)
    parser.add_argument('--date-field',choices=['DATA_NOTIFICACAO','DATA_INCLUSAO_SISTEMA'],default='DATA_NOTIFICACAO')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    run(threshold=args.threshold,date_field=args.date_field,output=args.output)
