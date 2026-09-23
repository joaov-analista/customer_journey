-- ================
-- CUSTOMER JOURNEY INTELLIGENCE
-- ================

-- Onde os clientes encontram mais dificuldades?
CREATE VIEW vw_dificuldade_p_funcionalidade AS
SELECT 
	funcionalidade,
	COUNT(*) AS total_eventos,
	SUM(teve_erro::int) AS total_erros,
	ROUND(AVG(teve_erro::int) * 100, 2) AS pct_taxa_erro,
	ROUND(AVG(tempo_segundos), 1) AS media_tempo_segundos,
	COUNT(DISTINCT id_sessao) AS sessoes_afetadas
FROM eventos
GROUP BY funcionalidade
ORDER BY pct_taxa_erro DESC;

SELECT * FROM vw_dificuldade_p_funcionalidade LIMIT 10;

-- Quais funcionalidades geram maior frustração?
CREATE VIEW vw_frustacao_p_funcionalidade AS
SELECT 
	e.funcionalidade,
	ROUND(AVG(s.score_experiencia), 1) AS score_medio,
	ROUND(AVG(a.nps), 1) AS nps_medio,
	ROUND(AVG(a.csat), 1) AS csat_medio,
	COUNT(DISTINCT er.id_erro) AS qtd_erro,
	SUM(CASE WHEN er.resolvido = false
		THEN 1 ELSE 0 END) AS erros_nao_resolvido
FROM eventos e
JOIN sessoes s ON e.id_sessao = s.id_sessao
LEFT JOIN erros er ON er.id_evento = e.id_evento
LEFT JOIN avaliacoes a ON a.id_sessao = s.id_sessao AND a.aceitou_pesquisa = true
GROUP BY e.funcionalidade
ORDER BY score_medio ASC;

SELECT * FROM vw_frustacao_p_funcionalidade LIMIT 10;

--Quais perfis possuem pior experiência?
CREATE VIEW vw_experiencia_p_perfil AS
SELECT
	c.persona,
	c.segmento,
	c.faixa_renda,
	c.app_favorito,
	COUNT(DISTINCT s.id_sessao) AS total_sessoes,
	ROUND(AVG(s.score_experiencia), 1) AS score_medio,
	ROUND(AVG(a.nps), 2) AS nps_medio,
	ROUND(AVG(a.csat), 2) AS csat_medio,
	ROUND(AVG(s.abandonada::int) * 100, 2) AS pct_sessao_abandonada,
	ROUND((SUM(CASE WHEN a.nps >= 9 THEN 1 ELSE 0 END) -
		   SUM(CASE WHEN a.nps <= 6 THEN 1 ELSE 0 END))
		   * 100.0 / NULLIF(COUNT(a.id_avaliacao), 0), 1) AS nps_score
FROM clientes c
JOIN sessoes s ON c.id_cliente = s.id_cliente
LEFT JOIN avaliacoes a ON a.id_sessao = s.id_sessao AND a.aceitou_pesquisa = true
GROUP BY c.persona, c.segmento, c.faixa_renda, c.app_favorito
ORDER BY score_medio ASC;

SELECT * FROM vw_experiencia_p_perfil LIMIT 10;

-- Em qual etapa ocorre o maior abandono?
CREATE VIEW vw_etapa_com_mais_abandono AS
SELECT 
	e.funcionalidade,
	COUNT(*) AS total_abandonos,
	ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_do_total,
	ROUND(AVG(e.ordem), 1) AS ordem_media_abandono
FROM eventos e
JOIN sessoes s ON s.id_sessao = e.id_sessao
WHERE s.abandonada = true AND e.ordem = (
	SELECT MAX(e2.ordem)
	FROM eventos e2
	WHERE e2.id_sessao = e.id_sessao
)
GROUP BY e.funcionalidade
ORDER BY total_abandonos DESC;

SELECT * FROM vw_etapa_com_mais_abandono;

-- Quanto tempo o usuário leva em cada funcionalidade?
CREATE VIEW vw_tempo_por_funcionalidade AS
SELECT
	funcionalidade,
	status,
	COUNT(*) AS total_eventos,
	ROUND(AVG(tempo_segundos), 1) AS media_tempo_segundos,
	MIN(tempo_segundos) AS minimo_tempo,
	MAX(tempo_segundos) AS maximo_tempo
