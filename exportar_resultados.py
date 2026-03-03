import sys
import os

sys.path.append(os.path.dirname(__file__))
from mongo_utils import conectarMongoDB, listarResultados, exportarParaJSON

def exibirResultados(resultados):
    """Exibe os resultados de forma organizada"""
    if not resultados:
        print("\n⚠ Nenhum resultado encontrado no MongoDB")
        return
    
    print(f"\n{'='*60}")
    print(f"RESULTADOS ENCONTRADOS: {len(resultados)}")
    print(f"{'='*60}\n")
    
    for i, doc in enumerate(resultados, 1):
        print(f"{i}. {doc.get('nome_analise', 'N/A')}")
        print(f"   Tipo: {doc.get('tipo_analise', 'N/A')}")
        print(f"   Data: {doc.get('data_execucao', 'N/A')}")
        print(f"   ID: {doc.get('_id', 'N/A')}")
        print()

def main():
    """Função principal"""
    print("="*60)
    print("EXPORTADOR DE RESULTADOS - MongoDB")
    print("="*60)
    
    cliente, colecao = conectarMongoDB()
    
    if colecao is None:
        print("\n⚠ Não foi possível conectar ao MongoDB")
        print("  Verifique se o MongoDB está rodando ou configure MONGO_URI")
        return
    
    resultados = listarResultados(colecao)
    
    if not resultados:
        print("\n⚠ Nenhum resultado encontrado no banco de dados")
        if cliente:
            cliente.close()
        return
    
    exibirResultados(resultados)
    
    
    print("\n" + "="*60)
    print("EXPORTAÇÃO:")
    print("="*60)
    exportar = input("Deseja exportar os resultados para JSON? (s/n): ").strip().lower()
    
    if exportar in ['s', 'sim']:
        exportarParaJSON(colecao)
    else:
        print("\n✓ Nenhuma exportação realizada.")
    
    if cliente:
        cliente.close()
    
    print("\n" + "="*60)
    print("Operação concluída!")
    print("="*60)

if __name__ == "__main__":
    main()

