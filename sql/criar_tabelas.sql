-- ================
-- CUSTOMER JOURNEY INTELIGENCE
-- ================

-- 1. CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
	id_cliente SERIAL PRIMARY KEY,
	nome VARCHAR(100) NOT NULL,
	idade SMALLINT NOT NULL,
	sexo CHAR(1) NOT NULL CHECK (sexo IN ('m', 'f')),
	cidade VARCHAR(100) NOT NULL,
	uf CHAR(2) NOT NULL,
	segmento VARCHAR(30) NOT NULL,
	tempo_relacionamento SMALLINT NOT NULL CHECK (tempo_relacionamento >= 0),
	faixa_renda VARCHAR(30) NOT NULL,
	tipo_conta VARCHAR(20) NOT NULL,
	app_favorito VARCHAR(10) NOT NULL,
	persona VARCHAR(20) NOT NULL,
	faixa_renda_cod SMALLINT NOT NULL CHECK (faixa_renda_cod BETWEEN 0 AND 4)	
);

-- 2. SESSOES
CREATE TABLE IF NOT EXISTS sessoes (
	id_sessao SERIAL PRIMARY KEY,
	id_cliente INT NOT NULL REFERENCES clientes(id_cliente),
	data_hora_inicio TIMESTAMP NOT NULL,
	dispositivo VARCHAR(20) NOT NULL,
	versao_app VARCHAR(5) NOT NULL,
	qualidade_conexao VARCHAR(50) NOT NULL,
	duracao_segundos INT NOT NULL CHECK (duracao_segundos >= 0),
	data_hora_fim TIMESTAMP NOT NULL,
	abandonada BOOLEAN NOT NULL DEFAULT FALSE,
	motivo_encerramento VARCHAR(20) NOT NULL,
	score_experiencia SMALLINT NOT NULL CHECK (score_experiencia BETWEEN 0 AND 100),
	hora_inicio SMALLINT NOT NULL CHECK (hora_inicio BETWEEN 0 AND 23),
	dia_inicio VARCHAR(20) NOT NULL 
);

-- 3. EVENTOS 
CREATE TABLE IF NOT EXISTS eventos (
	id_evento SERIAL PRIMARY KEY,
	id_sessao INT NOT NULL REFERENCES sessoes(id_sessao),
	ordem SMALLINT NOT NULL CHECK (ordem >= 1),
	timestamp TIMESTAMP NOT NULL,
	funcionalidade VARCHAR(20) NOT NULL,
	acao VARCHAR(30) NOT NULL,
	tempo_segundos INT NOT NULL CHECK (tempo_segundos >= 1),
	status VARCHAR(20) NOT NULL,
	teve_erro BOOLEAN NOT NULL DEFAULT FALSE,
	hora_dia SMALLINT NOT NULL CHECK (hora_dia BETWEEN 0 AND 23),
	dia_semana VARCHAR(20) NOT NULL
);

-- 4. ERROS
CREATE TABLE IF NOT EXISTS erros (
	id_erro SERIAL PRIMARY KEY,
	id_evento INT NOT NULL REFERENCES eventos(id_evento),
	id_sessao INT NOT NULL REFERENCES sessoes(id_sessao),
	tipo_erro VARCHAR(30) NOT NULL,
	codigo_erro VARCHAR(30) NOT NULL,
	tempo_resolucao INT  NULL ,
	resolvido BOOLEAN NOT NULL DEFAULT FALSE,
	tentativas SMALLINT NOT NULL DEFAULT 1
);

-- 5. AVALIAÇÕES 
CREATE TABLE IF NOT EXISTS avaliacoes (
	id_avaliacao SERIAL PRIMARY KEY,
	id_sessao INT NOT NULL UNIQUE REFERENCES sessoes(id_sessao),
	nps SMALLINT NOT NULL CHECK (nps BETWEEN 0 AND 10),
	csat SMALLINT NOT NULL CHECK (csat BETWEEN 1 AND 5), 
	comentario TEXT NULL,
	aceitou_pesquisa BOOLEAN NOT NULL DEFAULT FALSE,
	score_experiencia SMALLINT NOT NULL CHECK (score_experiencia BETWEEN 0 AND 100),
	data_avaliacao TIMESTAMP NOT NULL
);