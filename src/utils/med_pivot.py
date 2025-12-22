"""
Função para desagrupar colunas com valores separados por pipe "|" ou padrões X000D.

As colunas podem ter valores agrupados usando diferentes padrões:
- Pipe simples: "|"
- X000D (com ou sem pipe antes): "|X000D", "X000D", "_X000D_"
- Variações: "_x000D_", "X000D_", "_X000D"
"""

import pandas as pd
import re
import hashlib
from typing import List, Union


def _normalizar_separadores(valor: str) -> str:
    """
    Normaliza diferentes padrões de separação para pipe simples.
    
    Padrões tratados:
    - "_x000D_" ou "_X000D_": removido completamente (substituído por "")
      Exemplos: "A_x000D_B" → "AB", "A_x000D_|B" → "A|B", "A|_x000D_B" → "A|B"
    - |X000D ou |x000D: convertido para pipe "|"
    - X000D| ou x000D|: convertido para pipe "|"
    - X000D_ ou x000D_: convertido para pipe "|"
    - _X000D ou _x000D: convertido para pipe "|"
    - X000D ou x000D (standalone): convertido para pipe "|"
    
    Parameters:
    -----------
    valor : str
        String com valores agrupados
        
    Returns:
    --------
    str
        String normalizada com pipes simples
    """
    if not valor or pd.isna(valor):
        return ''
    
    valor_str = str(valor)
    
    # PRIMEIRO: Remover "_x000D_" completamente (case-insensitive, com ou sem espaços)
    # Este padrão não é separador, é apenas caractere de controle a ser removido
    # Exemplos: "A_x000D_|B" → "A|B", "A|_x000D_B" → "A|B", "A_x000D_B" → "AB"
    # Padrão: underscore, espaços opcionais, X000D (case-insensitive), espaços opcionais, underscore
    valor_str = re.sub(r'_\s*[Xx]000[Dd]\s*_', '', valor_str, flags=re.IGNORECASE)
    
    # DEPOIS: Converter padrões X000D que são separadores para pipe "|"
    # Ordem importa: tratar padrões mais específicos primeiro
    
    # Padrões com pipe antes ou depois: |X000D ou X000D|
    valor_str = re.sub(r'\|\s*[Xx]000[Dd]', '|', valor_str, flags=re.IGNORECASE)
    valor_str = re.sub(r'[Xx]000[Dd]\s*\|', '|', valor_str, flags=re.IGNORECASE)
    
    # Padrões com underscore (mas não _x000D_ que já foi removido): _X000D ou X000D_
    valor_str = re.sub(r'_\s*[Xx]000[Dd]', '|', valor_str, flags=re.IGNORECASE)
    valor_str = re.sub(r'[Xx]000[Dd]\s*_', '|', valor_str, flags=re.IGNORECASE)
    
    # Padrão standalone (sem pipe ou underscore): X000D
    valor_str = re.sub(r'[Xx]000[Dd]', '|', valor_str, flags=re.IGNORECASE)
    
    # Limpar pipes duplicados e espaços ao redor
    valor_str = re.sub(r'\|\s*\|\s*', '|', valor_str)  # pipes duplicados com espaços
    valor_str = re.sub(r'\|{2,}', '|', valor_str)  # pipes duplicados (2 ou mais)
    valor_str = valor_str.strip('| ')  # remover pipes nas extremidades
    
    return valor_str


