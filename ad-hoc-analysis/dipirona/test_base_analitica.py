"""Testes de regras e de cardinalidade com casos adversariais sintéticos.

Executar: .venv/bin/python -m unittest discover -s ad-hoc-analysis/dipirona -p 'test_*.py' -v
As verificações sobre dados reais também são executadas pelo notebook/script.
"""
import unittest

from base_analitica import FLAGS, Study, classify, group_name, normalize


class ClassificationTests(unittest.TestCase):
    def test_accents_separators_and_order(self):
        a = classify('cafeína anidra_X000D_|dipirona_X000D_|citrato de orfenadrina')
        b = classify('ORPHENADRINE CITRATE|METAMIZOLE SODIUM|CAFFEINE')
        self.assertEqual(a,b)
        self.assertEqual(a,(True,'Associação','Dipirona + cafeína + orfenadrina',False))

    def test_product_composition_only(self):
        self.assertFalse(classify('PARACETAMOL')[0])
        self.assertFalse(classify('NOVALGINA')[0])
        self.assertFalse(classify('DIPIRONAFAKE')[0])

    def test_ambiguous_never_arbitrary(self):
        self.assertEqual(classify('DIPIRONA|COMPONENTE DESCONHECIDO')[1],'Revisar')
        self.assertNotEqual(classify('METAMIZOLE MAGNESIUM')[2],classify('METAMIZOLE SODIUM')[2])
        self.assertNotEqual(classify('HYOSCINE|DIPIRONA')[2],classify('HYOSCINE BUTYLBROMIDE|DIPIRONA')[2])

    def test_threshold_boundary_and_isolated(self):
        self.assertEqual(group_name('Associação','Dipirona + cafeína',49,50),'Outras associações')
        self.assertEqual(group_name('Associação','Dipirona + cafeína',50,50),'Dipirona + cafeína')
        self.assertEqual(group_name('Isolada','Dipirona',1,50),'Dipirona isolada')
        self.assertEqual(normalize('  dipiróna   monoidratada  '),'DIPIRONA MONOIDRATADA')


class JoinTests(unittest.TestCase):
    def test_duplicates_roles_dates_and_multiple_compositions(self):
        # Duas linhas da mesma composição não podem duplicar uma reação.
        # Um concomitante sem suspeito dipirona e uma data ausente são excluídos.
        s=Study()
        c=s.c
        c.execute('''create table dim_notificacoes as select * from (values
            ('a',date '2020-01-01',date '2020-01-02'),
            ('b',date '2020-01-01',date '2020-01-02'),
            ('c',NULL::date,date '2020-01-02'),
            ('d',date '2018-12-31',date '2019-01-01'),
            ('e',date '2025-12-31',date '2025-12-31'),
            ('f',date '2026-01-01',date '2025-12-31'))
            t(IDENTIFICACAO_NOTIFICACAO,DATA_NOTIFICACAO,DATA_INCLUSAO_SISTEMA)''')
        c.execute('''create table identificados as select * from (values
            ('a','SUSPEITO',true,'Isolada','Dipirona',false,'m1'),
            ('a','SUSPEITO',true,'Isolada','Dipirona',false,'m2'),
            ('a','SUSPEITO',true,'Associação','Dipirona + cafeína',false,'m3'),
            ('a','SUSPEITO',false,'Revisar','Paracetamol',true,'m4'),
            ('b','CONCOMITANTE',true,'Isolada','Dipirona',false,'m5'),
            ('c','SUSPEITO',true,'Isolada','Dipirona',false,'m6'),
            ('d','SUSPEITO',true,'Isolada','Dipirona',false,'m7'),
            ('e','SUSPEITO',true,'Isolada','Dipirona',false,'m8'),
            ('f','SUSPEITO',true,'Isolada','Dipirona',false,'m9'))
            t(IDENTIFICACAO_NOTIFICACAO,RELACAO_MEDICAMENTO_EVENTO_VALOR,confirmado,tipo_dipirona,associacao_detalhada,revisar_classificacao,HASH_GOLD)''')
        c.execute("create macro norm(x) as upper(x)")
        c.execute("create macro in_period(x) as x between date '2019-01-01' and date '2025-12-31'")
        s.classify_groups()
        self.assertEqual(c.sql('select distinct IDENTIFICACAO_NOTIFICACAO from elegiveis order by 1').fetchall(),[('a',),('e',)])
        f=s.reports['frequencias_associacao'].set_index('associacao_detalhada')
        self.assertEqual(f.loc['Dipirona','notificacoes_distintas'],2)
        self.assertEqual(f.loc['Dipirona + cafeína','notificacoes_distintas'],1)
        # Completa o esquema e chama o build real, incluindo reação idêntica repetida.
        for name in ['UF_VALOR','SEXO_VALOR','GRUPO_IDADE_VALOR','TIPO_ENTRADA_VIGIMED_VALOR','NOTIFICADOR_VALOR']:
            c.execute(f'alter table dim_notificacoes add column {name} varchar')
        c.execute('alter table dim_notificacoes add column DATA_ULTIMA_ATUALIZACAO date')
        for name in ['NOME_MEDICAMENTO_WHODRUG','PRINCIPIOS_ATIVOS_WHODRUG','ATC_CODE_LEVEL_4','ATC_CODE_LEVEL_5','ATC_LEVEL_5']:
            c.execute(f'alter table elegiveis add column {name} varchar')
        c.execute("create table dim_soc_llt(REACAO_CHAVE varchar,LLT_CODE varchar,SOC_CODE varchar,SOC_NAME varchar,PT_CODE varchar,PT_NAME varchar,LLT_NAME varchar,PRIMARY_FLAG varchar)")
        c.execute("insert into dim_soc_llt values ('primaria','llt1','soc1','SOC','pt1','PT','LLT','Y'),('secundaria','llt1','soc2','Outro SOC','pt1','PT','LLT','N')")
        c.execute("create table fat_reacoes(IDENTIFICACAO_NOTIFICACAO varchar,REACAO_CHAVE varchar,HASH_GOLD varchar)")
        c.execute("insert into fat_reacoes values ('a','primaria','r1'),('a','primaria','r2'),('a','secundaria','r3')")
        for name, dtype in {
            'DATA_INICIO_HORA':'timestamp','DATA_FINAL_HORA':'timestamp',
            'GRAVE_CHAVE':'integer','GRAVE_VALOR':'varchar','DESFECHO_CHAVE':'integer','DESFECHO_VALOR':'varchar',
            'DURACAO_TIPO_CHAVE':'integer','DURACAO_TIPO_VALOR':'varchar','DURACAO_VALOR':'double',
            **{name:'integer' for name in FLAGS},
        }.items():
            c.execute(f'alter table fat_reacoes add column {name} {dtype}')
        s.build()
        result=s.df('select * from analitica')
        self.assertEqual(len(result),3)  # 2 composições x 1 assinatura + 1 sem reação
        self.assertEqual(result.id_reacao.nunique(),1)
        self.assertEqual(result.id_notificacao.nunique(),2)
        self.assertEqual(s.scalar('select n_reacoes_fonte from reacoes'),3)
        self.assertEqual(s.scalar('select soc_code from reacoes'),'soc1')
        c.close()


if __name__=='__main__':
    unittest.main()
