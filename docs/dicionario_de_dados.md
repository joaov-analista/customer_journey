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
|id_sessao|SERIAL|NÃO|Identificador único da sessão|PK, gerado automaticamente|
|id_cliente|INT|NÃO|Cliente que realizou a sessão|FK → clientes.id_cliente|
|data_hora_inicio|TIMESTAMP|NÃO|Data e hora de início da sessão|Formato YYYY-MM-DD HH:MM:SS|
|data_hora_fim|TIMESTAMP|NÃO|Data e hora de encerramento da sessão|Calculada após a simulação dos eventos|
|hora_inicio|SMALLINT|NÃO|Hora do início da sessão|0 a 23. Derivado de data_hora_inicio|
|dia_inicio|VARCHAR(20)|NÃO|Dia da semana do início da sessão|Ex: segunda-feira, sábado. Derivado de data_hora_inicio|
|duracao_segundos|INT|NÃO|Duração total da sessão em segundos|≥ 0. Soma dos tempos de todos os eventos|
|dispositivo|VARCHAR(20)|NÃO|Sistema operacional usado na sessão|android ou ios|
|versao_app|VARCHAR(5)|NÃO|Versão do aplicativo na sessão|5.8, 5.9, 6.0 ou 6.1|
|qualidade_conexao|VARCHAR(50)|NÃO|Qualidade da conexão de internet|excelente, boa, regular ou ruim|
|abandonada|BOOLEAN|NÃO|Indica se a sessão foi encerrada sem logout|true = sessão abandonada. Default: false|
|motivo_encerramento|VARCHAR(20)|NÃO|Motivo pelo qual a sessão foi encerrada|logout, abandono ou timeout|
|score_experiencia|SMALLINT|NÃO|Score de experiência calculado da sessão|0 a 100. Inicia em 100 e sofre penalizações por erros, abandono e tempo excessivo|

3. Tabela eventos  
Registra cada interação do cliente com uma funcionalidade dentro de uma sessão. É a tabela central do modelo e a mais volumosa.

| Campo | Tipo | Nulo | Descrição | Valores/Regras |
|---|---|---|---|---|
|id_evento|SERIAL|NÃO|Identificador único do evento|PK, gerado automaticamente|
|id_sessao|INT|NÃO|Sessão à qual o evento pertence|FK → sessoes.id_sessao|
|ordem|SMALLINT|NÃO|Sequência do evento dentro da sessão|≥ 1. Inicia em 1 e é incrementado a cada evento da sessão|
|timestamp|TIMESTAMP|NÃO|Data e hora exata do evento|Formato YYYY-MM-DD HH:MM:SS|
|hora_dia|SMALLINT|NÃO|Hora do evento|0 a 23. Derivado de timestamp|
|dia_semana|VARCHAR(20)|NÃO|Dia da semana do evento|Ex: segunda-feira. Derivado de timestamp|
|funcionalidade|VARCHAR(20)|NÃO|Tela ou funcionalidade acessada|login, home, saldo, pix, pagamento, cartao, investimentos, chat, logout|
|acao|VARCHAR(30)|NÃO|Ação realizada pelo cliente na funcionalidade|Ex: confirmar, visualizar, erro, repetir_confirmar|
|tempo_segundos|INT|NÃO|Tempo gasto no evento em segundos|≥ 1. Varia conforme persona, conexão e ocorrência de erro|
|status|VARCHAR(20)|NÃO|Resultado do evento|sucesso, erro ou abandono|
|teve_erro|BOOLEAN|NÃO|Indica se o evento resultou em erro|true = evento com erro. Default: false|

4. Tabela erros  
Registra os erros gerados pelos eventos. Derivada da tabela eventos, toda linha aqui corresponde a um evento com teve_erro = true.

| Campo | Tipo | Nulo | Descrição | Valores/Regras |
|---|---|---|---|---|
|id_erro|SERIAL|NÃO|Identificador único do erro|PK, gerado automaticamente|
|id_evento|INT|NÃO|Evento que originou o erro|FK → eventos.id_evento|
|id_sessao|INT|NÃO|Sessão onde o erro ocorreu|FK → sessoes.id_sessao. Atalho para evitar joins extras|
|tipo_erro|VARCHAR(30)|NÃO|Classificação do erro|timeout, falha_autenticacao, erro_interno, conexao_interrompida, servico_indisponivel|
|codigo_erro|VARCHAR(30)|NÃO|Código técnico do erro|Ex: err_timeout_408, err_auth_401, err_internal_500|
|tempo_resolucao|INT|SIM|Tempo em segundos até a resolução do erro|NULL quando não resolvido|
|resolvido|BOOLEAN|NÃO|Indica se o cliente conseguiu resolver o erro|true = retentativa bem-sucedida. Default: false|
|tentativas|SMALLINT|NÃO|Número de tentativas realizadas pelo cliente|≥ 1. Máximo de 3 tentativas por regra de negócio|

5. Tabela avaliacoes  
Registra as avaliações de experiência coletadas ao fim de algumas sessões. Nem toda sessão gera avaliação, apenas 25% dos clientes são convidados e a aceitação é probabilística por persona.

| Campo | Tipo | Nulo | Descrição | Valores/Regras |
|---|---|---|---|---|
|id_avaliacao|SERIAL|NÃO|Identificador único da avaliação|PK, gerado automaticamente|
|id_sessao|INT|NÃO|Sessão avaliada|FK → sessoes.id_sessao. Unique: uma avaliação por sessão|
|nps|SMALLINT|NÃO|Nota de recomendação|0 a 10. Derivado do score_experiencia|
|csat|SMALLINT|NÃO|Nota de satisfação|1 a 5. Derivado do score_experiencia|
|comentario|TEXT|SIM|Comentário textual do cliente|Gerado apenas quando NPS ≤ 6 ou CSAT ≤ 3. NULL nos demais casos|
|aceitou_pesquisa|BOOLEAN|NÃO|Indica se o cliente respondeu a pesquisa|true = aceitou. Probabilidade varia por persona|
|score_experiencia|SMALLINT|NÃO|Score de experiência da sessão avaliada|0 a 100. Copiado de sessoes.score_experiencia para facilitar análises diretas na tabela|
|data_avaliacao|TIMESTAMP|NÃO|Data e hora em que a avaliação foi registrada|Entre 10 e 90 segundos após sessoes.data_hora_fim|
