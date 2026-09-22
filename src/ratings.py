# =============================================================================
# ratings.py
# Customer Journey Intelligence — Gerador da Tabela Avaliações
#
# Responsabilidade única: para cada sessão elegível, decidir:
#   1. Se o cliente foi CONVIDADO a responder a pesquisa (probabilístico)
#   2. Se ele ACEITOU (probabilístico por persona)
#   3. Qual NPS e CSAT correspondem ao score_experiencia da sessão
#   4. Se um COMENTÁRIO é gerado (sessões com experiência ruim têm mais chance)
#   5. Qual o TEXTO do comentário (template + variações de tom e sufixo)
#
# Entradas necessárias:
#   - df_sessoes  : com coluna score_experiencia (calculada por events.py)
#   - df_clientes : com coluna persona
#   - df_eventos  : para identificar a funcionalidade problemática da sessão
#
# Saída: data/raw/avaliacoes.csv
# =============================================================================

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import config as cfg

# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------
random.seed(cfg.RANDOM_SEED)
np.random.seed(cfg.RANDOM_SEED)


# =============================================================================
# 1. TEMPLATES DE COMENTÁRIO EXPANDIDOS
# =============================================================================

# Prefixos de abertura por tom emocional
_PREFIXOS: dict[str, list[str]] = {
    "irritado": [
        "Muito insatisfeito. ",
        "Péssima experiência. ",
        "Decepcionante. ",
        "Horrível. ",
        "Que decepção. ",
    ],
    "decepcionado": [
        "Esperava mais. ",
        "Poderia ser melhor. ",
        "Não fui bem atendido. ",
        "Estou desapontado. ",
        "",
    ],
    "neutro": [
        "Precisa melhorar. ",
        "Tive dificuldades. ",
        "Não foi uma boa experiência. ",
        "",
        "",
    ],
}

# Sufixos de fechamento (vazio com maior peso — comentários curtos são mais realistas)
_SUFIXOS: list[str] = [
    " Por favor, resolvam isso.",
    " Espero melhorias em breve.",
    " Já usei outros aplicativos que funcionam melhor.",
    " Isso é inaceitável.",
    " Vou considerar usar outro banco.",
    "",
    "",
    "",
]

# Comentários específicos para sessões que terminaram em abandono
_COMENTARIOS_ABANDONO: list[str] = [
    "O aplicativo travou e precisei fechar.",
    "Não consegui completar o que precisava.",
    "O app parou de funcionar no meio da operação.",
    "Tive que fechar o aplicativo antes de terminar.",
    "O sistema ficou lento e desisti.",
    "Não consegui nem acessar o que queria.",
]

# Comentários para sessões muito longas sem erro específico identificado
_COMENTARIOS_LENTIDAO: list[str] = [
    "O aplicativo estava muito lento hoje.",
    "Tudo demorou mais do que o normal.",
    "As telas demoraram muito para carregar.",
    "A lentidão do app me frustrou bastante.",
    "O desempenho está muito abaixo do esperado.",
]


# =============================================================================
# 2. DERIVAÇÃO DA FUNCIONALIDADE PROBLEMÁTICA
# =============================================================================

def _mapear_funcionalidade_erro(df_eventos: pd.DataFrame) -> pd.Series:
    """
    Para cada sessão com ao menos um erro, identifica a funcionalidade
    mais problemática (maior contagem de erros; empate desfeito pela última).

    Retorna pd.Series {id_sessao: funcionalidade}.
    Sessões sem erro não aparecem na série (get retorna "").
    """
    ev_erro = df_eventos[df_eventos["teve_erro"] == True].copy()

    if ev_erro.empty:
        return pd.Series(dtype=str)

    contagem = (
        ev_erro.groupby(["id_sessao", "funcionalidade"])
               .size()
               .reset_index(name="n_erros")
    )
    idx_max  = contagem.groupby("id_sessao")["n_erros"].idxmax()
    func_err = contagem.loc[idx_max].set_index("id_sessao")["funcionalidade"]
    return func_err


# =============================================================================
# 3. GERAÇÃO DO COMENTÁRIO
# =============================================================================

def _tom_por_nps(nps: int) -> str:
    if nps <= 3:
        return "irritado"
    elif nps <= 5:
        return "decepcionado"
    return "neutro"


