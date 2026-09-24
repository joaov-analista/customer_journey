import pandas as pd

# importar arquivos

clientes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\clientes.csv")
sessoes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\sessoes.csv")
eventos = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\eventos.csv")
erros = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\erros.csv")
avaliacoes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\avaliacoes.csv")

def validacao(dfs):
    print("="*50)
    print("Tipos de dados")
    print(dfs.info())
    print("QTD Nulos")
    print(dfs.isnull().sum())
    print("QTD de valores unicos")
    print(dfs.nunique())
    print("="*50)
    
print("TABELA CLIENTES")
print(clientes.head().to_string())
print("QTD duplicados em id_cliente")
print(clientes["id_cliente"].duplicated().sum())
validacao(clientes)
print("TABELA SESSÕES")
print(sessoes.head().to_string())
print("QTD duplicados em id_sessao")
print(sessoes["id_sessao"].duplicated().sum())
print("QTD duplicados em id_cliente")
print(sessoes["id_cliente"].duplicated().sum())
validacao(sessoes)
print("TABELA EVENTOS")
print(eventos.head().to_string())
print("QTD duplicados em id_sessao")
print(eventos["id_sessao"].duplicated().sum())
validacao(eventos)
print("TABELA ERROS")
print(erros.head().to_string())
print("QTD duplicados em id_evento")
print(erros["id_evento"].duplicated().sum())
print("QTD duplicados em id_sessao")
print(erros["id_sessao"].duplicated().sum())
validacao(erros)
print("TABELA AVALIAÇÕES")
print(avaliacoes.head().to_string())
validacao(avaliacoes)

# verifica se todos os clientes em sessoes constam na tabela de clientes
sessoes["clientes_invalidos"] = sessoes["id_cliente"].isin(clientes["id_cliente"])
print(sessoes['clientes_invalidos'].value_counts())

# verifica se toda sessao de eventos consta na tabela sessao
eventos["sessao_invalida"] = eventos["id_sessao"].isin(sessoes["id_sessao"])
print(eventos["sessao_invalida"].value_counts())

# verifica se todo evento e sessao de erros consta na tabela de evento e erros
erros["evento_invalido"] = erros["id_evento"].isin(eventos["id_evento"])
erros["sessao_invalida"] = erros["id_sessao"].isin(sessoes["id_sessao"])
print(erros["evento_invalido"].value_counts())
print(erros["sessao_invalida"].value_counts())

# verifica se toda sessao em avaliacoes consta na tabela de sessoes
avaliacoes["sessao_invalida"] = avaliacoes["id_sessao"].isin(sessoes["id_sessao"])
print(avaliacoes["sessao_invalida"].value_counts())

