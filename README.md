# ENEM-2020-Teste-Tecnico-Pulse-2026

## 1 - Objetivo
Resolução do Teste Técnico proposto pela Pulse como etapa do processo seletivo para a posição de Especialista em Dados

## 2 - Stack utilizada
Docker, MySQL, Python e Tableau.

## 3 - Arquitetura do projeto
A solução foi estruturada em um fluxo de dados local utilizando Python, MySQL em container Docker e Tableau para visualização analítica.

O pipeline segue a arquitetura:

Microdados ENEM 2020 (CSV)
- ETL em Python
- Banco MySQL `enem_db`
- Modelo dimensional
- Consultas SQL e conexão com Tableau
- Dashboard analítico
  
A base original foi processada em blocos (chunks) para permitir a leitura eficiente do arquivo completo dos microdados, evitando consumo excessivo de memória durante o carregamento.

## 4 - Modelagem dimensional
A modelagem foi organizada em formato dimensional, com uma tabela fato principal e dimensões analíticas.

### Tabela fato

`fato_desempenho`

Contém as notas dos participantes nas provas objetivas e na redação:

- `NU_INSCRICAO`
- `NU_NOTA_CN`
- `NU_NOTA_CH`
- `NU_NOTA_LC`
- `NU_NOTA_MT`
- `NU_NOTA_REDACAO`

### Dimensões

`dim_aluno`

Contém marcadores sociais do participante e informações de presença:

- `TP_SEXO`
- `TP_COR_RACA`
- `TP_FAIXA_ETARIA`
- `TP_ESCOLA`
- `TP_PRESENCA_CN`
- `TP_PRESENCA_CH`
- `TP_PRESENCA_LC`
- `TP_PRESENCA_MT`

`dim_escola`

Contém informações territoriais das escolas:

- `CO_UF_ESC`
- `SG_UF_ESC`
- `CO_MUNICIPIO_ESC`
- `NO_MUNICIPIO_ESC`
- `TP_LOCALIZACAO_ESC`

`dim_socioeconomica`

Contém as respostas do questionário socioeconômico do ENEM:

- `Q001` a `Q025`

`dim_redacao`

Contém o status da redação e as notas por competência:

- `TP_STATUS_REDACAO`
- `NU_NOTA_COMP1` até `NU_NOTA_COMP5`

`dim_inse`

Tabela criada para armazenar o índice socioeconômico calculado via PCA:

- `NU_INSCRICAO`
- `INSE_Score`

### Construção do INSE
Além das variáveis originais da base, foi criado um Índice de Nível Socioeconômico (`INSE_Score`) a partir das respostas do questionário socioeconômico.

O índice foi calculado com PCA (_Principal Component Analysis_), após transformação das variáveis categóricas em  numéricas e padronização das variáveis com `StandardScaler`. Foram consideradas as variáveis relacionadas a renda familiar, escolaridade, bens domésticos e acesso a recursos como internet e equipamentos (televisão, lava-louças etc). O índice foi utilizado como uma medida sintética do nível socioeconômico do participante.

Esse índice foi posteriormente utilizado no Tableau para analisar a relação entre contexto socioeconômico do participante e desempenho nas provas objetivas.

## 5 - ETL
O processo de ETL foi desenvolvido em Python com uso das bibliotecas `pandas`, `sqlalchemy`, `pymysql`, `numpy` e `scikit-learn`.

As principais etapas foram:

1. Criação automática do banco de dados `enem_db` no MySQL.
2. Leitura do arquivo `MICRODADOS_ENEM_2020.csv` em blocos de 50.000 registros.
3. Seleção apenas das colunas necessárias para fato e dimensões.
4. Tratamento de valores nulos e padronização dos tipos de dados.
5. Separação da base em tabelas dimensionais e tabela fato.
6. Carga incremental das tabelas no MySQL.
7. Construção de um índice socioeconômico próprio via PCA.
8. Gravação do índice socioeconômico pela tabela `dim_inse`.