def _gerar_comentario(
    nps:              int,
    csat:             int,
    funcionalidade:   str,
    abandonada:       bool,
    duracao_segundos: int,
    score:            int,
) -> str | None:
    """
    Decide se há comentário e gera o texto quando aplicável.

    Probabilidades de comentário:
      NPS <= 6 ou CSAT <= 3  →  ~78%
      NPS 7–8                →  ~8%
      NPS 9–10               →  ~2%

    Replica o comportamento real: clientes insatisfeitos comentam mais.
    """
    ruim = (nps <= cfg.NPS_LIMIAR_COMENTARIO) or (csat <= cfg.CSAT_LIMIAR_COMENTARIO)

    if ruim:
        if random.random() > 0.78:
            return None
    elif nps <= 8:
        if random.random() > 0.08:
            return None
    else:
        if random.random() > 0.02:
            return None

    # Monta o texto
    tom     = _tom_por_nps(nps)
    prefixo = random.choice(_PREFIXOS[tom])
    sufixo  = random.choice(_SUFIXOS)

    # Escolhe o corpo baseado no contexto mais relevante da sessão
    if abandonada and not funcionalidade:
        corpo = random.choice(_COMENTARIOS_ABANDONO)
    elif duracao_segundos > cfg.SESSAO_LONGA_THRESHOLD * 1.5 and not funcionalidade:
        corpo = random.choice(_COMENTARIOS_LENTIDAO)
    elif funcionalidade and funcionalidade in cfg.COMENTARIOS_TEMPLATES:
        corpo = random.choice(cfg.COMENTARIOS_TEMPLATES[funcionalidade])
    else:
        corpo = random.choice(cfg.COMENTARIOS_TEMPLATES["GERAL"])

    return (prefixo + corpo + sufixo).strip()


# =============================================================================
# 4. TIMESTAMP DA AVALIAÇÃO
# =============================================================================

def _gerar_timestamp_avaliacao(data_hora_fim: str) -> str:
    """
    A avaliação ocorre entre 10 e 90 segundos após o encerramento da sessão
    (cliente ainda está no app ou acabou de fechá-lo).
    """
    fim   = datetime.strptime(data_hora_fim, "%Y-%m-%d %H:%M:%S")
    delay = timedelta(seconds=random.randint(10, 90))
    return (fim + delay).strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# 5. FUNÇÃO PÚBLICA
# =============================================================================

