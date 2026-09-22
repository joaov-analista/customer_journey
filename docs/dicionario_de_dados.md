# CUSTOMER JOURNEY INTELIGENCE   

1. Tabela clientes
Campo | Tipo | Descrição | Regra/Observação
id_cliente | INT | Identificador único de cliente | SERIAL PRIMARY KEY
nome | VARCHAR(100) | Nome do cliente | NOT NULL
idade | SMALLINT |  Idade do cliente | NOT NULL
sexo | CHAR(1) | Sexo do cliente | NOT NULL CHECK (sexo IN ('m', 'f'))
cidade | VARCHAR(100) | Cidade de residência do cliente | NOT NULL
uf | CHAR(2) | Estado de residência do cliente | NOT NULL
segmento | VARCHAR(30) | | NOT NULL
tempo_relacionamento | SMALLINT | | NOT NULL CHECK (tempo_relacionamento >= 0)
faixa_renda | VARCHAR(30) | | NOT NULL
tipo_conta | VARCHAR(20) | | NOT NULL
app_favorito | VARCHAR(10) | | NOT NULL
persona | VARCHAR(20) | | NOT NULL
faixa_renda_cod | SMALLINT | | NOT NULL CHECK (faixa_renda_cod BETWEEN 0 AND 4)
