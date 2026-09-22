# =============================================================================
# events.py
# Customer Journey Intelligence — Motor de Simulação de Eventos
#
# Responsabilidade: para cada sessão, simular a jornada completa do cliente
# dentro do aplicativo, evento a evento, respeitando:
#   - Fluxo obrigatório: LOGIN → HOME → [func] → HOME → LOGOUT
#   - Probabilidades de uso por persona e hora do dia (sazonalidade)
#   - Probabilidade de erro composta: base × versão × conexão × persona
#   - Lógica de tentativa / abandono pós-erro
#   - Acumulação do score de experiência ao longo da sessão
#
# Saída principal : df_eventos  (tabela eventos)
# Saída secundária: df_erros    (tabela erros, derivada dos eventos com erro)
# Atualiza        : df_sessoes  (duracao_segundos, abandonada, motivo_encerramento)
#
# =============================================================================

import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config as cfg

# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------
random.seed(cfg.RANDOM_SEED)
np.random.seed(cfg.RANDOM_SEED)


# =============================================================================
# 1. ESTRUTURAS DE DADOS INTERNAS
# =============================================================================

@dataclass
class ContextoSessao:
    """
    Carrega todos os parâmetros fixos de uma sessão.
    Evita lookups repetidos nos DataFrames durante a iteração.
    """
    id_sessao:         int
    id_cliente:        int
    persona:           str
    dispositivo:       str
    versao_app:        str
    qualidade_conexao: str
    timestamp_inicio:  datetime
    abandonada_orig:   bool   # valor original de sessions.py (pode ser sobrescrito)


@dataclass
class EstadoSessao:
    """
    Acumula o estado mutável conforme os eventos são gerados.
    """
    score:              int   = cfg.SCORE_INICIAL
    duracao_total_s:    int   = 0
    n_funcionalidades:  int   = 0
    n_erros:            int   = 0
    funcionalidade_erro: str  = ""   # última funcionalidade com erro (para comentário)
    teve_chat:          bool  = False
    logout_realizado:   bool  = False
    abandonada:         bool  = False
    motivo_encerramento: str  = "Logout"


# =============================================================================
# 2. CÁLCULO DA PROBABILIDADE DE ERRO
# =============================================================================

def _prob_erro(
    funcionalidade: str,
    persona:        str,
    versao_app:     str,
    qualidade:      str,
) -> float:
    """
    Probabilidade final de erro para um evento, combinando quatro fatores
    multiplicativos independentes:

        P = base × mult_persona × mult_versao × mult_conexao

    Clampado em [0, 0.95] para evitar erros determinísticos.
    """
    base = cfg.PROB_ERRO_BASE.get(funcionalidade, 0.01)

    mult_persona = cfg.PERSONA_ERRO_MULTIPLICADOR.get(
        funcionalidade,
        cfg.PERSONA_ERRO_MULTIPLICADOR["DEFAULT"]
    )[persona]

    mult_versao   = cfg.VERSAO_ERRO_MULTIPLICADOR[versao_app]
    mult_conexao  = cfg.QUALIDADE_ERRO_MULTIPLICADOR[qualidade]

    return min(0.95, base * mult_persona * mult_versao * mult_conexao)


# =============================================================================
# 3. SELEÇÃO DE FUNCIONALIDADE COM BOOST SAZONAL
# =============================================================================

def _pesos_funcionais_com_boost(persona: str, hora: int) -> list[float]:
    """
    Retorna os pesos de seleção de funcionalidade para a persona,
    ajustados pelos boosts de sazonalidade intra-dia:
        - Manhã   (7–9h)  : BOOST_MANHA
        - Almoço  (12–14h): BOOST_ALMOCO
        - Noite   (18–22h): BOOST_NOITE
    """
    pesos = list(cfg.PROB_FUNCIONALIDADE[persona])   # cópia

    boost_map: dict[str, float] = {}
    if 7 <= hora <= 9:
        boost_map = cfg.BOOST_MANHA
    elif 12 <= hora <= 14:
        boost_map = cfg.BOOST_ALMOCO
    elif 18 <= hora <= 22:
        boost_map = cfg.BOOST_NOITE

    for i, func in enumerate(cfg.FUNCIONALIDADES_NAVEGAVEIS_ORDER):
        if func in boost_map:
            pesos[i] *= boost_map[func]

    # Renormaliza para distribuição de probabilidade válida
    soma = sum(pesos)
    return [p / soma for p in pesos]