def gerar_avaliacoes(
    df_sessoes:  pd.DataFrame,
    df_clientes: pd.DataFrame,
    df_eventos:  pd.DataFrame,
) -> pd.DataFrame:
    """
    Gera a tabela completa de avaliações.

    Parâmetros
    ----------
    df_sessoes  : DataFrame com score_experiencia (gerado por events.py)
    df_clientes : DataFrame com persona por cliente
    df_eventos  : DataFrame de eventos (para derivar funcionalidade problemática)

    Retorna
    -------
    pd.DataFrame com colunas:
        id_avaliacao, id_sessao, nps, csat, comentario,
        aceitou_pesquisa, score_experiencia, data_avaliacao
    """
    print(f"[ratings] Gerando avaliações para {len(df_sessoes):,} sessões...")

    # Pré-processamento
    persona_map: dict[int, str] = (
        df_clientes.set_index("id_cliente")["persona"].to_dict()
    )

    print("[ratings] Mapeando funcionalidades com erro por sessão...")
    func_erro_map: pd.Series = _mapear_funcionalidade_erro(df_eventos)

    # Loop principal
    registros:   list[dict] = []
    id_avaliacao = 1

    total      = len(df_sessoes)
    checkpoint = max(1, total // 5)

    for i, row in enumerate(df_sessoes.itertuples(index=False), start=1):
        if i % checkpoint == 0:
            pct = i / total * 100
            print(f"  [{pct:5.1f}%]  {i:,}/{total:,} sessões  "
                  f"| avaliações geradas: {len(registros):,}")

        persona = persona_map.get(row.id_cliente, "Cliente Tradicional")
        score   = int(row.score_experiencia) if not pd.isna(row.score_experiencia) \
                  else cfg.SCORE_INICIAL

        # ETAPA 1 — Convite (25% das sessões)
        if random.random() > cfg.PROB_CONVIDADO_PESQUISA:
            continue

        # ETAPA 2 — Aceite (por persona, com boost para sessões ruins)
        prob_aceite = cfg.PROB_ACEITAR_PESQUISA[persona]
        if score < 45:
            prob_aceite = min(0.95, prob_aceite * 1.40)

        aceitou = random.random() < prob_aceite

        # ETAPA 3 — NPS e CSAT (do score + ruído humano de ±1)
        nps  = cfg.score_para_nps(score)
        csat = cfg.score_para_csat(score)

        nps  = max(0, min(10, nps  + random.choices([-1, 0, 0, 1], weights=[1, 5, 5, 1])[0]))
        csat = max(1, min(5,  csat + random.choices([-1, 0, 0, 1], weights=[1, 5, 5, 1])[0]))

        # ETAPA 4 — Comentário (apenas para aceites ou sessões ruins convictas)
        funcionalidade = func_erro_map.get(row.id_sessao, "")
        comentario     = _gerar_comentario(
            nps              = nps,
            csat             = csat,
            funcionalidade   = funcionalidade,
            abandonada       = bool(row.abandonada),
            duracao_segundos = int(row.duracao_segundos),
            score            = score,
        )

        # ETAPA 5 — Timestamp
        data_avaliacao = _gerar_timestamp_avaliacao(row.data_hora_fim)

        registros.append({
            "id_avaliacao":     id_avaliacao,
            "id_sessao":        row.id_sessao,
            "nps":              nps,
            "csat":             csat,
            "comentario":       comentario,
            "aceitou_pesquisa": aceitou,
            "score_experiencia":score,
            "data_avaliacao":   data_avaliacao,
        })
        id_avaliacao += 1

    df = pd.DataFrame(registros)

    if df.empty:
        print("[ratings] Nenhuma avaliação gerada.")
        return _df_avaliacoes_vazio()

    _validar(df, df_sessoes)
    _exibir_resumo(df, df_clientes, persona_map)

    return df


def _df_avaliacoes_vazio() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id_avaliacao", "id_sessao", "nps", "csat",
        "comentario", "aceitou_pesquisa", "score_experiencia", "data_avaliacao",
    ])


# =============================================================================
# 6. VALIDAÇÕES
# =============================================================================

def _validar(df: pd.DataFrame, df_sessoes: pd.DataFrame) -> None:

    assert df["id_avaliacao"].is_unique, \
        "IDs de avaliação duplicados."

    sessoes_validas = set(df_sessoes["id_sessao"])
    assert df["id_sessao"].isin(sessoes_validas).all(), \
        "Avaliações com id_sessao inválido."

    assert df["id_sessao"].is_unique, \
        "Mais de uma avaliação por sessão."

    assert df["nps"].between(0, 10).all(), \
        f"NPS fora do intervalo [0,10]."

    assert df["csat"].between(1, 5).all(), \
        f"CSAT fora do intervalo [1,5]."

    comentarios_nao_nulos = df["comentario"].dropna()
    assert (comentarios_nao_nulos.str.strip().str.len() > 0).all(), \
        "Comentários com string vazia encontrados."

    print("[ratings] ✓ Validações concluídas sem erros.")


# =============================================================================
# 7. RESUMO ESTATÍSTICO
# =============================================================================

