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

def filtrarJogosAclamados(dadosJogos, padraoQualidade):
    """Filtra jogos que atendem ao padrão de qualidade"""
    print(f"Filtrando jogos com nota >= {padraoQualidade}...")
    
    jogosAclamados = dadosJogos[dadosJogos['steam_review_score'] >= padraoQualidade].copy()
    print(f"Jogos aclamados encontrados: {len(jogosAclamados)}")
    
    return jogosAclamados

def analisarSucessosPorAno(jogosAclamados, anoMinimo):
    """Analisa a distribuição de sucessos por ano"""
    print(f"Analisando sucessos a partir de {anoMinimo}...")
    
    jogosRecentes = jogosAclamados[jogosAclamados['release_year'] >= anoMinimo]
    contagemAnual = jogosRecentes['release_year'].value_counts().sort_index()
    
    anoDeOuro = contagemAnual.idxmax()
    numeroSucessos = contagemAnual.max()
    
    print(f"Ano de ouro: {anoDeOuro} com {numeroSucessos} jogos aclamados")
    
    return contagemAnual, anoDeOuro, numeroSucessos

def criarGraficoAscensao(contagemAnual, anoDeOuro, numeroSucessos, padraoQualidade):
    """Cria gráfico mostrando a ascensão dos jogos aclamados"""
    print("Criando gráfico de ascensão...")
    
    plt.figure(figsize=(14, 7))
    sns.barplot(x=contagemAnual.index, y=contagemAnual.values, palette='crest')
    
    plt.title(f'Ascensão dos Jogos Aclamados na Steam (Nota >= {padraoQualidade})', 
              fontsize=14, weight='bold')
    plt.xlabel('Ano de Lançamento', fontsize=12)
    plt.ylabel('Quantidade de Jogos de Sucesso', fontsize=12)
    plt.xticks(rotation=45)
    
    # Destacar o ano de ouro
    indiceAnoOuro = list(contagemAnual.index).index(anoDeOuro)
    plt.axvline(x=indiceAnoOuro, color='gold', linestyle='--', linewidth=2.5)
    plt.text(x=indiceAnoOuro, y=numeroSucessos, 
             s=f'  Ano de Ouro: {anoDeOuro}\n  ({numeroSucessos} jogos)', 
             horizontalalignment='left', color='darkgoldenrod', weight='bold')
    
    plt.tight_layout()
    plt.show()

def exibirResultados(contagemAnual, anoDeOuro, numeroSucessos, padraoQualidade):
    """Exibe os resultados da análise"""
    print("\n" + "="*60)
    print("ANÁLISE DO ANO DE OURO DOS JOGOS NA STEAM")
    print("="*60)
    print(f"Padrão de qualidade: Nota >= {padraoQualidade}")
    print(f"Ano de ouro: {anoDeOuro}")
    print(f"Número de jogos aclamados em {anoDeOuro}: {numeroSucessos}")
    
    print(f"\nTop 5 anos com mais jogos aclamados:")
    top5Anos = contagemAnual.head(5)
    for i, (ano, quantidade) in enumerate(top5Anos.items(), 1):
        print(f"  {i}. {ano}: {quantidade} jogos")
    
    print(f"\nTotal de jogos aclamados analisados: {contagemAnual.sum()}")
    print(f"Período analisado: {contagemAnual.index.min()} - {contagemAnual.index.max()}")

def main():
    """Função principal que executa toda a análise"""
    # Conectar ao MongoDB
    cliente, colecao = conectarMongoDB()
    
    dadosJogos = carregarDados()
    
    if dadosJogos is None:
        if cliente:
            cliente.close()
        return
    
    padraoQualidade = 80
    anoMinimo = 2000
    
    jogosAclamados = filtrarJogosAclamados(dadosJogos, padraoQualidade)
    contagemAnual, anoDeOuro, numeroSucessos = analisarSucessosPorAno(jogosAclamados, anoMinimo)
    
    criarGraficoAscensao(contagemAnual, anoDeOuro, numeroSucessos, padraoQualidade)
    exibirResultados(contagemAnual, anoDeOuro, numeroSucessos, padraoQualidade)
    
    # Salvar resultados no MongoDB
    # Verifica se há dados válidos antes de converter
    anoOuroValor = int(anoDeOuro) if pd.notna(anoDeOuro) else None
    numeroSucessosValor = int(numeroSucessos) if pd.notna(numeroSucessos) else 0
    totalJogosValor = int(contagemAnual.sum()) if len(contagemAnual) > 0 else 0
    
    resultados = {
        'ano_ouro': anoOuroValor,
        'numero_sucessos_ano_ouro': numeroSucessosValor,
        'contagem_anual': converterParaDict(contagemAnual),
        'total_jogos_aclamados': totalJogosValor
    }
    
    # Converte valores do index para int (podem ser numpy.int64)
    anoMin = int(contagemAnual.index.min()) if len(contagemAnual) > 0 else None
    anoMax = int(contagemAnual.index.max()) if len(contagemAnual) > 0 else None
    
    metadados = {
        'padrao_qualidade': int(padraoQualidade),
        'ano_minimo': int(anoMinimo),
        'periodo_analisado': f"{anoMin}-{anoMax}" if anoMin and anoMax else "N/A"
    }
    
    salvarResultado(colecao, 'Ano de Ouro Jogos', 'ano_nota', resultados, metadados)
    
    if cliente:
        cliente.close()
    
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()