def _escolher_funcionalidade(persona: str, hora: int, ja_usadas: set[str]) -> str | None:
    """
    Sorteia a próxima funcionalidade navegável.
    Exclui funcionalidades já usadas na mesma sessão com probabilidade
    crescente (cliente tende a não repetir a mesma tela na mesma sessão,
    mas pode fazê-lo ocasionalmente).
    """
    funcs  = cfg.FUNCIONALIDADES_NAVEGAVEIS_ORDER
    pesos  = _pesos_funcionais_com_boost(persona, hora)

    # Penaliza funcionalidades já visitadas (reduz peso em 70%)
    pesos_ajustados = [
        p * 0.30 if funcs[i] in ja_usadas else p
        for i, p in enumerate(pesos)
    ]
    soma = sum(pesos_ajustados)
    if soma == 0:
        return None
    pesos_ajustados = [p / soma for p in pesos_ajustados]

    return random.choices(funcs, weights=pesos_ajustados, k=1)[0]


# =============================================================================
# 4. GERAÇÃO DE TEMPO POR EVENTO
# =============================================================================

def _gerar_tempo(
    funcionalidade: str,
    persona:        str,
    qualidade:      str,
    situacao:       str = "normal",   # normal | com_erro | pos_repeticao
) -> int:
    """
    Gera o tempo gasto (segundos) em um evento com variação log-normal.

    Fatores:
        tempo_base × mult_situacao × mult_conexao × mult_persona × ruído
    """
    base      = cfg.TEMPO_MEDIO_FUNCIONALIDADE.get(funcionalidade, 10)
    m_sit     = cfg.TEMPO_MULTIPLICADOR[situacao]
    m_persona = cfg.TEMPO_MULTIPLICADOR_PERSONA[persona]

    m_conexao = 1.0
    if qualidade == "Ruim":
        m_conexao = cfg.TEMPO_MULTIPLICADOR["conexao_ruim"]
    elif qualidade == "Regular":
        m_conexao = cfg.TEMPO_MULTIPLICADOR["conexao_regular"]

    media  = base * m_sit * m_conexao * m_persona
    cv     = cfg.TEMPO_STD_PROPORCAO
    sigma  = np.sqrt(np.log(1 + cv**2))
    mu     = np.log(max(1.0, media)) - sigma**2 / 2

    tempo = int(np.random.lognormal(mean=mu, sigma=sigma))
    return max(1, tempo)


# =============================================================================
# 5. TIPO E CÓDIGO DE ERRO
# =============================================================================

def _sortear_tipo_erro(funcionalidade: str) -> str:
    """Sorteia o tipo de erro compatível com a funcionalidade."""
    tipos_possiveis = cfg.ERROS_POR_FUNCIONALIDADE.get(funcionalidade, ["ERRO_INTERNO"])
    pesos = [cfg.ERRO_TIPO_PESOS.get(t, 0.1) for t in tipos_possiveis]
    soma  = sum(pesos)
    pesos = [p / soma for p in pesos]
    return random.choices(tipos_possiveis, weights=pesos, k=1)[0]


def _sortear_codigo_erro(tipo_erro: str) -> str:
    """Sorteia o código HTTP/sistema do erro."""
    codigos = cfg.ERRO_CODIGOS.get(tipo_erro, ["ERR_UNKNOWN"])
    return random.choice(codigos)


# =============================================================================
# 6. ATUALIZAÇÃO DO SCORE DE EXPERIÊNCIA
# =============================================================================

