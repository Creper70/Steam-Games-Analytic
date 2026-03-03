import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Adiciona o diretório raiz ao path para importar mongo_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mongo_utils import conectarMongoDB, salvarResultado, converterParaDict

# Taxas de câmbio para conversão de moedas para BRL
TAXAS_CAMBIO = {
    'BRL': 1.00, 
    'USD': 5.32, 'EUR': 6.25, 'GBP': 7.18,
    'IDR': 0.00032, 'KRW': 0.0038, 'CAD': 3.90, 'AUD': 3.45,
    'SGD': 3.95, 'HKD': 0.68, 'PLN': 1.40, 'THB': 0.15,
    'KZT': 0.012
}

def carregarDados():
    """Carrega e limpa os dados dos jogos"""
    print("Carregando dados...")
    
    caminhoArquivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'steam_games_data_limpo.csv')
    dadosJogos = pd.read_csv(caminhoArquivo)
    
    dadosJogos['price'] = pd.to_numeric(dadosJogos['price'], errors='coerce')
    dadosJogos['steam_review_score'] = pd.to_numeric(dadosJogos['steam_review_score'], errors='coerce')
    
    dadosLimpos = dadosJogos.dropna(subset=['price', 'steam_review_score', 'currency'])
    print(f"Total de jogos com dados válidos: {len(dadosLimpos)}")
    
    return dadosLimpos

def converterPrecosParaBRL(dadosJogos):
    """Converte preços de diferentes moedas para BRL"""
    print("Convertendo preços para BRL...")
    
    def converterPreco(linha):
        moeda = linha['currency']
        preco = linha['price']
        taxa = TAXAS_CAMBIO.get(moeda, 1.0)
        return preco * taxa
    
    dadosJogos['precoBRL'] = dadosJogos.apply(converterPreco, axis=1)
    jogosPagos = dadosJogos[dadosJogos['precoBRL'] > 0].copy()
    
    print(f"Jogos pagos analisados: {len(jogosPagos)}")
    return jogosPagos

def calcularCorrelacao(jogosPagos):
    """Calcula a correlação entre preço e nota"""
    correlacao = jogosPagos['precoBRL'].corr(jogosPagos['steam_review_score'])
    print(f"Correlação de Pearson: {correlacao:.4f}")
    return correlacao

def criarCategoriasNota(jogosPagos):
    """Cria categorias de nota para análise"""
    print("Criando categorias de nota...")
    
    faixas = [0, 59, 69, 79, 89, 100]
    rotulos = ['< 60 (Mista/Negativa)', '60-69 (Mista)', '70-79 (Principalmente Positiva)', 
               '80-89 (Muito Positiva)', '90+ (Extremamente Positiva)']
    
    jogosPagos['categoriaNota'] = pd.cut(jogosPagos['steam_review_score'], 
                                        bins=faixas, labels=rotulos, 
                                        right=True, include_lowest=True)
    return jogosPagos

def calcularPrecoMedioPorCategoria(jogosPagos):
    """Calcula preço médio por categoria de nota"""
    print("Calculando preço médio por categoria...")
    
    precoMedioPorCategoria = jogosPagos.groupby('categoriaNota')['precoBRL'].mean().reset_index()
    return precoMedioPorCategoria


def criarGraficoRelacao(precoMedioPorCategoria):
    """Cria gráfico de barras mostrando relação preço vs nota"""
    print("Criando gráfico de preço médio por categoria de nota...")
    
    plt.figure(figsize=(12, 7))
    plt.bar(precoMedioPorCategoria['categoriaNota'], precoMedioPorCategoria['precoBRL'], 
            color='#009688')
    
    plt.title('Preço Médio (R$) por Faixa de Nota de Análise do Steam', fontsize=14, weight='bold')
    plt.xlabel('Faixa de Nota de Análise do Steam', fontsize=12)
    plt.ylabel('Preço Médio (R$)', fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def exibirResultados(correlacao, precoMedioPorCategoria):
    """Exibe os resultados da análise"""
    print("\n" + "="*50)
    print("ANÁLISE DA RELAÇÃO PREÇO vs NOTA")
    print("="*50)
    print(f"Coeficiente de Correlação de Pearson: {correlacao:.4f}")
    
    if correlacao > 0.3:
        print("Interpretação: Correlação positiva moderada/forte")
    elif correlacao > 0.1:
        print("Interpretação: Correlação positiva fraca")
    elif correlacao > -0.1:
        print("Interpretação: Praticamente sem correlação")
    else:
        print("Interpretação: Correlação negativa")
    
    print("\nPreço Médio por Categoria de Nota:")
    print(precoMedioPorCategoria.to_string(index=False))

def main():
    """Função principal que executa toda a análise"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    jogosPagos = converterPrecosParaBRL(dadosJogos)
    correlacao = calcularCorrelacao(jogosPagos)
    jogosPagos = criarCategoriasNota(jogosPagos)
    precoMedioPorCategoria = calcularPrecoMedioPorCategoria(jogosPagos)
    
    criarGraficoRelacao(precoMedioPorCategoria)
    exibirResultados(correlacao, precoMedioPorCategoria)
    
    # Salvar resultados no MongoDB
    resultados = {
        'correlacao_pearson': float(correlacao),
        'preco_medio_por_categoria': converterParaDict(precoMedioPorCategoria),
        'total_jogos_analisados': len(jogosPagos)
    }
    
    metadados = {
        'interpretacao': 'Correlação positiva moderada/forte' if correlacao > 0.3 
                        else 'Correlação positiva fraca' if correlacao > 0.1
                        else 'Praticamente sem correlação' if correlacao > -0.1
                        else 'Correlação negativa'
    }
    
    salvarResultado(colecao, 'Preco vs Nota', 'correlacao', resultados, metadados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()