import pandas as pd

# importar arquivos

clientes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\clientes.csv")
sessoes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\sessoes.csv")
eventos = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\eventos.csv")
erros = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\erros.csv")
avaliacoes = pd.read_csv("C:\\Projetos banco de dados\\aplicativo bancario\\avaliacoes.csv")

def view(df, nome):
    print("="*90)
    print(f"{nome}")
    print(df.head(5).to_string())
    print(df.info())
    print("="*90)
        
# ===============================
# TRANSFORMAÇÃO GERAL
# ===============================

# tirar espaços de todas as bases e deixar tudo minusculo
def limpar_texto(df):
    for coluna in df.select_dtypes(include="object").columns:
        df[coluna] = df[coluna].str.strip().str.lower()
    return df

clientes = limpar_texto(clientes)
sessoes = limpar_texto(sessoes)
eventos = limpar_texto(eventos)
erros = limpar_texto(erros)
avaliacoes = limpar_texto(avaliacoes)


# ===============================
# TRANSFORMAÇÃO TABELA CLIENTES
# ===============================

# transformar faixa renda e categorico
ordem = ["até r$ 2.000",
    "r$ 2.001 – r$ 5.000",
    "r$ 5.001 – r$ 10.000",
    "r$ 10.001 – r$ 20.000",
    "acima de r$ 20.000"]

clientes["faixa_renda"] = pd.Categorical(clientes["faixa_renda"], categories=ordem, ordered=True)

clientes["faixa_renda_cod"] = clientes["faixa_renda"].cat.codes # 0 a 4

# verificar outliers em tempo relacionamento e idade, apenas registro
q1_tr = clientes["tempo_relacionamento"].quantile(0.25)
q3_tr = clientes["tempo_relacionamento"].quantile(0.75)
IQR_tr = q3_tr - q1_tr
limite_baixo_tr = q1_tr - 1.5 * IQR_tr
limite_alto_tr = q3_tr + 1.5 * IQR_tr

outliers_tr = clientes[(clientes["tempo_relacionamento"] < limite_baixo_tr) | (clientes["tempo_relacionamento"] > limite_alto_tr)]

q1 = clientes["idade"].quantile(0.25)
q3 = clientes["idade"].quantile(0.75)
IQR = q3 - q1
limite_baixo = q1 - 1.5 * IQR
limite_alto = q3 + 1.5 * IQR

outliers_i = clientes[(clientes["idade"] < limite_baixo) | (clientes["idade"] > limite_alto)]

print("="*90)
print("OUTLIERS CLIENTES")
print(f"{len(outliers_tr)} encontrados em tempo_relacionamento")
print(f"Menor:\n {outliers_tr.min()}")
print(f"Maior:\n {outliers_tr.max()}")
print(f"{len(outliers_i)} encontrados em idade")
print(f"Menor:\n {outliers_i.min()}")
print(f"Maior:\n {outliers_i.max()}")
print("="*90)

# ===============================
# TRANSFORMAÇÃO TABELA SESSOES
# ===============================
# transformar versao app em string
sessoes["versao_app"] = sessoes["versao_app"].astype("string")

# transformar data inicio e fim em datetime de sessoes
sessoes["data_hora_inicio"] = pd.to_datetime(sessoes['data_hora_inicio'])
sessoes["data_hora_fim"] = pd.to_datetime(sessoes['data_hora_fim'])


# extrair hora dia (0-23) e dia semana (1-7) de data hora inicio e fim
# pode usar .dt.dayofweek para o dia_inicio, mas o panda coloca 0=segunda e 6=domingo 
sessoes["hora_inicio"] = sessoes["data_hora_inicio"].dt.hour
sessoes["dia_inicio"] = sessoes["data_hora_inicio"].dt.day_name(locale="pt_BR")

# verificar outliers em duracao segundos
q1_s = sessoes["duracao_segundos"].quantile(0.25)
q3_s = sessoes["duracao_segundos"].quantile(0.75)
IQR_s = q3_s - q1_s
limite_baixo_s = q1 - 1.5 * IQR_s
limite_alto_s = q3 + 1.5 * IQR_s

outliers_s = sessoes[(sessoes["duracao_segundos"] < limite_baixo_s) | (sessoes["duracao_segundos"] > limite_alto_s)]
print("="*90)
print("OUTLIERS SESSOES")
print(f"{len(outliers_s)} encontrados em duracao_segundos")
print(f"Menor:\n {outliers_s.min()}")
print(f"Maior:\n {outliers_s.max()}")
print(sessoes.info())
print("="*90)

# ===============================
# TRANSFORMAÇÃO TABELA EVENTOS
# ===============================

# verificar outliers em tempo segundos
q1_e = eventos["tempo_segundos"].quantile(0.25)
q3_e = eventos["tempo_segundos"].quantile(0.75)
IQR_e = q3_e - q1_e
limite_baixo_e = q1_e - 1.5 * IQR_e
limite_alto_e = q3_e + 1.5 * IQR_e

outliers_e = eventos[(eventos["tempo_segundos"] < limite_baixo_e) | (eventos["tempo_segundos"] > limite_alto_e)]

print("="*90)
print("OUTLIERS EVENTOS")
print(f"{len(outliers_e)} encontrados em tempo_segundos")
print(f"Menor:\n {outliers_e.min()}")
print(f"Maior:\n {outliers_e.max()}")
print("="*90)

# transformar timestamp em datetime de eventos
eventos["timestamp"] = pd.to_datetime(eventos["timestamp"])

# extrair hora dia (0-23) e dia semana (0-6) de timestamp
eventos["hora_dia"] = eventos["timestamp"].dt.hour
eventos["dia_semana"] = eventos["timestamp"].dt.day_name(locale="pt_BR")

# ===============================
# TRANSFORMAÇÃO TABELA ERROS
# ===============================
#  Substituir os valores nulos das colunas 
# ‘NaN' por ‘None’
erros["tempo_resolucao"] = erros["tempo_resolucao"].astype("Int64")
# ===============================
# TRANSFORMAÇÃO TABELA AVALIACOES
# ===============================

#  Substituir os valores nulos das colunas 
# ‘NaN' por ‘None’
avaliacoes["comentario"] = avaliacoes["comentario"].replace("nan", None)
# transformar data avaliacao em datetime
avaliacoes["data_avaliacao"] = pd.to_datetime(avaliacoes["data_avaliacao"])

for df, nome in [(clientes, "CLIENTES"),
                 (sessoes, "SESSOES"),
                 (eventos, "EVENTOS"),
                 (erros, "ERROS"),
                 (avaliacoes, "AVALIAÇÕES")]:
    view(df, nome)

# ===============================
# SALVAR BASES
# ===============================
bases = {
    "clientes" : clientes,
    "sessoes" : sessoes,
    "eventos" : eventos,
    "erros" : erros,
    "avaliacoes" : avaliacoes
}

for name, df in bases.items():
    df.to_csv(f"{name}_transformados.csv", index=False, encoding="utf-8-sig")
    print(f"{name} salvo")