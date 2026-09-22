# CUSTOMER JOURNEY INTELIGENCE   

1. Tabela clientes
Contém o cadastro de cada cliente simulado. É a tabela raiz do modelo, todas as demais se relacionam com ela via id_cliente.

| Campo | Tipo | Nulo | Descrição | Valores/Regras |
|---|---|---|---|---|
|id_cliente|SERIAL|NÃO|Identificador único do cliente|PK, gerado automaticamente|
|nome|VARCHAR(100)|NÃO|Nome completo do cliente|Gerado sinteticamente via Faker pt_BR|
|idade|SMALLINT|NÃO|Idade do cliente em anos|Entre 18 e 85, definida pela persona|
|sexo|CHAR(1)|NÃO|Sexo do cliente|m ou f|
|cidade|VARCHAR(100)|NÃO|Cidade de residência|Gerada de acordo com UF|
|uf|CHAR(2)|NÃO|Estado de residência|Sigla com 2 caracteres. Ex: SP, PE|
|segmento|VARCHAR(30)|NÃO|Segmento bancário do cliente|varejo, uniclass, personnalité|
|tempo_relacionamento|SMALLINT|NÃO|Anos de relacionamento com o banco|≥ 0 Correlacionado com idade e tipo de conta|
|faixa_renda|VARCHAR(30)|NÃO|Faixa de renda mensal|até r$ 2.000, r$ 2.001 – r$ 5.000, r$ 5.001 – r$ 10.000, r$ 10.001 – r$ 20.000, acima de r$ 20.000|
|faixa_renda_cod|SMALLINT|NÃO|Código numérico ordenado da faixa de renda|0 a 4, em ordem crescente de renda|
|tipo_conta|VARCHAR(20)|NÃO|Tipo de conta bancária|corrente, digital, salário|
|app_favorito|VARCHAR(10)|NÃO|Sistema operacional do dispositivo principal|android ou ios|
|persona|VARCHAR(20)|NÃO|Perfil comportamental do cliente|jovem digital, cliente tradicional, investidor, idoso, premium|

2. Tabela sessoes
Registra cada abertura do aplicativo por um cliente. Uma sessão engloba todos os eventos ocorridos desde a abertura até o encerramento.

| Campo | Tipo | Nulo | Descrição | Valores/Regras |
|---|---|---|---|---|
id_sessao	SERIAL	NÃO	Identificador único da sessão	PK, gerado automaticamente
id_cliente	INT	NÃO	Cliente que realizou a sessão	FK → clientes.id_cliente
data_hora_inicio	TIMESTAMP	NÃO	Data e hora de início da sessão	Formato YYYY-MM-DD HH:MM:SS
data_hora_fim	TIMESTAMP	NÃO	Data e hora de encerramento da sessão	Calculada após a simulação dos eventos
hora_inicio	SMALLINT	NÃO	Hora do início da sessão	0 a 23. Derivado de data_hora_inicio
dia_inicio	VARCHAR(20)	NÃO	Dia da semana do início da sessão	Ex: segunda-feira, sábado. Derivado de data_hora_inicio
duracao_segundos	INT	NÃO	Duração total da sessão em segundos	≥ 0. Soma dos tempos de todos os eventos
dispositivo	VARCHAR(20)	NÃO	Sistema operacional usado na sessão	android ou ios
versao_app	VARCHAR(5)	NÃO	Versão do aplicativo na sessão	5.8, 5.9, 6.0 ou 6.1
qualidade_conexao	VARCHAR(50)	NÃO	Qualidade da conexão de internet	excelente, boa, regular ou ruim
abandonada	BOOLEAN	NÃO	Indica se a sessão foi encerrada sem logout	true = sessão abandonada. Default: false
motivo_encerramento	VARCHAR(20)	NÃO	Motivo pelo qual a sessão foi encerrada	logout, abandono ou timeout
score_experiencia	SMALLINT	NÃO	Score de experiência calculado da sessão	0 a 100. Inicia em 100 e sofre penalizações por erros, abandono e tempo excessivo
