import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Adiciona o diretório raiz ao path para importar mongo_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mongo_utils import conectarMongoDB, salvarResultado, converterParaDict

sns.set_style("whitegrid")

def carregarDados():
    """Carrega os dados dos jogos já limpos"""
    print("Carregando dados...")
    try:
        
        caminhoArquivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'steam_games_data_limpo.csv')
        dadosJogos = pd.read_csv(caminhoArquivo)
        
        print(f"Total de jogos carregados: {len(dadosJogos)}")
        return dadosJogos
        
    except FileNotFoundError:
        print("Erro: Arquivo 'steam_games_data_limpo.csv' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return None

def processarGeneros(dadosJogos):
    """Processa e limpa os gêneros dos jogos"""
    print("Processando gêneros...")
    
    todosGenerosBrutos = dadosJogos['genres'].str.split(',').explode()
    todosGenerosLimpos = todosGenerosBrutos.str.strip()
    
    print(f"Total de gêneros únicos encontrados: {todosGenerosLimpos.nunique()}")
    
    return todosGenerosLimpos

def analisarTopGeneros(todosGeneros, topN):
    """Analisa os top N gêneros mais comuns"""
    print(f"Analisando top {topN} gêneros...")
    
    topGeneros = todosGeneros.value_counts().nlargest(topN)
    
    print(f"Top {topN} gêneros identificados")
    return topGeneros

def criarGraficoTopGeneros(topGeneros):
    """Cria gráfico de barras horizontal com os top gêneros"""
    print("Criando gráfico de top gêneros...")
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=topGeneros.values, y=topGeneros.index, palette='viridis')
    
    plt.title('Top 10 Gêneros Mais Comuns na Steam', fontsize=14, weight='bold')
    plt.xlabel('Quantidade de Jogos', fontsize=12)
    plt.ylabel('Gênero', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()

def exibirResultados(topGeneros):
    """Exibe os resultados da análise"""
    print("\n" + "="*50)
    print("ANÁLISE DOS GÊNEROS MAIS COMUNS NA STEAM")
    print("="*50)
    
    print(f"\nTop 10 Gêneros Mais Comuns:")
    for i, (genero, quantidade) in enumerate(topGeneros.items(), 1):
        print(f"  {i:2d}. {genero:<25} : {quantidade:4d} jogos")
    
    totalJogos = topGeneros.sum()
    print(f"\nTotal de jogos nos top 10 gêneros: {totalJogos}")
    
    generoMaisComum = topGeneros.index[0]
    quantidadeMaisComum = topGeneros.iloc[0]
    percentual = (quantidadeMaisComum / totalJogos) * 100
    
    print(f"Gênero mais comum: {generoMaisComum} ({quantidadeMaisComum} jogos - {percentual:.1f}%)")

def main():
    """Função principal que executa toda a análise"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    
    if dadosJogos is None:
        if cliente:
            cliente.close()
        return
    
    todosGeneros = processarGeneros(dadosJogos)
    topGeneros = analisarTopGeneros(todosGeneros, 10)
    
    criarGraficoTopGeneros(topGeneros)
    exibirResultados(topGeneros)
    
    # Salvar resultados no MongoDB
    resultados = {
        'top_generos': converterParaDict(topGeneros),
        'total_generos_unicos': int(todosGeneros.nunique()),
        'total_jogos_analisados': len(dadosJogos)
    }
    
    metadados = {
        'top_n': 10,
        'total_generos': int(todosGeneros.nunique())
    }
    
    salvarResultado(colecao, 'Top Generos Steam', 'generos', resultados, metadados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()