import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Adiciona o diretório raiz ao path para importar mongo_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mongo_utils import conectarMongoDB, salvarResultado, converterParaDict

def carregarDados():
    """Carrega e exibe informações básicas dos dados"""
    print("Carregando dados...")
    
    caminhoArquivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'steam_games_data_limpo.csv')
    dadosJogos = pd.read_csv(caminhoArquivo)
    
    print(f"Total de jogos: {len(dadosJogos)}")
    print(f"Anos disponíveis: {dadosJogos['release_year'].min()} a {dadosJogos['release_year'].max()}")
    print("\nPrimeiras linhas:")
    print(dadosJogos.head())
    
    return dadosJogos

def criarGruposDeAnos(anoMinimo, anoMaximo):
    """Cria grupos de 5 anos para análise"""
    print("\n=== CRIANDO GRUPOS DE 5 ANOS ===")
    print(f"Ano mínimo: {anoMinimo}")
    print(f"Ano máximo: {anoMaximo}")
    
    gruposAnos = []
    anoAtual = anoMinimo
    
    while anoAtual <= anoMaximo:
        anoFim = anoAtual + 4
        gruposAnos.append((anoAtual, anoFim))
        anoAtual += 5
    
    print(f"Grupos criados: {gruposAnos}")
    return gruposAnos

def analisarTendenciasPorPeriodo(dadosJogos, gruposAnos):
    """Analisa as tendências de gênero para cada período de 5 anos"""
    print("\n=== ANÁLISE POR GRUPO DE 5 ANOS ===")
    
    listaTendencias = []
    
    for grupo in gruposAnos:
        anoInicio, anoFim = grupo
        jogosDoPeriodo = dadosJogos[(dadosJogos['release_year'] >= anoInicio) & 
                                   (dadosJogos['release_year'] <= anoFim)]
        
        if len(jogosDoPeriodo) == 0:
            print(f"{anoInicio}-{anoFim}: Nenhum jogo encontrado")
            continue
        
        print(f"\n--- {anoInicio}-{anoFim} ---")
        print(f"Total de jogos: {len(jogosDoPeriodo)}")
        
        contagemGeneros = jogosDoPeriodo['genres'].value_counts()
        
        print("Top 5 gêneros:")
        for i, (genero, quantidade) in enumerate(contagemGeneros.head(5).items(), 1):
            print(f"  {i}. {genero}: {quantidade} jogos")
        
        generoTendencia = contagemGeneros.index[0]
        quantidadeTendencia = contagemGeneros.iloc[0]
        
        listaTendencias.append({
            'periodo': f"{anoInicio}-{anoFim}",
            'generoTendencia': generoTendencia,
            'quantidade': quantidadeTendencia,
            'totalJogos': len(jogosDoPeriodo)
        })
        
        print(f"Gênero tendência: {generoTendencia} ({quantidadeTendencia} jogos)")
    
    return listaTendencias

def exibirResumoTendencias(listaTendencias):
    """Exibe o resumo das tendências por período"""
    print("\n" + "="*50)
    print("RESUMO DAS TENDÊNCIAS POR PERÍODO")
    print("="*50)
    
    for tendencia in listaTendencias:
        print(f"{tendencia['periodo']}: {tendencia['generoTendencia']} "
              f"({tendencia['quantidade']}/{tendencia['totalJogos']} jogos)")

def analisarGenerosMaisFrequentes(listaTendencias):
    """Analisa quais gêneros apareceram mais vezes como tendência"""
    print("\n=== ANÁLISE ADICIONAL ===")
    
    generosTendencia = [t['generoTendencia'] for t in listaTendencias]
    contagemTendencias = pd.Series(generosTendencia).value_counts()
    
    print("Gêneros que mais apareceram como tendência:")
    for genero, vezes in contagemTendencias.items():
        print(f"  {genero}: {vezes} períodos")

def criarGraficoTendencias(listaTendencias):
    """Cria gráfico de barras com as tendências por período"""
    print("\n=== CRIANDO GRÁFICO ===")
    
    periodos = [t['periodo'] for t in listaTendencias]
    generos = [t['generoTendencia'] for t in listaTendencias]
    quantidades = [t['quantidade'] for t in listaTendencias]
    
    plt.figure(figsize=(14, 10))
    plt.bar(range(len(periodos)), quantidades)
    
    for i, (periodo, genero, quantidade) in enumerate(zip(periodos, generos, quantidades)):
        plt.text(i, quantidade + max(quantidades) * 0.02, genero, 
                 ha='center', va='bottom', fontsize=8, rotation=45, weight='bold')
    
    plt.xlabel('Período de 5 Anos', fontsize=12)
    plt.ylabel('Número de Jogos do Gênero Mais Popular', fontsize=12)
    plt.title('Gênero Mais Popular por Período de 5 Anos', fontsize=14, weight='bold', pad=20)
    plt.xticks(range(len(periodos)), periodos, rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

def main():
    """Função principal que executa toda a análise"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    
    anoMinimo = dadosJogos['release_year'].min()
    anoMaximo = dadosJogos['release_year'].max()
    
    gruposAnos = criarGruposDeAnos(anoMinimo, anoMaximo)
    listaTendencias = analisarTendenciasPorPeriodo(dadosJogos, gruposAnos)
    
    exibirResumoTendencias(listaTendencias)
    analisarGenerosMaisFrequentes(listaTendencias)
    criarGraficoTendencias(listaTendencias)
    
    # Salvar resultados no MongoDB
    generosTendencia = [t['generoTendencia'] for t in listaTendencias]
    contagemTendencias = pd.Series(generosTendencia).value_counts()
    
    resultados = {
        'tendencias_por_periodo': listaTendencias,
        'generos_mais_frequentes': converterParaDict(contagemTendencias),
        'total_periodos_analisados': len(listaTendencias)
    }
    
    # Verifica se há valores válidos antes de converter
    anoMinimoValor = int(anoMinimo) if pd.notna(anoMinimo) else None
    anoMaximoValor = int(anoMaximo) if pd.notna(anoMaximo) else None
    
    metadados = {
        'ano_minimo': anoMinimoValor,
        'ano_maximo': anoMaximoValor,
        'tamanho_grupo_anos': 5
    }
    
    salvarResultado(colecao, 'Genero por Ano', 'genero_ano', resultados, metadados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()