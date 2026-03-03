# Steam Games Analytics - Análise Exploratória e Big Data

Projeto acadêmico focado na extração e análise exploratória de dados da plataforma Steam. O objetivo principal é entender as tendências de mercado e identificar os fatores que contribuem para o sucesso de um jogo digital, analisando as relações entre custo, gênero, avaliação dos jogadores e frequência de lançamentos.

## Domínio e Origem dos Dados
A análise concentra-se no setor de videogames e na distribuição digital para a plataforma PC. 
* Os dados originais foram coletados diretamente da API Steamworks.
* A base de dados utilizada nas análises conta com 1.000 jogos distintos que possuem avaliações válidas na plataforma.

## Processamento de Dados (ETL) e Datasets
A etapa de preparação dos dados foi documentada através da disponibilização dos datasets em seus estados bruto e processado neste repositório. O processo de transformação englobou:
* **Limpeza e Padronização:** Tratamento de valores ausentes na coluna de preço, padronização de formatos de data e conversão de colunas de texto para valores numéricos, gerando uma base estruturada para consumo analítico.

**Arquivos disponíveis:**
* `steam_games_data.csv`: Dataset bruto extraído da API.
* `steam_games_data_limpo.csv`: Dataset higienizado e formatado para a execução dos scripts de análise.

## Módulos de Análise Exploratória (EDA)
O núcleo deste repositório consiste em scripts independentes desenvolvidos em Python que respondem a perguntas de negócio específicas com base nos dados processados:

* **1. Gênero de Jogos (`Genero_Jogos.py`):** Identifica os gêneros mais prevalentes na plataforma. O script realiza a separação de strings compostas (ex: "Action,RPG") em entradas individuais para gerar um ranking preciso.
* **2. Preço vs. Nota (`2_Preco-Nota`):** Investiga a correlação entre o custo de aquisição dos jogos e as suas respectivas avaliações, analisando a distribuição de títulos por faixas de preço.
* **3. Ano vs. Nota (`3_Ano-Nota`):** Mapeia a evolução da recepção do público e a qualidade percebida dos jogos ao longo dos anos de lançamento.
* **4. Gênero vs. Ano (`4_Gen-Ano`):** Avalia a popularidade, o surgimento e o declínio de diferentes gêneros de jogos ao longo do tempo.
* **7. Distribuição de Notas (`7_Nota-Distribuicao`):** Apresenta uma visão estatística da distribuição geral das avaliações na plataforma.

## Equipe Desenvolvedora
Projeto desenvolvido como requisito para a disciplina de Análise de Negócios com Uso de Big Data na Universidade Veiga de Almeida (2025). 
* **Integrantes:** Caique Guimarães, Charles Henrique, Davi Manoel, João Paulo, João Victor e Lucas Costa.