## 6 - Indicadores solicitados
### Escola com maior média
Até 2019, o INEP disponibilizava resultados com identificação escolar. A partir de 2020, em conformidade com a Lei Geral de Proteção de Dados (LGPD) e novas diretrizes de divulgação, o nível de agregação mínimo passou a ser o município do aluno. Feitas as devidas decisões metodológicas, Florianópolis (SC) foi o município com a maior média do país: 579,2 pts

### Demais indicadores
- **Aluno com a maior média:** aluno do sexo masculino, 18 anos, branco e sem informação de município e UF. A média foi de 858,5. 
- **Média geral:** 526,6 pts
- **% ausentes:** 55,2%
- **Total inscritos:** 5.783.109
- **Média por disciplina:** Ciências da Natureza = 490,5; Ciências Humanas = 514,3; Linguagens e Códigos = 526,0; Matemática = 520,7; Redação = 581,3
- **Média por sexo:** Masculino = 524,5 e Feminino = 491,5
- **Média por etnia:** Branca = 536,8; Parda = 486,4; Preta = 482,2; Amarela = 497,5; Indígena = 457,5; Não Declarada = 513,1

## 7 - Dashboard
Todas as visualizações foram construídas no Tableau Public. Para acesso ao dashboard, clique [aqui](https://public.tableau.com/views/PainelEnem2020/Perfil?:language=pt-BR&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link).

O dashboard foi organizado em 4 páginas:

- Geral
- Desempenho
- Perfil
- Redação

## 8 - Conclusões e insights

1. Observa-se um elevado índice de abstenção em 2020, reflexo direto das medidas restritivas impostas pela pandemia de Covid-19.

2. As variações de desempenho no ENEM podem ser estruturadas em quatro pilares: a Redação destaca-se pela alta treinabilidade técnica. Linguagens e Matemática apresentam resultados estáveis geralmente devido à carga horária contínua. Ciências Humanas, por sua vez, demandam interpretação e pensamento crítico. Ciências da Natureza apresenta a maior defasagem, refletindo a carência de práticas laboratoriais e a complexidade do raciocínio lógico-científico exigido.

3. Participantes que obtiveram maiores notas na Redação também apresentaram, em média, melhor desempenho nas demais áreas do exame, evidenciando uma relação positiva entre competências de escrita e desempenho acadêmico geral.

4. Observou-se diferença de desempenho entre grupos raciais, com participantes autodeclarados brancos e amarelos apresentando médias superiores às observadas para participantes pretos, pardos e indígenas, refletindo as desigualdades educacionais historicamente presentes em nosso país.

5. O nível socioeconômico mostrou associação positiva com a Nota Total, indicando um fenômeno já conhecido socialmente: candidatos com maior acesso a recursos educacionais tendem a alcançar melhores resultados no exame.

6. Participantes oriundos de escolas privadas apresentaram desempenho médio superior em relação aos estudantes de escolas públicas, reforçando diferenças estruturais de acesso a recursos pedagógicos e oportunidades de aprendizagem.

7. As faixas etárias mais jovens, especialmente entre 17 e 20 anos, concentraram as maiores médias de desempenho, enquanto candidatos de faixas etárias mais elevadas apresentaram redução gradual nas notas médias.

8. Observou-se uma relação positiva entre a escolaridade materna e o desempenho dos participantes no ENEM. De forma geral, as notas aumentam progressivamente à medida que cresce o nível de instrução da mãe.

9. Foram identificadas diferenças regionais relevantes, com estados das regiões Sul e Sudeste apresentando, em média, desempenho superior ao observado em parte das regiões Norte e Nordeste, evidenciando desigualdades territoriais no acesso à educação de qualidade.

10. A análise conjunta das variáveis sugere que fatores socioeconômicos, contexto escolar e características demográficas possuem influência significativa sobre o desempenho dos participantes, indicando que a nota total do ENEM é resultado não apenas do esforço individual, mas também das condições educacionais e sociais às quais os estudantes vivenciam.


