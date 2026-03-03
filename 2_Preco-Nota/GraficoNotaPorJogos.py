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

def contarJogosPorCategoriaNota(jogosPagos):
    """Conta número de jogos por categoria de nota"""
    print("Contando jogos por categoria de nota...")
    
    contagemNota = jogosPagos['categoriaNota'].value_counts().reset_index()
    contagemNota.columns = ['categoriaNota', 'numeroJogos']
    
    return contagemNota

def criarGraficoNotaPorNumeroJogos(contagemNota):
    """Cria gráfico de barras mostrando número de jogos por categoria de nota"""
    print("Criando gráfico de número de jogos por categoria de nota...")
    
    plt.figure(figsize=(12, 7))
    plt.bar(contagemNota['categoriaNota'], contagemNota['numeroJogos'], 
            color='#4ECDC4')
    
    plt.title('Número de Jogos por Categoria de Nota', fontsize=14, weight='bold')
    plt.xlabel('Categoria de Nota', fontsize=12)
    plt.ylabel('Número de Jogos', fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def exibirResultados(contagemNota):
    """Exibe os resultados da análise"""
    print("\n" + "="*50)
    print("ANÁLISE DE JOGOS POR CATEGORIA DE NOTA")
    print("="*50)
    
    print("\nNúmero de Jogos por Categoria de Nota:")
    print(contagemNota.to_string(index=False))
    
    totalJogos = contagemNota['numeroJogos'].sum()
    print(f"\nTotal de jogos analisados: {totalJogos}")
    
    categoriaMaisComum = contagemNota.loc[contagemNota['numeroJogos'].idxmax()]
    print(f"Categoria mais comum: {categoriaMaisComum['categoriaNota']} ({categoriaMaisComum['numeroJogos']} jogos)")
    
    # Calcular percentuais
    print("\nDistribuição percentual:")
    for _, linha in contagemNota.iterrows():
        percentual = (linha['numeroJogos'] / totalJogos) * 100
        print(f"{linha['categoriaNota']}: {percentual:.1f}%")

def main():
    """Função principal que executa a análise de nota por número de jogos"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    jogosPagos = converterPrecosParaBRL(dadosJogos)
    jogosPagos = criarCategoriasNota(jogosPagos)
    contagemNota = contarJogosPorCategoriaNota(jogosPagos)
    
    criarGraficoNotaPorNumeroJogos(contagemNota)
    exibirResultados(contagemNota)
    
    # Salvar resultados no MongoDB
    totalJogos = contagemNota['numeroJogos'].sum()
    distribuicaoPercentual = {}
    for _, linha in contagemNota.iterrows():
        percentual = (linha['numeroJogos'] / totalJogos) * 100
        categoria = linha['categoriaNota']
        # Converte Categorical para string se necessário
        if hasattr(categoria, 'item'):
            categoria = str(categoria)
        else:
            categoria = str(categoria)
        distribuicaoPercentual[categoria] = float(percentual)
    
    categoriaMaisComum = contagemNota.loc[contagemNota['numeroJogos'].idxmax()]['categoriaNota']
    # Converte Categorical para string se necessário
    if hasattr(categoriaMaisComum, 'item'):
        categoriaMaisComum = str(categoriaMaisComum)
    else:
        categoriaMaisComum = str(categoriaMaisComum)
    
    resultados = {
        'contagem_por_categoria': converterParaDict(contagemNota),
        'total_jogos': int(totalJogos),
        'distribuicao_percentual': distribuicaoPercentual,
        'categoria_mais_comum': categoriaMaisComum
    }
    
    salvarResultado(colecao, 'Nota por Numero Jogos', 'nota_categoria', resultados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()