def _penalizar_erro(estado: EstadoSessao, tipo_erro: str) -> None:
    """Aplica a penalização correta ao score conforme o tipo de erro."""
    if tipo_erro == "TIMEOUT":
        estado.score += cfg.PENALIZACOES["erro_timeout"]
    elif tipo_erro == "FALHA_AUTENTICACAO":
        estado.score += cfg.PENALIZACOES["erro_falha_autenticacao"]
    elif tipo_erro == "SERVICO_INDISPONIVEL":
        estado.score += cfg.PENALIZACOES["erro_servico_indisponivel"]
    else:
        estado.score += cfg.PENALIZACOES["erro_generico"]

    estado.score = max(0, estado.score)
    estado.n_erros += 1


def _registrar_bonus_sucesso(estado: EstadoSessao, funcionalidade: str) -> None:
    """Aplica bônus por funcionalidade concluída sem erro."""
    if funcionalidade not in ("HOME", "LOGIN", "LOGOUT"):
        estado.score = min(100, estado.score + cfg.BONUS["sucesso_sem_erro"])


# =============================================================================
# 7. SIMULAÇÃO DE UMA FUNCIONALIDADE (com loop de erro/retentativa)
# =============================================================================

def _simular_funcionalidade(
    ctx:             ContextoSessao,
    estado:          EstadoSessao,
    funcionalidade:  str,
    id_evento_base:  int,
    ordem_base:      int,
    timestamp_atual: datetime,
    eventos:         list[dict],
    erros:           list[dict],
    id_erro_counter: list[int],   # lista de 1 elemento — mutável por referência
) -> tuple[int, int, datetime, bool]:
    """
    Simula a interação do cliente com uma funcionalidade, incluindo
    possíveis erros e retentativas.

    Retorna (próximo_id_evento, próxima_ordem, próximo_timestamp, abandonou).
    """
    id_evento = id_evento_base
    ordem     = ordem_base
    ts        = timestamp_atual
    tentativa = 0
    abandonou = False

    while True:
        tentativa += 1
        situacao   = "normal" if tentativa == 1 else "pos_repeticao"
        tempo_gasto = _gerar_tempo(funcionalidade, ctx.persona, ctx.qualidade_conexao, situacao)

        # Determina se houve erro nesta tentativa
        p_erro   = _prob_erro(funcionalidade, ctx.persona, ctx.versao_app, ctx.qualidade_conexao)
        teve_erro = random.random() < p_erro

        if teve_erro:
            tipo_erro   = _sortear_tipo_erro(funcionalidade)
            codigo_erro = _sortear_codigo_erro(tipo_erro)

            # Tempo com erro é maior
            tempo_gasto = _gerar_tempo(funcionalidade, ctx.persona,
                                       ctx.qualidade_conexao, "com_erro")

            # Registra evento com erro
            eventos.append({
                "id_evento":       id_evento,
                "id_sessao":       ctx.id_sessao,
                "ordem":           ordem,
                "timestamp":       ts.strftime("%Y-%m-%d %H:%M:%S"),
                "funcionalidade":  funcionalidade,
                "acao":            "ERRO",
                "tempo_segundos":  tempo_gasto,
                "status":          "ERRO",
                "teve_erro":       True,
            })

            # Registra na tabela de erros
            resolvido = False   # ainda não resolvido; decide abaixo
            erros.append({
                "id_erro":         id_erro_counter[0],
                "id_evento":       id_evento,
                "id_sessao":       ctx.id_sessao,
                "tipo_erro":       tipo_erro,
                "codigo_erro":     codigo_erro,
                "tempo_resolucao": None,    # preenchido abaixo se resolvido
                "resolvido":       False,
                "tentativas":      tentativa,
            })
            idx_erro = len(erros) - 1
            id_erro_counter[0] += 1
            id_evento += 1
            ordem     += 1
            ts         = ts + timedelta(seconds=tempo_gasto)

            estado.duracao_total_s += tempo_gasto
            _penalizar_erro(estado, tipo_erro)
            if tentativa > 1:
                estado.score = max(0, estado.score + cfg.PENALIZACOES["repeticao_acao"])
            estado.funcionalidade_erro = funcionalidade

            # Decide: tentar de novo ou abandonar?
            p_abandono = cfg.PERSONA_PROB_ABANDONO_POS_ERRO[ctx.persona]
            desistiu   = (
                random.random() < p_abandono
                or tentativa >= cfg.MAX_TENTATIVAS
            )

            if desistiu:
                # Abandono da funcionalidade (não necessariamente da sessão)
                estado.score = max(0, estado.score + cfg.PENALIZACOES["abandono_funcionalidade"])
                # Marca o erro como não resolvido
                erros[idx_erro]["resolvido"] = False
                abandonou = True
                break
            else:
                # Nova tentativa: o erro foi resolvido (parcialmente)
                p_resolve = cfg.PROB_ERRO_RESOLVIDO[tipo_erro]
                if random.random() < p_resolve:
                    erros[idx_erro]["resolvido"]       = True
                    erros[idx_erro]["tempo_resolucao"] = tempo_gasto
                # Continua o loop para tentar de novo

        else:
            # Sucesso nesta tentativa
            # Verifica tempo excessivo
            tempo_medio = cfg.TEMPO_MEDIO_FUNCIONALIDADE.get(funcionalidade, 10)
            if tempo_gasto > tempo_medio * cfg.TEMPO_EXCESSIVO_FATOR:
                estado.score = max(0, estado.score + cfg.PENALIZACOES["tempo_excessivo"])

            eventos.append({
                "id_evento":       id_evento,
                "id_sessao":       ctx.id_sessao,
                "ordem":           ordem,
                "timestamp":       ts.strftime("%Y-%m-%d %H:%M:%S"),
                "funcionalidade":  funcionalidade,
                "acao":            _acao_sucesso(funcionalidade, tentativa),
                "tempo_segundos":  tempo_gasto,
                "status":          "SUCESSO",
                "teve_erro":       False,
            })

            id_evento += 1
            ordem     += 1
            ts         = ts + timedelta(seconds=tempo_gasto)
            estado.duracao_total_s += tempo_gasto

            _registrar_bonus_sucesso(estado, funcionalidade)
            break

    return id_evento, ordem, ts, abandonou


