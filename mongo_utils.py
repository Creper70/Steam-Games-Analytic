from pymongo import MongoClient
from datetime import datetime
import os
import json
import pandas as pd

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = 'bigdata_steam'
COLLECTION_RESULTADOS = 'resultados_analises'

def conectarMongoDB():
    """Conecta ao MongoDB e retorna o cliente e a coleção"""
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        cliente.server_info()
        banco = cliente[DATABASE_NAME]
        colecao = banco[COLLECTION_RESULTADOS]
        print(f"✓ Conectado ao MongoDB: {DATABASE_NAME}")
        return cliente, colecao
    except Exception as e:
        print(f"⚠ MongoDB não disponível: {MONGO_URI}")
        print(f"  Os scripts continuarão funcionando, mas os resultados não serão salvos.")
        print(f"  Para usar MongoDB, inicie o servidor ou configure MONGO_URI para um servidor remoto.")
        return None, None

def limparParaMongoDB(dados):
    """Converte dados para formato compatível com MongoDB"""
    import numpy as np
    
    try:
        if pd.isna(dados):
            return None
    except (TypeError, ValueError):
        pass
    
    if isinstance(dados, dict):
        return {str(key): limparParaMongoDB(value) 
                for key, value in dados.items()}
    elif isinstance(dados, list):
        return [limparParaMongoDB(item) for item in dados]
    elif isinstance(dados, np.ndarray):
        return limparParaMongoDB(dados.tolist())
    elif isinstance(dados, np.integer):
        return int(dados)
    elif isinstance(dados, np.floating):
        return float(dados)
    elif isinstance(dados, np.bool_):
        return bool(dados)
    elif isinstance(dados, (str, int, float, bool, type(None))):
        return dados
    else:
        try:
            if hasattr(dados, 'item'):
                return limparParaMongoDB(dados.item())
            return str(dados)
        except:
            return None

def salvarResultado(colecao, nomeAnalise, tipoAnalise, resultados, metadados=None):
    """Salva os resultados de uma análise no MongoDB"""
    if colecao is None:
        return False
    
    documento = None
    try:
        resultados_limpos = limparParaMongoDB(resultados)
        metadados_limpos = limparParaMongoDB(metadados) if metadados else {}
        
        documento = {
            'nome_analise': str(nomeAnalise),
            'tipo_analise': str(tipoAnalise),
            'resultados': resultados_limpos,
            'data_execucao': datetime.now(),
            'metadados': metadados_limpos
        }
        
        resultado = colecao.insert_one(documento)
        print(f"✓ Resultados salvos no MongoDB (ID: {resultado.inserted_id})")
        return True
    except Exception as e:
        print(f"⚠ Erro ao salvar no MongoDB: {str(e)}")
        return False

def converterParaDict(dados, profundidade=0):
    """Converte dados do pandas para formato compatível com MongoDB"""
    if profundidade > 10:
        return {'erro': 'Profundidade máxima de recursão atingida'}
    
    try:
        import numpy as np
        
        if hasattr(dados, 'to_dict') and hasattr(dados, 'columns'):
            df_copy = dados.copy()
            for col in df_copy.columns:
                if df_copy[col].dtype.name == 'category':
                    df_copy[col] = df_copy[col].astype(str)
                df_copy[col] = df_copy[col].where(pd.notna(df_copy[col]), None)
            
            return {
                'tipo': 'dataframe',
                'dados': df_copy.to_dict('records'),
                'colunas': df_copy.columns.tolist()
            }
        elif hasattr(dados, 'to_dict') and hasattr(dados, 'index'):
            series_copy = dados.copy()
            if series_copy.dtype.name == 'category':
                series_copy = series_copy.astype(str)
            series_copy = series_copy.where(pd.notna(series_copy), None)
            
            dict_series = {}
            for key, value in series_copy.to_dict().items():
                key_str = str(limparParaMongoDB(key))
                dict_series[key_str] = limparParaMongoDB(value)
            
            index_list = series_copy.index.tolist() if hasattr(series_copy.index, 'tolist') else list(series_copy.index)
            index_list = [limparParaMongoDB(x) for x in index_list]
            
            return {
                'tipo': 'series',
                'dados': dict_series,
                'index': index_list
            }
        elif isinstance(dados, dict):
            resultado = {}
            for key, value in dados.items():
                resultado[str(key)] = converterParaDict(value, profundidade + 1)
            return resultado
        elif isinstance(dados, list):
            return [converterParaDict(item, profundidade + 1) for item in dados]
        else:
            if pd.isna(dados) if hasattr(pd, 'isna') else False:
                return None
            if hasattr(np, 'integer') and isinstance(dados, np.integer):
                return int(dados)
            if hasattr(np, 'floating') and isinstance(dados, np.floating):
                return float(dados)
            if pd.api.types.is_categorical_dtype(type(dados)):
                return str(dados)
            return dados
    except Exception as e:
        try:
            return {'valor': str(dados), 'erro_conversao': str(e)}
        except:
            return {'erro_conversao': str(e)}

def listarResultados(colecao, tipoAnalise=None, limite=None):
    """Lista todos os resultados salvos no MongoDB"""
    if colecao is None:
        print("⚠ MongoDB não disponível")
        return []
    
    try:
        query = {}
        if tipoAnalise:
            query['tipo_analise'] = tipoAnalise
        
        cursor = colecao.find(query).sort('data_execucao', -1)
        if limite:
            cursor = cursor.limit(limite)
        
        resultados = list(cursor)
        return resultados
    except Exception as e:
        print(f"Erro ao listar resultados: {e}")
        return []

def exportarParaJSON(colecao, nomeArquivo='resultados_analises.json', tipoAnalise=None):
    """Exporta todos os resultados para um arquivo JSON"""
    resultados = listarResultados(colecao, tipoAnalise)
    
    if not resultados:
        print("Nenhum resultado encontrado para exportar")
        return False
    
    try:
        for resultado in resultados:
            if '_id' in resultado:
                resultado['_id'] = str(resultado['_id'])
            if 'data_execucao' in resultado:
                resultado['data_execucao'] = resultado['data_execucao'].isoformat()
        
        caminhoArquivo = os.path.join(os.path.dirname(__file__), nomeArquivo)
        with open(caminhoArquivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Resultados exportados para: {caminhoArquivo}")
        print(f"  Total de documentos: {len(resultados)}")
        return True
    except Exception as e:
        print(f"Erro ao exportar para JSON: {e}")
        return False

