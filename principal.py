
### --- Teste Pulse: Analista de Dados --- ###

# Pacotes
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from urllib.parse import quote_plus
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


## -------- CONEXÃO MYSQL + CRIAÇÃO DO BANCO -------- ##

engine = create_engine(f"mysql+pymysql://root:{quote_plus('129246@')}@127.0.0.1:3306/")

# Criação do banco
with engine.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS enem_db"))
    print("Banco de dados 'enem_db' criado ou já existente.")

engine = create_engine(f"mysql+pymysql://root:{quote_plus('129246@')}@127.0.0.1:3306/enem_db")


## -------- PROCESSO ETL -------- ##

# Caminho do arquivo
arquivo = "microdados_enem_2020/DADOS/MICRODADOS_ENEM_2020.csv"

cols_fato = ['NU_INSCRICAO', 'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']
cols_aluno = ['NU_INSCRICAO', 'TP_SEXO', 'TP_COR_RACA', 'TP_FAIXA_ETARIA', 'TP_ESCOLA', 'TP_PRESENCA_CN','TP_PRESENCA_CH','TP_PRESENCA_LC',
              'TP_PRESENCA_MT']
cols_socio = ['NU_INSCRICAO'] + [f'Q{str(i).zfill(3)}' for i in range(1, 26)]
cols_escola = ['NU_INSCRICAO','CO_UF_ESC','SG_UF_ESC','CO_MUNICIPIO_ESC','NO_MUNICIPIO_ESC','TP_LOCALIZACAO_ESC']
cols_redacao = ['NU_INSCRICAO','TP_STATUS_REDACAO','NU_NOTA_COMP1','NU_NOTA_COMP2','NU_NOTA_COMP3','NU_NOTA_COMP4','NU_NOTA_COMP5']


todas_colunas = list(set(cols_fato + cols_aluno + cols_socio + cols_escola + cols_redacao))

# Função de tratamento dos dados

def limpar_dados(df):
    # Tratamento da Tabela Fato (Notas)
    cols_notas = ['NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']
    df[cols_notas] = df[cols_notas].fillna(0)
    
    # 2. Tratamento da Dimensão Aluno (Exceto TP_SEXO)
    cols_aluno_num = ['NU_INSCRICAO','TP_COR_RACA', 'TP_FAIXA_ETARIA', 'TP_ESCOLA', 'TP_PRESENCA_CN','TP_PRESENCA_CH','TP_PRESENCA_LC',
              'TP_PRESENCA_MT']
    for col in cols_aluno_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(-1).astype(int)
    
    # Tratamento específico para Sexo (Mantendo 'F' e 'M')
    if 'TP_SEXO' in df.columns:
        df['TP_SEXO'] = df['TP_SEXO'].fillna('N').astype(str)

    # Tratamento da Dimensão Escola
    cols_escola = ['CO_UF_ESC','SG_UF_ESC','CO_MUNICIPIO_ESC','NO_MUNICIPIO_ESC','TP_LOCALIZACAO_ESC']
    for col in cols_escola:
        if col in df.columns:
            if 'CO_' in col or 'TP_' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = df[col].fillna('N/A').astype(str)
    
    # Tratamento da Dimensão Redação
    cols_redacao = ['TP_STATUS_REDACAO','NU_NOTA_COMP1','NU_NOTA_COMP2','NU_NOTA_COMP3','NU_NOTA_COMP4','NU_NOTA_COMP5']
    df[cols_redacao] = df[cols_redacao].fillna(0)
            
    return df

# Execução ETL 

chunksize = 50000

# Abrindo o arquivo e lendo em blocos
reader = pd.read_csv(arquivo, sep=';', encoding='ISO-8859-1', usecols=todas_colunas, chunksize=chunksize)

print("Iniciando carga no MySQL...")

for i, chunk in enumerate(reader):
    
    chunk_limpo = limpar_dados(chunk)
    
    modo = 'replace' if i == 0 else 'append'
       
    # Envia para as tabelas (Fato e Dimensões)
    chunk_limpo[cols_fato].to_sql('fato_desempenho', con=engine, if_exists=modo, index=False)
    chunk_limpo[cols_aluno].to_sql('dim_aluno', con=engine, if_exists=modo, index=False)
    chunk_limpo[cols_socio].to_sql('dim_socioeconomica', con=engine, if_exists=modo, index=False)
    chunk_limpo[cols_escola].to_sql('dim_escola', con=engine, if_exists=modo, index=False)
    chunk_limpo[cols_redacao].to_sql('dim_redacao', con=engine, if_exists=modo, index=False)
    
    print(f"Bloco {i+1} processado e gravado com todas as tabelas.")