def _exibir_resumo(
    df:          pd.DataFrame,
    df_clientes: pd.DataFrame,
    persona_map: dict[int, str],
) -> None:
    total         = len(df)
    n_aceitas     = df["aceitou_pesquisa"].sum()
    n_recusadas   = total - n_aceitas
    n_comentarios = df["comentario"].notna().sum()
    aceitas       = df[df["aceitou_pesquisa"] == True]

    print(f"\n{'─'*58}")
    print(f"  RESUMO DA TABELA AVALIAÇÕES  ({total:,} registros)")
    print(f"{'─'*58}")

    print(f"\n  Volume:")
    print(f"    Convites enviados:        {total:,}")
    print(f"    Pesquisas aceitas:        {n_aceitas:,}  ({n_aceitas/total*100:.1f}%)")
    print(f"    Pesquisas recusadas:      {n_recusadas:,}  ({n_recusadas/total*100:.1f}%)")
    print(f"    Com comentário:           {n_comentarios:,}  "
          f"({n_comentarios/n_aceitas*100:.1f}% das aceitas)")

    # NPS oficial (calculado apenas sobre aceitas)
    n_ac          = max(1, len(aceitas))
    promotores    = (aceitas["nps"] >= 9).sum()
    neutros_nps   = aceitas["nps"].between(7, 8).sum()
    detratores    = (aceitas["nps"] <= 6).sum()
    nps_score     = (promotores - detratores) / n_ac * 100

    print(f"\n  NPS (pesquisas aceitas — {n_ac:,}):")
    print(f"    Promotores  (9–10): {promotores:>6,}  ({promotores/n_ac*100:.1f}%)")
    print(f"    Neutros     (7–8):  {neutros_nps:>6,}  ({neutros_nps/n_ac*100:.1f}%)")
    print(f"    Detratores  (0–6):  {detratores:>6,}  ({detratores/n_ac*100:.1f}%)")
    print(f"    NPS Score:          {nps_score:+.1f}")
    print(f"    NPS médio:          {aceitas['nps'].mean():.2f}")

    print(f"\n  Distribuição NPS (0–10):")
    for v in range(11):
        qtd  = (aceitas["nps"] == v).sum()
        pct  = qtd / n_ac * 100
        barr = "█" * max(0, qtd // max(1, n_ac // 80))
        print(f"    {v:>2}  {qtd:>5,}  ({pct:4.1f}%)  {barr}")

    print(f"\n  Distribuição CSAT (1–5):")
    for v in range(1, 6):
        qtd = (aceitas["csat"] == v).sum()
        pct = qtd / n_ac * 100
        print(f"    {v}  {qtd:>5,}  ({pct:.1f}%)")
    print(f"    CSAT médio: {aceitas['csat'].mean():.2f}")

    # Por persona
    sess_cli = df.copy()
    # Mapeamos id_sessao → id_cliente usando persona_map ao contrário não é trivial;
    # omitimos a análise por persona no resumo standalone para não depender de joins
    # extras — isso é feito no generator.py com o dataset completo.

    # NPS por faixa de score
    print(f"\n  NPS médio por faixa de score_experiencia:")
    bins   = [0, 20, 40, 60, 80, 101]
    labels = ["0–19", "20–39", "40–59", "60–79", "80–100"]
    df_tmp = aceitas.copy()
    df_tmp["faixa"] = pd.cut(
        df_tmp["score_experiencia"], bins=bins, labels=labels, right=False
    )
    por_faixa = df_tmp.groupby("faixa", observed=True)["nps"].agg(["mean", "count"])
    for faixa, row in por_faixa.iterrows():
        if row["count"] > 0:
            print(f"    Score {str(faixa):<8}  NPS médio: {row['mean']:.2f}  "
                  f"(n={int(row['count']):,})")

    # Comentários por funcionalidade (frequência de menção)
    com_df = df[df["comentario"].notna()]["comentario"]
    print(f"\n  Amostra de {min(10, n_comentarios)} comentários gerados:")
    for c in com_df.sample(min(10, n_comentarios), random_state=cfg.RANDOM_SEED).values:
        print(f"    › {c}")

    print(f"{'─'*58}\n")


# =============================================================================
# 8. EXECUÇÃO DIRETA (modo standalone)
# =============================================================================

if __name__ == "__main__":
    import os
    from customers import gerar_clientes
    from sessions  import gerar_sessoes
    from events    import gerar_eventos

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    df_clientes                      = gerar_clientes()
    df_sessoes                       = gerar_sessoes(df_clientes)
    df_eventos, df_erros, df_sessoes = gerar_eventos(df_sessoes, df_clientes)
    df_avaliacoes                    = gerar_avaliacoes(df_sessoes, df_clientes, df_eventos)

    df_avaliacoes.to_csv(cfg.OUTPUT_AVALIACOES, index=False, encoding="utf-8")

    print(f"[ratings] Arquivo salvo em: {cfg.OUTPUT_AVALIACOES}")
    print(f"[ratings] Shape: {df_avaliacoes.shape}")
    print(f"\n  Primeiros registros:\n")
    print(df_avaliacoes.head(10).to_string(index=False))
