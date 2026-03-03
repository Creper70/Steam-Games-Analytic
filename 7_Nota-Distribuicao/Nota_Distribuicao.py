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

def calcularEstatisticasNotas(dadosJogos):
    """Calcula estatísticas descritivas das notas"""
    print("Calculando estatísticas das notas...")
    
    estatisticas = dadosJogos['steam_review_score'].describe()
    return estatisticas

def criarGraficoDistribuicao(dadosJogos):
    """Cria histograma da distribuição das notas"""
    print("Criando gráfico de distribuição...")
    
    plt.figure(figsize=(12, 7))
    
    sns.histplot(dadosJogos['steam_review_score'], bins=30, kde=True, color='mediumpurple')
    
    media = dadosJogos['steam_review_score'].mean()
    mediana = dadosJogos['steam_review_score'].median()
    
    plt.axvline(media, color='red', linestyle='--', linewidth=2, 
                label=f"Média: {media:.2f}")
    plt.axvline(mediana, color='green', linestyle='-', linewidth=2, 
                label=f"Mediana: {mediana:.2f}")
    
    plt.title('Distribuição das Notas dos Jogos na Steam', fontsize=14, weight='bold')
    plt.xlabel('Pontuação de Avaliação (Nota de 0 a 100)', fontsize=12)
    plt.ylabel('Quantidade de Jogos', fontsize=12)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    return media, mediana

def exibirResultados(estatisticas, media, mediana):
    """Exibe os resultados da análise"""
    print("\n" + "="*60)
    print("ANÁLISE DA DISTRIBUIÇÃO DAS NOTAS DOS JOGOS NA STEAM")
    print("="*60)
    
    print("\nEstatísticas Descritivas das Notas:")
    print(f"  Contagem total: {estatisticas['count']:.0f} jogos")
    print(f"  Média: {estatisticas['mean']:.2f}")
    print(f"  Desvio padrão: {estatisticas['std']:.2f}")
    print(f"  Mínimo: {estatisticas['min']:.2f}")
    print(f"  Primeiro quartil (25%): {estatisticas['25%']:.2f}")
    print(f"  Mediana (50%): {estatisticas['50%']:.2f}")
    print(f"  Terceiro quartil (75%): {estatisticas['75%']:.2f}")
    print(f"  Máximo: {estatisticas['max']:.2f}")
    
    print(f"\nAnálise da Distribuição:")
    print(f"  Média: {media:.2f}")
    print(f"  Mediana: {mediana:.2f}")
    
    diferenca = abs(media - mediana)
    if diferenca < 2:
        print(f"  Interpretação: Distribuição aproximadamente simétrica (diferença: {diferenca:.2f})")
    elif media > mediana:
        print(f"  Interpretação: Distribuição com cauda à direita (média > mediana)")
    else:
        print(f"  Interpretação: Distribuição com cauda à esquerda (média < mediana)")

def main():
    """Função principal que executa toda a análise"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    
    if dadosJogos is None:
        if cliente:
            cliente.close()
        return
    
    estatisticas = calcularEstatisticasNotas(dadosJogos)
    media, mediana = criarGraficoDistribuicao(dadosJogos)
    
    exibirResultados(estatisticas, media, mediana)
    
    # Salvar resultados no MongoDB
    resultados = {
        'estatisticas': {
            'count': float(estatisticas['count']),
            'mean': float(estatisticas['mean']),
            'std': float(estatisticas['std']),
            'min': float(estatisticas['min']),
            '25%': float(estatisticas['25%']),
            '50%': float(estatisticas['50%']),
            '75%': float(estatisticas['75%']),
            'max': float(estatisticas['max'])
        },
        'media': float(media),
        'mediana': float(mediana)
    }
    
    diferenca = abs(media - mediana)
    interpretacao = 'Distribuição aproximadamente simétrica' if diferenca < 2 \
                   else 'Distribuição com cauda à direita' if media > mediana \
                   else 'Distribuição com cauda à esquerda'
    
    metadados = {
        'interpretacao': interpretacao,
        'diferenca_media_mediana': float(diferenca)
    }
    
    salvarResultado(colecao, 'Distribuicao Notas', 'distribuicao', resultados, metadados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()