def _acao_sucesso(funcionalidade: str, tentativa: int) -> str:
    """Retorna a ação registrada em um evento bem-sucedido."""
    mapa = {
        "LOGIN":         "CONFIRMAR",
        "HOME":          "NAVEGAR",
        "SALDO":         "VISUALIZAR",
        "PIX":           "CONFIRMAR",
        "PAGAMENTO":     "CONFIRMAR",
        "CARTAO":        "VISUALIZAR_FATURA",
        "INVESTIMENTOS": "VISUALIZAR_CARTEIRA",
        "CHAT":          "ENCERRAR",
        "LOGOUT":        "CONFIRMAR",
    }
    acao = mapa.get(funcionalidade, "CONFIRMAR")
    return f"REPETIR_{acao}" if tentativa > 1 else acao


# =============================================================================
# 8. SIMULAÇÃO COMPLETA DE UMA SESSÃO
# =============================================================================

def _simular_sessao(
    ctx:             ContextoSessao,
    id_evento_base:  int,
    id_erro_base:    int,
) -> tuple[list[dict], list[dict], EstadoSessao]:
    """
    Simula a jornada completa de uma sessão, gerando todos os eventos
    e erros associados.

    Fluxo garantido:
        LOGIN → HOME → [func1] → HOME → [func2] → HOME → ... → HOME → LOGOUT

    Retorna (eventos, erros, estado_final).
    """
    eventos:  list[dict] = []
    erros:    list[dict] = []
    estado    = EstadoSessao()

    id_evento   = id_evento_base
    ordem       = 1
    ts          = ctx.timestamp_inicio
    id_erro_ctr = [id_erro_base]   # lista mutável para passar por referência

    hora = ctx.timestamp_inicio.hour

    # ------------------------------------------------------------------
    # ETAPA 1 — LOGIN (obrigatório)
    # ------------------------------------------------------------------
    id_evento, ordem, ts, abandonou_login = _simular_funcionalidade(
        ctx, estado, "LOGIN",
        id_evento, ordem, ts, eventos, erros, id_erro_ctr,
    )

    if abandonou_login:
        # Falhou no login e desistiu: sessão encerrada aqui
        estado.abandonada         = True
        estado.motivo_encerramento = "Abandono"
        estado.score = max(0, estado.score + cfg.PENALIZACOES["abandono_sessao"])
        return eventos, erros, estado

    # ------------------------------------------------------------------
    # ETAPA 2 — HOME inicial
    # ------------------------------------------------------------------
    id_evento, ordem, ts, _ = _simular_funcionalidade(
        ctx, estado, "HOME",
        id_evento, ordem, ts, eventos, erros, id_erro_ctr,
    )

    # ------------------------------------------------------------------
    # ETAPA 3 — Navegação pelas funcionalidades
    # ------------------------------------------------------------------
    n_funcs_alvo = max(1, int(np.random.poisson(
        lam=cfg.PERSONA_FUNCS_POR_SESSAO[ctx.persona]
    )))

    ja_usadas:   set[str] = set()
    abandonou_sessao = False

    for _ in range(n_funcs_alvo):
        funcionalidade = _escolher_funcionalidade(ctx.persona, hora, ja_usadas)
        if funcionalidade is None:
            break

        ja_usadas.add(funcionalidade)
        estado.n_funcionalidades += 1

        if funcionalidade == "CHAT":
            estado.teve_chat = True
            estado.score = max(0, estado.score + cfg.PENALIZACOES["uso_chat"])

        id_evento, ordem, ts, abandonou_func = _simular_funcionalidade(
            ctx, estado, funcionalidade,
            id_evento, ordem, ts, eventos, erros, id_erro_ctr,
        )

        if abandonou_func:
            # Verifica se abandona só a funcionalidade ou a sessão inteira
            p_abandona_sessao = cfg.PERSONA_PROB_ABANDONO_POS_ERRO[ctx.persona] * 0.6
            if random.random() < p_abandona_sessao:
                abandonou_sessao = True
                estado.abandonada          = True
                estado.motivo_encerramento = "Abandono"
                estado.score = max(0, estado.score + cfg.PENALIZACOES["abandono_sessao"])
                break
            # Senão, volta ao HOME e tenta outra funcionalidade
            id_evento, ordem, ts, _ = _simular_funcionalidade(
                ctx, estado, "HOME",
                id_evento, ordem, ts, eventos, erros, id_erro_ctr,
            )
            continue

        # HOME de retorno entre funcionalidades
        id_evento, ordem, ts, _ = _simular_funcionalidade(
            ctx, estado, "HOME",
            id_evento, ordem, ts, eventos, erros, id_erro_ctr,
        )

    # ------------------------------------------------------------------
    # ETAPA 4 — LOGOUT (se não abandonou)
    # ------------------------------------------------------------------
    if not abandonou_sessao:
        id_evento, ordem, ts, _ = _simular_funcionalidade(
            ctx, estado, "LOGOUT",
            id_evento, ordem, ts, eventos, erros, id_erro_ctr,
        )
        estado.logout_realizado    = True
        estado.motivo_encerramento = "Logout"
        estado.score = min(100, estado.score + cfg.BONUS["logout_realizado"])

    # ------------------------------------------------------------------
    # ETAPA 5 — Bônus / penalizações finais de sessão
    # ------------------------------------------------------------------
    if estado.n_funcionalidades <= 2:
        estado.score = min(100, estado.score + cfg.BONUS["poucas_funcionalidades"])

    if estado.duracao_total_s > cfg.SESSAO_LONGA_THRESHOLD:
        estado.score = max(0, estado.score + cfg.PENALIZACOES["sessao_muito_longa"])

    estado.score = max(0, min(100, estado.score))

    return eventos, erros, estado