FROM eventos
GROUP BY funcionalidade, status
ORDER BY funcionalidade, status;

SELECT *FROM vw_tempo_por_funcionalidade LIMIT 10;

-- Quais caminhos levam a uma experiência positiva?
CREATE VIEW vw_caminhos_esperiencia_positiva AS
SELECT 
	s.motivo_encerramento,
	s.qualidade_conexao,
	s.versao_app,
	c.persona,
	COUNT(DISTINCT s.id_sessao) AS total_sessoes,
	ROUND(AVG( s.score_experiencia), 1) AS score_medio,
	ROUND(AVG( a.nps), 2) AS nps_medio,
	SUM(CASE WHEN s.score_experiencia >=80 
		THEN 1 ELSE 0 END) AS sessoes_positivas,
	ROUND(SUM(CASE WHEN s.score_experiencia >=80
		THEN 1 ELSE 0 END) * 100.0 
		/ COUNT(DISTINCT s.id_sessao), 1) AS pct_sessoes_positivas
FROM sessoes s
JOIN clientes c ON c.id_cliente = s.id_cliente
LEFT JOIN avaliacoes a ON a.id_sessao = s.id_sessao AND a.aceitou_pesquisa = true
GROUP BY s.motivo_encerramento, s.qualidade_conexao, s.versao_app, c.persona
ORDER BY score_medio DESC;

SELECT * FROM vw_caminhos_esperiencia_positiva LIMIT 10;

-- Quais assuntos aparecem com maior frequência nas reclamações?
CREATE VIEW vw_assuntos_com_maior_frequencia AS
SELECT 
	a.comentario,
	a.nps,
	a.csat,
	a.score_experiencia,
	c.persona,
	c.segmento,
	s.motivo_encerramento,
	s.qualidade_conexao
FROM avaliacoes a
JOIN sessoes s ON s.id_sessao = a.id_sessao
JOIN clientes c ON c.id_cliente = s.id_cliente
WHERE a.comentario IS NOT NULL
ORDER BY a.nps ASC;

SELECT * FROM vw_assuntos_com_maior_frequencia LIMIT 10;

-- O sentimento varia conforme a funcionalidade?
CREATE VIEW vw_sentimento_p_funcionalidade AS
SELECT
	e.funcionalidade,
	ROUND(AVG(a.nps), 2) AS nps_medio,
	ROUND(AVG(a.csat), 2) AS csat_medio,
	ROUND(AVG(a.score_experiencia), 2) AS score_medio,
	COUNT(DISTINCT a.id_avaliacao) AS avaliacoes,
	SUM(CASE WHEN a.nps <=6 THEN 1 ELSE 0 END) AS detratores,
	SUM(CASE WHEN a.nps >=9 THEN 1 ELSE 0 END) AS promotores,
	ROUND((SUM(CASE WHEN a.nps <=6 THEN 1 ELSE 0 END) -
		  SUM(CASE WHEN a.nps >=9 THEN 1 ELSE 0 END))
		  * 100.0 / NULLIF (COUNT(a.id_avaliacao), 0), 1) AS nps_score
FROM eventos e
JOIN avaliacoes a ON a.id_sessao = e.id_sessao
	AND a.aceitou_pesquisa = true
GROUP BY e.funcionalidade
ORDER BY nps_score ASC;

SELECT * FROM vw_sentimento_p_funcionalidade LIMIT 10;

