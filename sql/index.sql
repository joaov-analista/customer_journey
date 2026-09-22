-- ==============
-- INDICES
-- =============

-- buscas por clientes
CREATE INDEX idx_sessoes_cliente ON sessoes(id_cliente);

-- buscas por sessao nos eventos
CREATE INDEX idx_eventos_sessao ON eventos(id_sessao);

-- Filtros de erro nos eventos (índice parcial)
CREATE INDEX idx_eventos_erro ON eventos (funcionalidade, tempo_segundos)
    WHERE teve_erro = TRUE;

-- Buscas por evento e sessão nos erros
CREATE INDEX idx_erros_evento ON erros(id_evento);
CREATE INDEX idx_erros_sessao ON erros(id_sessao);

-- NPS apenas sobre pesquisas aceitas (índice parcial)
CREATE INDEX idx_avaliacoes_aceitas ON avaliacoes (nps, csat)
    WHERE aceitou_pesquisa = TRUE;

-- Sazonalidade em eventos
CREATE INDEX idx_eventos_hora ON eventos(hora_dia, dia_semana);

-- Sazonalidade em sessoes
CREATE INDEX idx_sessoes_hora ON sessoes(hora_inicio, dia_inicio);