# =============================================================================
# 9. FUNÇÃO PÚBLICA
# =============================================================================

def gerar_eventos(
    df_sessoes:  pd.DataFrame,
    df_clientes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Gera os eventos e erros para todas as sessões e atualiza a tabela de sessões.

    Parâmetros
    ----------
    df_sessoes  : pd.DataFrame — saída de sessions.gerar_sessoes()
    df_clientes : pd.DataFrame — saída de customers.gerar_clientes()

    Retorna
    -------
    df_eventos  : pd.DataFrame — tabela eventos
    df_erros    : pd.DataFrame — tabela erros (derivada dos eventos)
    df_sessoes  : pd.DataFrame — tabela sessoes com duracao, score e motivo atualizados
    """
    print(f"[events] Simulando eventos para {len(df_sessoes):,} sessões...")

    # Lookup rápido: id_cliente → persona
    persona_map: dict[int, str] = (
        df_clientes.set_index("id_cliente")["persona"].to_dict()
    )

    todos_eventos: list[dict] = []
    todos_erros:   list[dict] = []

    # Colunas que serão atualizadas nas sessões
    sess_update: dict[int, dict] = {}   # id_sessao → {campo: valor}

    id_evento_counter = 1
    id_erro_counter   = 1

    total      = len(df_sessoes)
    checkpoint = max(1, total // 10)

    for i, row in enumerate(df_sessoes.itertuples(index=False), start=1):
        if i % checkpoint == 0:
            pct = i / total * 100
            print(f"  [{pct:5.1f}%]  {i:,}/{total:,} sessões  "
                  f"| eventos: {len(todos_eventos):,}  "
                  f"| erros: {len(todos_erros):,}")

        persona = persona_map.get(row.id_cliente, "Cliente Tradicional")

        ctx = ContextoSessao(
            id_sessao         = row.id_sessao,
            id_cliente        = row.id_cliente,
            persona           = persona,
            dispositivo       = row.dispositivo,
            versao_app        = row.versao_app,
            qualidade_conexao = row.qualidade_conexao,
            timestamp_inicio  = datetime.strptime(row.data_hora_inicio, "%Y-%m-%d %H:%M:%S"),
            abandonada_orig   = row.abandonada,
        )

        eventos_sess, erros_sess, estado = _simular_sessao(
            ctx,
            id_evento_base = id_evento_counter,
            id_erro_base   = id_erro_counter,
        )

        todos_eventos.extend(eventos_sess)
        todos_erros.extend(erros_sess)

        id_evento_counter += len(eventos_sess)
        id_erro_counter   += len(erros_sess)

        # Prepara atualização da sessão com dados reais pós-simulação
        ts_fim_real = (
            ctx.timestamp_inicio + timedelta(seconds=estado.duracao_total_s)
        ).strftime("%Y-%m-%d %H:%M:%S")

        sess_update[row.id_sessao] = {
            "duracao_segundos":    estado.duracao_total_s,
            "data_hora_fim":       ts_fim_real,
            "abandonada":          estado.abandonada,
            "motivo_encerramento": estado.motivo_encerramento,
            "score_experiencia":   estado.score,
        }

    print(f"\n[events] Construindo DataFrames...")

    df_eventos = pd.DataFrame(todos_eventos)
    df_erros   = pd.DataFrame(todos_erros) if todos_erros else _df_erros_vazio()

    # Aplica atualizações nas sessões
    df_sessoes = df_sessoes.copy()
    upd = pd.DataFrame.from_dict(sess_update, orient="index")
    upd.index.name = "id_sessao"
    upd = upd.reset_index()
    df_sessoes = df_sessoes.merge(
        upd, on="id_sessao", how="left", suffixes=("_old", "")
    )
    # Remove colunas antigas duplicadas após merge
    cols_old = [c for c in df_sessoes.columns if c.endswith("_old")]
    df_sessoes.drop(columns=cols_old, inplace=True)

    # Adiciona score_experiencia à tabela de sessões
    if "score_experiencia" not in df_sessoes.columns:
        df_sessoes["score_experiencia"] = cfg.SCORE_INICIAL

    _validar(df_eventos, df_erros, df_sessoes)
    _exibir_resumo(df_eventos, df_erros, df_sessoes)

    return df_eventos, df_erros, df_sessoes


def _df_erros_vazio() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id_erro", "id_evento", "id_sessao",
        "tipo_erro", "codigo_erro",
        "tempo_resolucao", "resolvido", "tentativas",
    ])


# =============================================================================
# 10. VALIDAÇÕES
# =============================================================================

def _validar(
    df_eventos: pd.DataFrame,
    df_erros:   pd.DataFrame,
    df_sessoes: pd.DataFrame,
) -> None:

    assert df_eventos["id_evento"].is_unique, "IDs de evento duplicados."
    assert df_eventos["id_sessao"].isin(df_sessoes["id_sessao"]).all(), \
        "Eventos com id_sessao inválido."
    assert df_eventos["funcionalidade"].isin(cfg.FUNCIONALIDADES).all(), \
        "Funcionalidade inválida em evento."
    assert df_eventos["status"].isin(cfg.STATUS_EVENTO).all(), \
        "Status de evento inválido."
    assert (df_eventos["tempo_segundos"] >= 1).all(), \
        "Evento com tempo zero ou negativo."

    # Toda sessão deve ter ao menos 1 evento (LOGIN)
    sess_com_evento = set(df_eventos["id_sessao"].unique())
    sess_total      = set(df_sessoes["id_sessao"].unique())
    sem_evento      = sess_total - sess_com_evento
    assert len(sem_evento) == 0, \
        f"{len(sem_evento)} sessões sem nenhum evento."

    # Primeira ação de cada sessão deve ser LOGIN
    primeiro_evento = (
        df_eventos.sort_values(["id_sessao", "ordem"])
                  .groupby("id_sessao")
                  .first()
                  .reset_index()
    )
    assert (primeiro_evento["funcionalidade"] == "LOGIN").all(), \
        "Sessões sem LOGIN como primeiro evento."

    # Erros: id_evento deve existir em eventos
    if len(df_erros) > 0:
        assert df_erros["id_evento"].isin(df_eventos["id_evento"]).all(), \
            "Erros com id_evento inválido."
        assert df_erros["tipo_erro"].isin(cfg.ERRO_TIPO_PESOS.keys()).all(), \
            "Tipo de erro inválido."

    print("[events] ✓ Validações concluídas sem erros.")


# =============================================================================
# 11. RESUMO ESTATÍSTICO
# =============================================================================

def _exibir_resumo(
    df_ev:   pd.DataFrame,
    df_err:  pd.DataFrame,
    df_sess: pd.DataFrame,
) -> None:
    n_ev   = len(df_ev)
    n_err  = len(df_err)
    n_sess = len(df_sess)

    print(f"\n{'─'*60}")
    print(f"  RESUMO DA TABELA EVENTOS  ({n_ev:,} registros)")
    print(f"{'─'*60}")

    print(f"\n  Volume:")
    print(f"    Eventos gerados:         {n_ev:,}")
    print(f"    Erros registrados:       {n_err:,}  ({n_err/n_ev*100:.1f}% dos eventos)")
    print(f"    Média eventos/sessão:    {n_ev/n_sess:.1f}")

    print(f"\n  Eventos por funcionalidade:")
    for func, qtd in df_ev["funcionalidade"].value_counts().items():
        pct = qtd / n_ev * 100
        print(f"    {func:<15}  {qtd:>7,}  ({pct:.1f}%)")

    print(f"\n  Status dos eventos:")
    for status, qtd in df_ev["status"].value_counts().items():
        pct = qtd / n_ev * 100
        print(f"    {status:<12}  {qtd:>7,}  ({pct:.1f}%)")

    print(f"\n  Taxa de erro por funcionalidade:")
    taxa = (
        df_ev.groupby("funcionalidade")["teve_erro"]
             .mean()
             .sort_values(ascending=False)
    )
    for func, t in taxa.items():
        barra = "█" * int(t * 200)
        print(f"    {func:<15}  {t*100:5.2f}%  {barra}")

    if n_err > 0:
        print(f"\n  Erros por tipo:")
        for tipo, qtd in df_err["tipo_erro"].value_counts().items():
            pct = qtd / n_err * 100
            print(f"    {tipo:<25}  {qtd:>6,}  ({pct:.1f}%)")

        tx_resolucao = df_err["resolvido"].mean() * 100
        print(f"\n  Taxa de resolução de erros: {tx_resolucao:.1f}%")

    print(f"\n  Score de experiência (sessões):")
    scores = df_sess["score_experiencia"].dropna()
    print(f"    Média:    {scores.mean():.1f}")
    print(f"    Mediana:  {scores.median():.1f}")
    print(f"    P10:      {scores.quantile(0.10):.1f}")
    print(f"    P90:      {scores.quantile(0.90):.1f}")

    # Distribuição NPS implícito
    nps_vals = scores.apply(cfg.score_para_nps)
    print(f"\n  Distribuição NPS implícita (baseada em score):")
    detratores = (nps_vals <= 6).sum()
    neutros     = ((nps_vals >= 7) & (nps_vals <= 8)).sum()
    promotores  = (nps_vals >= 9).sum()
    n_total     = len(nps_vals)
    nps_score   = (promotores - detratores) / n_total * 100
    print(f"    Promotores  (9–10): {promotores:>6,}  ({promotores/n_total*100:.1f}%)")
    print(f"    Neutros     (7–8):  {neutros:>6,}  ({neutros/n_total*100:.1f}%)")
    print(f"    Detratores  (0–6):  {detratores:>6,}  ({detratores/n_total*100:.1f}%)")
    print(f"    NPS calculado:      {nps_score:+.1f}")

    print(f"\n  Sessões por motivo de encerramento (pós-simulação):")
    for motivo, qtd in df_sess["motivo_encerramento"].value_counts().items():
        pct = qtd / n_sess * 100
        print(f"    {motivo:<12}  {qtd:>7,}  ({pct:.1f}%)")

    print(f"{'─'*60}\n")


# =============================================================================
# 12. EXECUÇÃO DIRETA (modo standalone)
# =============================================================================

if __name__ == "__main__":
    import os
    from customers import gerar_clientes
    from sessions  import gerar_sessoes

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    df_clientes = gerar_clientes()
    df_sessoes  = gerar_sessoes(df_clientes)
    df_eventos, df_erros, df_sessoes = gerar_eventos(df_sessoes, df_clientes)

    df_eventos.to_csv(cfg.OUTPUT_EVENTOS,  index=False, encoding="utf-8")
    df_erros.to_csv(cfg.OUTPUT_ERROS,      index=False, encoding="utf-8")
    df_sessoes.to_csv(cfg.OUTPUT_SESSOES,  index=False, encoding="utf-8")

    print(f"[events] Eventos  → {cfg.OUTPUT_EVENTOS}   shape: {df_eventos.shape}")
    print(f"[events] Erros    → {cfg.OUTPUT_ERROS}     shape: {df_erros.shape}")
    print(f"[events] Sessões  → {cfg.OUTPUT_SESSOES}   shape: {df_sessoes.shape}")

    print(f"\n  Amostra de eventos:\n")
    print(df_eventos.head(12).to_string(index=False))