-- Existem padrões recorrentes?
-- Qual melhoria deve ser feita primeiro?
-- Quais problemas afetam mais clientes?
CREATE VIEW vw_padroes AS
SELECT
	er.tipo_erro,
	e.funcionalidade,
	COUNT(DISTINCT er.id_erro) AS total_erros,
	COUNT(DISTINCT s.id_cliente) AS clientes_afetados,
	COUNT(DISTINCT e.id_sessao) AS sessoes_afetadas,
	ROUND(AVG(s.score_experiencia), 1) AS score_medio_sessao,
	ROUND(AVG(a.nps), 2) AS nps_medio,
	ROUND(AVG(er.resolvido::int) * 100, 1) AS pct_resolucao,
	ROUND(AVG(er.tentativas), 1) AS media_tentativas,
	ROUND((SUM(CASE WHEN a.nps <=6 THEN 1 ELSE 0 END) -
		  SUM(CASE WHEN a.nps >=9 THEN 1 ELSE 0 END))
		  * 100.0 / NULLIF (COUNT(a.id_avaliacao), 0), 1) AS nps_score
FROM erros er
JOIN eventos e ON e.id_evento = er.id_evento
JOIN sessoes s ON s.id_sessao = er.id_sessao
LEFT JOIN avaliacoes a ON a.id_sessao = s.id_sessao
	AND a.aceitou_pesquisa = true
GROUP BY er.tipo_erro, e.funcionalidade
ORDER BY clientes_afetados DESC, score_medio_sessao ASC;

SELECT * FROM vw_padroes LIMIT 10;

-- Qual funcionalidade gera maior impacto no NPS?
CREATE VIEW vw_nps_p_funcionalidade AS
SELECT 
	e.funcionalidade,
	COUNT(DISTINCT s.id_sessao) AS sessoes_com_funcionalidade,
	ROUND(AVG(CASE WHEN e.teve_erro = false 
		  THEN a.nps END), 2) AS nps_medio_sem_erro,
	ROUND(AVG(CASE WHEN e.teve_erro = true
		  THEN a.nps END), 2) AS nps_com_erro,
	ROUND(AVG(CASE WHEN e.teve_erro = false THEN a.nps END) -
          AVG(CASE WHEN e.teve_erro = true THEN a.nps END), 2) AS delta_nps,
	ROUND((SUM(CASE WHEN a.nps <=6 THEN 1 ELSE 0 END) -
		  SUM(CASE WHEN a.nps >=9 THEN 1 ELSE 0 END))
		  * 100.0 / NULLIF (COUNT(a.id_avaliacao), 0), 1) AS nps_score
FROM eventos e
JOIN sessoes s ON s.id_sessao = e.id_sessao
JOIN avaliacoes a ON a.id_sessao = s.id_sessao
	AND a.aceitou_pesquisa = true
GROUP BY e.funcionalidade
ORDER BY delta_nps DESC;
	
SELECT * FROM vw_nps_p_funcionalidade LIMIT 10;

-- qual hora do dia tem mais erros de funcionalidade
CREATE VIEW vw_hora_com_mais_erros AS
SELECT
	e.funcionalidade,
	e.hora_dia,
	COUNT(DISTINCT er.id_erro) AS total_erros,
	COUNT(DISTINCT e.id_evento) AS total_eventos, 
	ROUND(AVG(e.tempo_segundos), 1) AS media_tempo_segundos,
	ROUND(AVG(s.score_experiencia), 1) AS media_score_experiencia
FROM eventos e
JOIN sessoes s ON s.id_sessao = e.id_sessao
JOIN erros er ON er.id_evento = e.id_evento
WHERE e.teve_erro = true
GROUP BY e.funcionalidade, e.hora_dia
ORDER BY total_erros DESC;

SELECT * FROM vw_hora_com_mais_erros LIMIT 10;

-- qual dia da semana tem mais erros
CREATE VIEW vw_dia_semana_mais_erros AS 
SELECT
	e.funcionalidade,
	e.dia_semana,
	COUNT(DISTINCT er.id_erro) AS total_erros,
	COUNT(DISTINCT e.id_evento) AS total_eventos,
	ROUND(AVG(e.tempo_segundos), 1) AS media_tempo_segundos,
	ROUND(AVG(s.score_experiencia), 1) AS medis_score_experiencia
FROM eventos e
JOIN sessoes s ON s.id_sessao = e.id_sessao
JOIN erros er ON er.id_evento = e.id_evento
WHERE e.teve_erro = true
GROUP BY e.funcionalidade, e.dia_semana
ORDER BY total_erros DESC;

SELECT * FROM vw_dia_semana_mais_erros LIMIT 10;
