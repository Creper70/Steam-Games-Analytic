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

def criarCategoriasPreco(jogosPagos):
    """Cria categorias de preço para análise"""
    print("Criando categorias de preço...")
    
    faixasPreco = [0, 10, 25, 50, 100, float('inf')]
    rotulosPreco = ['Gratuito (R$ 0)', 'Barato (R$ 1-10)', 'Médio (R$ 11-25)', 
                    'Caro (R$ 26-50)', 'Muito Caro (R$ 51+)']
    
    jogosPagos['categoriaPreco'] = pd.cut(jogosPagos['precoBRL'], 
                                         bins=faixasPreco, labels=rotulosPreco, 
                                         right=False, include_lowest=True)
    return jogosPagos

def contarJogosPorCategoriaPreco(jogosPagos):
    """Conta número de jogos por categoria de preço"""
    print("Contando jogos por categoria de preço...")
    
    contagemPreco = jogosPagos['categoriaPreco'].value_counts().reset_index()
    contagemPreco.columns = ['categoriaPreco', 'numeroJogos']
    contagemPreco = contagemPreco.sort_values('categoriaPreco')
    
    return contagemPreco

def criarGraficoPrecoPorNumeroJogos(contagemPreco):
    """Cria gráfico de barras mostrando número de jogos por categoria de preço"""
    print("Criando gráfico de número de jogos por categoria de preço...")
    
    plt.figure(figsize=(12, 7))
    plt.bar(contagemPreco['categoriaPreco'], contagemPreco['numeroJogos'], 
            color='#FF6B6B')
    
    plt.title('Número de Jogos por Categoria de Preço', fontsize=14, weight='bold')
    plt.xlabel('Categoria de Preço', fontsize=12)
    plt.ylabel('Número de Jogos', fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def exibirResultados(contagemPreco):
    """Exibe os resultados da análise"""
    print("\n" + "="*50)
    print("ANÁLISE DE JOGOS POR CATEGORIA DE PREÇO")
    print("="*50)
    
    print("\nNúmero de Jogos por Categoria de Preço:")
    print(contagemPreco.to_string(index=False))
    
    totalJogos = contagemPreco['numeroJogos'].sum()
    print(f"\nTotal de jogos analisados: {totalJogos}")
    
    categoriaMaisComum = contagemPreco.loc[contagemPreco['numeroJogos'].idxmax()]
    print(f"Categoria mais comum: {categoriaMaisComum['categoriaPreco']} ({categoriaMaisComum['numeroJogos']} jogos)")

def main():
    """Função principal que executa a análise de preço por número de jogos"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    jogosPagos = converterPrecosParaBRL(dadosJogos)
    jogosPagos = criarCategoriasPreco(jogosPagos)
    contagemPreco = contarJogosPorCategoriaPreco(jogosPagos)
    
    criarGraficoPrecoPorNumeroJogos(contagemPreco)
    exibirResultados(contagemPreco)
    
    # Salvar resultados no MongoDB
    categoriaMaisComum = contagemPreco.loc[contagemPreco['numeroJogos'].idxmax()]['categoriaPreco']
    # Converte Categorical para string se necessário
    if hasattr(categoriaMaisComum, 'item'):
        categoriaMaisComum = str(categoriaMaisComum)
    else:
        categoriaMaisComum = str(categoriaMaisComum)
    
    resultados = {
        'contagem_por_categoria': converterParaDict(contagemPreco),
        'total_jogos': int(contagemPreco['numeroJogos'].sum()),
        'categoria_mais_comum': categoriaMaisComum
    }
    
    salvarResultado(colecao, 'Preco por Numero Jogos', 'preco_categoria', resultados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()