print("ETL concluído com sucesso!")


## -------- CÁLCULO ÍNDICE NÍVEL SOCIOECONÔMICO -------- ##

# Conexão
engine = create_engine(f"mysql+pymysql://root:{quote_plus('129246@')}@127.0.0.1:3306/enem_db")

def calcular_inse():
    # Lê os dados necessários da tabela dim_socioeconomica
    # Seleciona apenas as colunas que importam para o cálculo
    print("Lendo dados do MySQL...")
    query = "SELECT * FROM dim_socioeconomica"
    df = pd.read_sql(query, engine)
    
    # Pré-processamento (separa as variáveis binárias e ordinais lógicas)
    cols_binarias = ['Q018', 'Q020', 'Q021', 'Q023', 'Q025']
    mapa_ordinal = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
    mapa_renda = {chr(i): i - 65 for i in range(65, 82)} 

    # Transformação das categorias em números -- necessário para o cálculo
    for col in cols_binarias:
        df[col + '_n'] = df[col].apply(lambda x: 1 if x == 'B' else 0)
    
    cols_ordinais = [c for c in df.columns if c.startswith('Q') and c not in cols_binarias and c not in ['Q005', 'Q006', 'NU_INSCRICAO']]
    for col in cols_ordinais:
        df[col + '_n'] = df[col].map(mapa_ordinal).fillna(0)
        
    df['Q006_n'] = df['Q006'].map(mapa_renda).fillna(0)
    df['Q005_n'] = pd.to_numeric(df['Q005'], errors='coerce').fillna(1).clip(upper=8)
    
    # Seleciona as colunas numéricas para o INSE
    cols_para_pca = [c for c in df.columns if c.endswith('_n') or c in ['Q006_n', 'Q005_n']]
    features = df[cols_para_pca].fillna(0)
    
    # Cálculo do INSE
    print("Calculando INSE via PCA...")
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    pca = PCA(n_components=1)
    df['INSE_Score'] = pca.fit_transform(features_scaled)
    
    # Gravar resultado no banco como uma nova tabela
    print("Salvando resultado no MySQL...")
    df_resultado = df[['NU_INSCRICAO', 'INSE_Score']]
    df_resultado.to_sql('dim_inse', con=engine, if_exists='replace', index=False)
    print("Processo concluído!")

# Executar a função
if __name__ == "__main__":
    calcular_inse()


## -------- LEVANTAMENTO DE INDICADORES -------- ##

# Otimização de Performance na hora das consultas com a criação de índices
with engine.connect() as conn:
    print("Criando índices para otimizar as consultas...")
    # Criar chaves primárias para acelerar buscas e joins
    conn.execute(text("ALTER TABLE fato_desempenho ADD PRIMARY KEY (NU_INSCRICAO);"))
    conn.execute(text("ALTER TABLE dim_aluno ADD PRIMARY KEY (NU_INSCRICAO);"))
    conn.execute(text("ALTER TABLE dim_escola ADD PRIMARY KEY (NU_INSCRICAO);"))
    conn.execute(text("ALTER TABLE dim_socioeconomica ADD PRIMARY KEY (NU_INSCRICAO);"))
    print("Índices criados com sucesso!")


# Função para rodar as queries
def rodar_query(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)



# Aluno com a maior média ----
query_maior_media_aluno = """
    SELECT 
        f.NU_INSCRICAO, 
        (f.NU_NOTA_CN + f.NU_NOTA_CH + f.NU_NOTA_LC + f.NU_NOTA_MT + f.NU_NOTA_REDACAO)/5 AS MEDIA,
        a.TP_SEXO,
        a.TP_COR_RACA,
        a.TP_ESCOLA,
        e.NO_MUNICIPIO_ESC
    FROM fato_desempenho f
    JOIN dim_aluno a ON f.NU_INSCRICAO = a.NU_INSCRICAO
    JOIN dim_escola e ON f.NU_INSCRICAO = e.NU_INSCRICAO
    WHERE a.TP_PRESENCA_CN = 1 
      AND a.TP_PRESENCA_CH = 1 
      AND a.TP_PRESENCA_LC = 1 
      AND a.TP_PRESENCA_MT = 1
    ORDER BY MEDIA DESC 
    LIMIT 1;
"""

print("Detalhes do aluno com maior média (validado):")
print(rodar_query(query_maior_media_aluno))