def desagrupar_colunas_pipe(
    df: pd.DataFrame, 
    colunas_agrupadas: List[str],
    manter_linhas_vazias: bool = False
) -> pd.DataFrame:
    """
    Desagrupa colunas que contêm valores separados por pipe "|" ou padrões X000D.
    Cria uma linha para cada valor na mesma posição, mantendo as demais colunas iguais.
    
    A função trata diferentes padrões de agrupamento:
    - Pipe simples: "A|B|C"
    - X000D como separador: "AX000DB" ou "A|X000DB" ou "A_X000DB" → "A|B"
    - "_x000D_" é removido completamente (não é separador): "A_x000D_B" → "AB"
    - Combinações: "A|X000DB|C" → "A|B|C"
    
    A função também cria automaticamente a coluna ATC_CODE_5_HASH antes do processamento,
    usando os valores ORIGINAIS (antes da limpeza) de:
    - IDENTIFICACAO_NOTIFICACAO
    - NOME_MEDICAMENTO_WHODRUG
    - ATC_CODE_5
    
    O ID é gerado usando hash SHA256 da concatenação desses valores, garantindo:
    - Consistência: mesmo valor sempre gera o mesmo hash
    - Limpeza: evita caracteres especiais problemáticos
    - Tamanho fixo: sempre 64 caracteres hexadecimais
    
    Isso permite rastrear quais linhas desagrupadas vieram da mesma linha original agrupada,
    pois todas terão o mesmo ATC_CODE_5_HASH.
    
    Exemplo:
    --------
    Se uma linha tem:
    - IDENTIFICACAO_NOTIFICACAO="BR-001"
    - NOME="A|B"
    - PRINCIPIOS="1|2"
    - CODIGO="X|Y"
    
    Serão criadas 2 linhas:
    - (BR-001, A, 1, X, ATC_CODE_5_HASH="abc123...")  # hash SHA256
    - (BR-001, B, 2, Y, ATC_CODE_5_HASH="abc123...")  # mesmo hash (mesma origem)
    
    Se os tamanhos forem diferentes, o último valor é repetido:
    - NOME="A|B|C"
    - PRINCIPIOS="1|2"
    
    Resultado:
    - (A, 1)
    - (B, 2)
    - (C, 2)  # último valor repetido
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame com dados agrupados
    colunas_agrupadas : list
        Lista com nomes das colunas que devem ser desagrupadas
    manter_linhas_vazias : bool, default False
        Se True, mantém linhas onde todas as colunas agrupadas estão vazias
        
    Returns:
    --------
    pd.DataFrame
        DataFrame desagrupado com uma linha para cada valor separado.
        Inclui a coluna ATC_CODE_5_HASH para rastrear linhas da mesma origem.
        
    Raises:
    ------
    ValueError
        Se nenhuma coluna válida for fornecida
    """
    if df.empty:
        return df.copy()
    
    df_result = df.copy()
    colunas_agrupadas = [col for col in colunas_agrupadas if col in df_result.columns]
    
    if not colunas_agrupadas:
        return df_result
    
    # Criar coluna ATC_CODE_5_HASH antes da limpeza e desagrupamento
    # Usa valores ORIGINAIS para identificar linhas que vieram da mesma linha agrupada
    # O ID é gerado usando SHA256 hash para garantir consistência e evitar caracteres especiais
    col_id = 'ATC_CODE_5_HASH'
    colunas_id = ['IDENTIFICACAO_NOTIFICACAO', 'NOME_MEDICAMENTO_WHODRUG', 'ATC_CODE_5']
    
    # Verificar se as colunas necessárias existem
    colunas_id_existentes = [col for col in colunas_id if col in df_result.columns]
    
    if len(colunas_id_existentes) == len(colunas_id):
        # Função auxiliar para gerar hash SHA256
        def gerar_hash_id(row):
            """Gera hash SHA256 a partir dos valores originais."""
            # Concatenar valores originais (antes da limpeza)
            string_id = (
                str(row['IDENTIFICACAO_NOTIFICACAO']) + '_' +
                str(row['NOME_MEDICAMENTO_WHODRUG']) + '_' +
                str(row['ATC_CODE_5'])
            )
            # Gerar hash SHA256 e retornar em hexadecimal
            return hashlib.sha256(string_id.encode('utf-8')).hexdigest()
        
        # Aplicar função para criar o ID
        df_result[col_id] = df_result.apply(gerar_hash_id, axis=1)
    
    def processar_linha(row: pd.Series) -> List[dict]:
        """
        Processa uma linha do DataFrame, dividindo valores agrupados.
        
        Returns:
        --------
        list
            Lista de dicionários, um para cada linha desagrupada
        """
        valores_divididos = {}
        max_len = 1
        
        # Dividir cada coluna agrupada
        for col in colunas_agrupadas:
            valor = row[col]
            
            if pd.isna(valor):
                valores_divididos[col] = ['']
            else:
                # Normalizar separadores
                valor_normalizado = _normalizar_separadores(valor)
                
                # Dividir por pipe e limpar
                if valor_normalizado and valor_normalizado.strip():
                    # Dividir por pipe e manter valores não vazios
                    valores = [v.strip() for v in valor_normalizado.split('|') if v.strip()]
                    # Se após split não houver valores (ex: string era apenas pipes), usar string vazia
                    if not valores:
                        valores = ['']
                else:
                    # Se valor normalizado está vazio, usar string vazia
                    valores = ['']
                
                valores_divididos[col] = valores
                max_len = max(max_len, len(valores))
        
        # Garantir que todas as listas tenham o mesmo tamanho
        # Se uma lista for menor, repetir o último valor
        for col in colunas_agrupadas:
            lista = valores_divididos[col]
            if len(lista) < max_len:
                ultimo_valor = lista[-1] if lista else ''
                valores_divididos[col].extend([ultimo_valor] * (max_len - len(lista)))
        
        # Criar uma lista de dicionários, um para cada linha desagrupada
        linhas_desagrupadas = []
        for i in range(max_len):
            nova_linha = row.to_dict()
            for col in colunas_agrupadas:
                nova_linha[col] = valores_divididos[col][i]
            linhas_desagrupadas.append(nova_linha)
        
        return linhas_desagrupadas
    
    # Aplicar processamento a cada linha
    todas_linhas = []
    for idx, row in df_result.iterrows():
        linhas = processar_linha(row)
        todas_linhas.extend(linhas)
    
    # Criar novo DataFrame
    df_desagrupado = pd.DataFrame(todas_linhas)
    
    # Remover linhas onde todas as colunas agrupadas estão vazias (se solicitado)
    if not manter_linhas_vazias:
        mask_vazias = df_desagrupado[colunas_agrupadas].apply(
            lambda row: all(str(val).strip() == '' for val in row), axis=1
        )
        df_desagrupado = df_desagrupado[~mask_vazias]
    
    # Resetar índice
    df_desagrupado = df_desagrupado.reset_index(drop=True)
    
    return df_desagrupado
