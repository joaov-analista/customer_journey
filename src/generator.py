# =============================================================================
# generator.py
# Customer Journey Intelligence — Orquestrador da Simulação
#
# Ponto de entrada único do projeto. Executa o pipeline completo em ordem:
#
#   1. customers.py  → gera clientes
#   2. sessions.py   → gera sessões
#   3. events.py     → gera eventos + erros + atualiza sessões
#   4. ratings.py    → gera avaliações
#   5. Exporta todos os CSVs para data/raw/
#   6. Imprime relatório de síntese com os principais indicadores
#
# Uso:
#   python generator.py                        # geração completa
#   python generator.py --skip-if-exists       # pula se CSVs já existem
#   python generator.py --report-only          # só lê os CSVs e imprime o relatório
#
# =============================================================================

import argparse
import os
import sys
import time
from datetime import datetime

import pandas as pd

import config as cfg
from customers import gerar_clientes
from sessions import gerar_sessoes
from events import gerar_eventos
from ratings import gerar_avaliacoes

# =============================================================================
# 1. UTILITÁRIOS
# =============================================================================

def _ts() -> str:
    """Timestamp formatado para logging."""
    return datetime.now().strftime("%H:%M:%S")


def _hms(segundos: float) -> str:
    """Converte segundos em string legível hh:mm:ss."""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _sep(char: str = "─", n: int = 65) -> str:
    return char * n


def _print_header(titulo: str) -> None:
    print(f"\n{_sep('═')}")
    print(f"  {titulo}")
    print(_sep('═'))


def _tamanho_arquivo(path: str) -> str:
    """Retorna tamanho do arquivo em formato legível."""
    if not os.path.exists(path):
        return "—"
    size = os.path.getsize(path)
    if size >= 1024**2:
        return f"{size / 1024**2:.1f} MB"
    return f"{size / 1024:.0f} KB"


# =============================================================================
# 2. PIPELINE PRINCIPAL
# =============================================================================

def executar_pipeline() -> dict[str, pd.DataFrame]:
    """
    Executa todas as etapas de geração de dados em sequência.

    Retorna
    -------
    dict com todos os DataFrames gerados:
        clientes, sessoes, eventos, erros, avaliacoes
    """
    _print_header("INICIANDO PIPELINE DE SIMULAÇÃO")
    print(f"  Seed:         {cfg.RANDOM_SEED}")
    print(f"  Clientes:     {cfg.N_CLIENTES:,}")
    print(f"  Sessões alvo: {cfg.N_SESSOES:,}")
    print(f"  Período:      {cfg.DATA_INICIO} → {cfg.DATA_FIM}")
    print(f"  Saída:        {cfg.OUTPUT_DIR}")
    print(f"  Início:       {_ts()}")

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    tempos: dict[str, float] = {}
    t_inicio_total = time.time()

    # ------------------------------------------------------------------
    # ETAPA 1 — Clientes
    # ------------------------------------------------------------------
    print(f"\n{_sep()}")
    print(f"  [1/4]  {_ts()}  Gerando clientes...")
    print(_sep())
    t0 = time.time()

    df_clientes = gerar_clientes()
    df_clientes.to_csv(cfg.OUTPUT_CLIENTES, index=False, encoding="utf-8")

    tempos["clientes"] = time.time() - t0
    print(f"\n  ✓ clientes.csv  "
          f"({len(df_clientes):,} linhas | "
          f"{_tamanho_arquivo(cfg.OUTPUT_CLIENTES)} | "
          f"{_hms(tempos['clientes'])})")

    # ------------------------------------------------------------------
    # ETAPA 2 — Sessões
    # ------------------------------------------------------------------
    print(f"\n{_sep()}")
    print(f"  [2/4]  {_ts()}  Gerando sessões...")
    print(_sep())
    t0 = time.time()

    df_sessoes = gerar_sessoes(df_clientes)

    tempos["sessoes"] = time.time() - t0
    print(f"\n  ✓ sessões em memória  "
          f"({len(df_sessoes):,} linhas | {_hms(tempos['sessoes'])})")

    # ------------------------------------------------------------------
    # ETAPA 3 — Eventos + Erros (sessões atualizadas aqui)
    # ------------------------------------------------------------------
    print(f"\n{_sep()}")
    print(f"  [3/4]  {_ts()}  Simulando eventos e erros...")
    print(_sep())
    t0 = time.time()

    df_eventos, df_erros, df_sessoes = gerar_eventos(df_sessoes, df_clientes)

    # Persiste sessões e eventos agora que estão completos
    df_sessoes.to_csv(cfg.OUTPUT_SESSOES, index=False, encoding="utf-8")
    df_eventos.to_csv(cfg.OUTPUT_EVENTOS, index=False, encoding="utf-8")
    df_erros.to_csv(cfg.OUTPUT_ERROS,     index=False, encoding="utf-8")

    tempos["eventos"] = time.time() - t0
    print(f"\n  ✓ sessoes.csv   "
          f"({len(df_sessoes):,} linhas | "
          f"{_tamanho_arquivo(cfg.OUTPUT_SESSOES)} | "
          f"{_hms(tempos['eventos'])})")
    print(f"  ✓ eventos.csv   "
          f"({len(df_eventos):,} linhas | "
          f"{_tamanho_arquivo(cfg.OUTPUT_EVENTOS)})")
    print(f"  ✓ erros.csv     "
          f"({len(df_erros):,} linhas | "
          f"{_tamanho_arquivo(cfg.OUTPUT_ERROS)})")

    # ------------------------------------------------------------------
    # ETAPA 4 — Avaliações
    # ------------------------------------------------------------------
    print(f"\n{_sep()}")
    print(f"  [4/4]  {_ts()}  Gerando avaliações...")
    print(_sep())
    t0 = time.time()

    df_avaliacoes = gerar_avaliacoes(df_sessoes, df_clientes, df_eventos)
    df_avaliacoes.to_csv(cfg.OUTPUT_AVALIACOES, index=False, encoding="utf-8")

    tempos["avaliacoes"] = time.time() - t0
    print(f"\n  ✓ avaliacoes.csv  "
          f"({len(df_avaliacoes):,} linhas | "
          f"{_tamanho_arquivo(cfg.OUTPUT_AVALIACOES)} | "
          f"{_hms(tempos['avaliacoes'])})")

    # ------------------------------------------------------------------
    # Tempo total
    # ------------------------------------------------------------------
    t_total = time.time() - t_inicio_total
    print(f"\n{_sep('═')}")
    print(f"  Pipeline concluído em {_hms(t_total)}")
    print(f"  Término: {_ts()}")
    print(_sep('═'))

    return {
        "clientes":   df_clientes,
        "sessoes":    df_sessoes,
        "eventos":    df_eventos,
        "erros":      df_erros,
        "avaliacoes": df_avaliacoes,
    }


# =============================================================================
# 3. VALIDAÇÃO CRUZADA FINAL
# =============================================================================

def validar_integridade(dfs: dict[str, pd.DataFrame]) -> bool:
    """
    Valida integridade referencial entre todas as tabelas.
    Retorna True se tudo estiver consistente.
    """
    print(f"\n{_sep()}")
    print("  VALIDAÇÃO DE INTEGRIDADE REFERENCIAL")
    print(_sep())

    erros_encontrados: list[str] = []

    def checar(condicao: bool, msg: str) -> None:
        status = "✓" if condicao else "✗"
        print(f"    {status}  {msg}")
        if not condicao:
            erros_encontrados.append(msg)

    cli_ids  = set(dfs["clientes"]["id_cliente"])
    sess_ids = set(dfs["sessoes"]["id_sessao"])
    ev_ids   = set(dfs["eventos"]["id_evento"])

    # Chaves primárias únicas
    checar(dfs["clientes"]["id_cliente"].is_unique,
           "clientes.id_cliente é único")
    checar(dfs["sessoes"]["id_sessao"].is_unique,
           "sessoes.id_sessao é único")
    checar(dfs["eventos"]["id_evento"].is_unique,
           "eventos.id_evento é único")
    checar(dfs["erros"]["id_erro"].is_unique,
           "erros.id_erro é único")
    checar(dfs["avaliacoes"]["id_avaliacao"].is_unique,
           "avaliacoes.id_avaliacao é único")

    # Chaves estrangeiras
    checar(dfs["sessoes"]["id_cliente"].isin(cli_ids).all(),
           "sessoes.id_cliente → clientes")
    checar(dfs["eventos"]["id_sessao"].isin(sess_ids).all(),
           "eventos.id_sessao → sessoes")
    checar(dfs["erros"]["id_evento"].isin(ev_ids).all(),
           "erros.id_evento → eventos")
    checar(dfs["avaliacoes"]["id_sessao"].isin(sess_ids).all(),
           "avaliacoes.id_sessao → sessoes")

    # Cardinalidade 1:1 avaliação × sessão
    checar(dfs["avaliacoes"]["id_sessao"].is_unique,
           "avaliacoes: no máximo 1 avaliação por sessão")

    # Cobertura: todos os clientes têm ao menos 1 sessão
    clientes_com_sessao = set(dfs["sessoes"]["id_cliente"])
    checar(cli_ids == clientes_com_sessao,
           "todos os clientes possuem ao menos 1 sessão")

    # Fluxo: primeira funcionalidade de cada sessão é LOGIN
    primeiro_ev = (
        dfs["eventos"]
        .sort_values(["id_sessao", "ordem"])
        .groupby("id_sessao")["funcionalidade"]
        .first()
    )
    checar((primeiro_ev == "LOGIN").all(),
           "todos os eventos começam com LOGIN")

    # Ranges de valores
    checar(dfs["clientes"]["idade"].between(18, 85).all(),
           "clientes.idade ∈ [18, 85]")
    checar(dfs["avaliacoes"]["nps"].between(0, 10).all(),
           "avaliacoes.nps ∈ [0, 10]")
    checar(dfs["avaliacoes"]["csat"].between(1, 5).all(),
           "avaliacoes.csat ∈ [1, 5]")
    checar((dfs["eventos"]["tempo_segundos"] >= 1).all(),
           "eventos.tempo_segundos ≥ 1")

    print()
    if erros_encontrados:
        print(f"  ✗  {len(erros_encontrados)} problema(s) encontrado(s).")
        for e in erros_encontrados:
            print(f"      → {e}")
        return False

    print(f"  ✓  Todas as verificações passaram.")
    return True


# =============================================================================
# 4. RELATÓRIO DE SÍNTESE
# =============================================================================

def imprimir_relatorio(dfs: dict[str, pd.DataFrame]) -> None:
    """
    Imprime um relatório analítico completo do dataset gerado,
    respondendo diretamente às perguntas de negócio do projeto.
    """
    cli  = dfs["clientes"]
    sess = dfs["sessoes"]
    ev   = dfs["eventos"]
    err  = dfs["erros"]
    av   = dfs["avaliacoes"]

    # Enriquecimento base
    sess_cli  = sess.merge(cli[["id_cliente", "persona", "segmento"]], on="id_cliente")
    ev_cli    = ev.merge(sess[["id_sessao", "id_cliente"]], on="id_sessao") \
                  .merge(cli[["id_cliente", "persona"]], on="id_cliente")
    av_aceitas = av[av["aceitou_pesquisa"] == True]
    av_full    = av_aceitas.merge(sess[["id_sessao", "id_cliente"]], on="id_sessao") \
                            .merge(cli[["id_cliente", "persona", "segmento"]], on="id_cliente")

    _print_header("RELATÓRIO DE SÍNTESE DO DATASET")

    # ------------------------------------------------------------------
    # SEÇÃO 1 — VISÃO GERAL DO DATASET
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  1. VISÃO GERAL DO DATASET")
    print(f"  {'─'*55}")

    total_ev  = len(ev)
    total_err = len(err)
    total_av  = len(av)
    total_ac  = len(av_aceitas)

    print(f"""
  ┌─────────────────────────────────────────────────┐
  │  Tabela          Registros       Arquivo         │
  ├─────────────────────────────────────────────────┤
  │  clientes        {len(cli):>10,}       {_tamanho_arquivo(cfg.OUTPUT_CLIENTES):<12}   │
  │  sessoes         {len(sess):>10,}       {_tamanho_arquivo(cfg.OUTPUT_SESSOES):<12}   │
  │  eventos       {total_ev:>12,}       {_tamanho_arquivo(cfg.OUTPUT_EVENTOS):<12}   │
  │  erros           {total_err:>10,}       {_tamanho_arquivo(cfg.OUTPUT_ERROS):<12}   │
  │  avaliacoes      {total_av:>10,}       {_tamanho_arquivo(cfg.OUTPUT_AVALIACOES):<12}   │
  └─────────────────────────────────────────────────┘

  Período simulado:  {cfg.DATA_INICIO} → {cfg.DATA_FIM}
  Clientes únicos:   {len(cli):,}
  Sessões totais:    {len(sess):,}  (média {len(sess)/len(cli):.1f} por cliente)
  Eventos totais:    {total_ev:,}  (média {total_ev/len(sess):.1f} por sessão)
  Erros registrados: {total_err:,}  ({total_err/total_ev*100:.2f}% dos eventos)
  Avaliações:        {total_av:,} convites → {total_ac:,} aceitas ({total_ac/total_av*100:.1f}%)
""")

    # ------------------------------------------------------------------
    # SEÇÃO 2 — PERFIL DA BASE DE CLIENTES
    # ------------------------------------------------------------------
    print(f"  {'─'*55}")
    print(f"  2. PERFIL DA BASE DE CLIENTES")
    print(f"  {'─'*55}\n")

    print("  Distribuição por Persona:")
    for persona, n in cli["persona"].value_counts().items():
        pct  = n / len(cli) * 100
        barr = "█" * int(pct / 2)
        print(f"    {persona:<25}  {n:>6,}  ({pct:4.1f}%)  {barr}")

    print("\n  Distribuição por Segmento:")
    for seg, n in cli["segmento"].value_counts().items():
        pct = n / len(cli) * 100
        print(f"    {seg:<15}  {n:>6,}  ({pct:.1f}%)")

    print(f"\n  Idade: média {cli['idade'].mean():.1f} anos  "
          f"| mediana {cli['idade'].median():.0f}  "
          f"| P10={cli['idade'].quantile(.1):.0f}  "
          f"| P90={cli['idade'].quantile(.9):.0f}")
    print(f"  Tempo de relacionamento: média {cli['tempo_relacionamento'].mean():.1f} anos")

    print("\n  Top 5 UFs:")
    for uf, n in cli["uf"].value_counts().head(5).items():
        pct = n / len(cli) * 100
        print(f"    {uf}  {n:>5,}  ({pct:.1f}%)")

    # ------------------------------------------------------------------
    # SEÇÃO 3 — JORNADA: ONDE OCORRE O MAIOR ABANDONO
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  3. JORNADA — ABANDONO E TEMPO POR FUNCIONALIDADE")
    print(f"  {'─'*55}\n")

    # Taxa de abandono por persona
    print("  Taxa de abandono por Persona:")
    for persona, taxa in (
        sess_cli.groupby("persona")["abandonada"].mean()
                .sort_values(ascending=False).items()
    ):
        barr = "█" * int(taxa * 200)
        print(f"    {persona:<25}  {taxa*100:5.1f}%  {barr}")

    # Funcionalidade com mais eventos de ABANDONO
    ev_abandono = ev[ev["status"] == "ABANDONO"]
    if len(ev_abandono) > 0:
        print(f"\n  Eventos de abandono por funcionalidade ({len(ev_abandono):,} total):")
        for func, n in ev_abandono["funcionalidade"].value_counts().items():
            pct = n / len(ev_abandono) * 100
            print(f"    {func:<15}  {n:>5,}  ({pct:.1f}%)")

    # Tempo médio por funcionalidade
    print("\n  Tempo médio por funcionalidade (todos os eventos):")
    tempo_func = ev.groupby("funcionalidade")["tempo_segundos"].mean().sort_values(ascending=False)
    tempo_cfg  = cfg.TEMPO_MEDIO_FUNCIONALIDADE
    for func, media in tempo_func.items():
        esperado = tempo_cfg.get(func, 0)
        diff     = media - esperado
        sinal    = "+" if diff >= 0 else ""
        print(f"    {func:<15}  {media:5.1f}s  (esperado {esperado}s  |  desvio {sinal}{diff:.1f}s)")

    # Sessões por hora do dia
    sess["_hora"] = pd.to_datetime(sess["data_hora_inicio"]).dt.hour
    print("\n  Volume de sessões por janela horária:")
    janelas = {"Madrugada 00–05h": (0,5), "Manhã 06–11h": (6,11),
               "Tarde 12–17h": (12,17), "Noite 18–23h": (18,23)}
    for label, (h1, h2) in janelas.items():
        n   = sess["_hora"].between(h1, h2).sum()
        pct = n / len(sess) * 100
        print(f"    {label:<22}  {n:>7,}  ({pct:.1f}%)")
    sess.drop(columns=["_hora"], inplace=True)

    # ------------------------------------------------------------------
    # SEÇÃO 4 — ERROS: ONDE OS CLIENTES ENCONTRAM MAIS DIFICULDADES
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  4. ERROS — DIFICULDADES E FRUSTRAÇÕES")
    print(f"  {'─'*55}\n")

    print("  Taxa de erro por funcionalidade (eventos com erro / total):")
    taxa_erro = (
        ev.groupby("funcionalidade")["teve_erro"].mean()
          .sort_values(ascending=False)
    )
    for func, taxa in taxa_erro.items():
        if taxa == 0:
            continue
        vol   = ev[ev["funcionalidade"] == func]["teve_erro"].sum()
        barr  = "█" * int(taxa * 500)
        print(f"    {func:<15}  {taxa*100:5.2f}%  ({vol:,} erros)  {barr}")

    print("\n  Distribuição por tipo de erro:")
    for tipo, n in err["tipo_erro"].value_counts().items():
        pct = n / total_err * 100
        print(f"    {tipo:<25}  {n:>5,}  ({pct:.1f}%)")

    print(f"\n  Taxa de resolução: {err['resolvido'].mean()*100:.1f}% dos erros foram resolvidos")
    print(f"  Tentativas médias por erro: {err['tentativas'].mean():.2f}")

    print("\n  Taxa de erro por Persona:")
    for persona, taxa in (
        ev_cli.groupby("persona")["teve_erro"].mean()
              .sort_values(ascending=False).items()
    ):
        print(f"    {persona:<25}  {taxa*100:.2f}%")

    print("\n  Taxa de erro por Versão do App:")
    ev_sess = ev.merge(sess[["id_sessao", "versao_app"]], on="id_sessao")
    for ver, taxa in (
        ev_sess.groupby("versao_app")["teve_erro"].mean()
               .sort_values(ascending=False).items()
    ):
        vol = ev_sess[ev_sess["versao_app"] == ver]["teve_erro"].sum()
        print(f"    v{ver:<8}  {taxa*100:.2f}%  ({vol:,} erros)")

    print("\n  Taxa de erro por Qualidade de Conexão:")
    ev_conn = ev.merge(sess[["id_sessao", "qualidade_conexao"]], on="id_sessao")
    for qual, taxa in (
        ev_conn.groupby("qualidade_conexao")["teve_erro"].mean()
               .sort_values(ascending=False).items()
    ):
        print(f"    {qual:<12}  {taxa*100:.2f}%")

    # ------------------------------------------------------------------
    # SEÇÃO 5 — SATISFAÇÃO: NPS E CSAT
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  5. SATISFAÇÃO — NPS, CSAT E SCORE DE EXPERIÊNCIA")
    print(f"  {'─'*55}\n")

    n_ac = len(av_aceitas)
    promotores  = (av_aceitas["nps"] >= 9).sum()
    neutros_nps = av_aceitas["nps"].between(7, 8).sum()
    detratores  = (av_aceitas["nps"] <= 6).sum()
    nps_score   = (promotores - detratores) / n_ac * 100

    print(f"  NPS Geral (n={n_ac:,} pesquisas aceitas):")
    print(f"    Promotores  (9–10):  {promotores:>6,}  ({promotores/n_ac*100:.1f}%)")
    print(f"    Neutros     (7–8):   {neutros_nps:>6,}  ({neutros_nps/n_ac*100:.1f}%)")
    print(f"    Detratores  (0–6):   {detratores:>6,}  ({detratores/n_ac*100:.1f}%)")
    print(f"    ▶  NPS Score:        {nps_score:+.1f}")
    print(f"    ▶  NPS médio:        {av_aceitas['nps'].mean():.2f}")
    print(f"    ▶  CSAT médio:       {av_aceitas['csat'].mean():.2f}")

    print("\n  NPS médio por Persona:")
    for persona, nps_med in (
        av_full.groupby("persona")["nps"].mean()
               .sort_values().items()
    ):
        det_pct = (av_full[av_full["persona"] == persona]["nps"] <= 6).mean() * 100
        print(f"    {persona:<25}  NPS {nps_med:.2f}  |  detratores {det_pct:.1f}%")

    print("\n  NPS médio por Segmento:")
    for seg, nps_med in (
        av_full.groupby("segmento")["nps"].mean()
               .sort_values().items()
    ):
        print(f"    {seg:<15}  NPS {nps_med:.2f}")

    print("\n  Score de experiência por Persona:")
    for persona, stats in (
        sess_cli.groupby("persona")["score_experiencia"]
                .agg(["mean", "median", "min"])
                .sort_values("mean").iterrows()
    ):
        print(f"    {persona:<25}  média {stats['mean']:.1f}  "
              f"| mediana {stats['median']:.0f}  "
              f"| mín {stats['min']:.0f}")

    print("\n  NPS médio por funcionalidade com erro (impacto no score):")
    # Sessões que tiveram erro em cada funcionalidade → NPS dessas sessões
    ev_erro_func = ev[ev["teve_erro"] == True][["id_sessao", "funcionalidade"]]
    av_com_sess  = av_aceitas.merge(ev_erro_func, on="id_sessao", how="inner")
    if len(av_com_sess) > 0:
        for func, nps_med in (
            av_com_sess.groupby("funcionalidade")["nps"].mean()
                       .sort_values().items()
        ):
            n_func = len(av_com_sess[av_com_sess["funcionalidade"] == func])
            print(f"    {func:<15}  NPS {nps_med:.2f}  (n={n_func:,})")

    # ------------------------------------------------------------------
    # SEÇÃO 6 — FEEDBACK: COMENTÁRIOS
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  6. FEEDBACK — COMENTÁRIOS E PADRÕES")
    print(f"  {'─'*55}\n")

    com_df  = av[av["comentario"].notna()]
    n_com   = len(com_df)
    print(f"  Total de comentários gerados: {n_com:,}")
    print(f"  Taxa de comentário (aceitas): {n_com/n_ac*100:.1f}%")

    print("\n  Palavras-chave mais frequentes nos comentários:")
    todas_palavras = " ".join(com_df["comentario"].str.lower()).split()
    stopwords = {
        "o","a","e","de","do","da","que","para","com","não","em",
        "os","as","um","uma","por","se","ao","na","no","me","muito",
        "mais","foi","tive","fiquei","consegui",
    }
    from collections import Counter
    freq = Counter(w for w in todas_palavras if w not in stopwords and len(w) > 3)
    for palavra, contagem in freq.most_common(15):
        barr = "█" * (contagem // max(1, n_com // 40))
        print(f"    {palavra:<25}  {contagem:>4,}  {barr}")

    print(f"\n  Amostra de comentários por faixa de NPS:")
    for nps_faixa, label in [(0, "NPS 0–3 (detratores severos)"),
                              (5, "NPS 4–6 (detratores)"),
                              (8, "NPS 7–8 (neutros)")]:
        sub = com_df[com_df["nps"] <= nps_faixa + 3]
        sub = sub[com_df["nps"] >= nps_faixa]
        if not sub.empty:
            amostra = sub["comentario"].sample(min(2, len(sub)), random_state=1).values
            print(f"\n  [{label}]")
            for c in amostra:
                print(f"    › {c}")

    # ------------------------------------------------------------------
    # SEÇÃO 7 — PRIORIZAÇÃO
    # ------------------------------------------------------------------
    print(f"\n  {'─'*55}")
    print(f"  7. PRIORIZAÇÃO — IMPACTO E ALCANCE DOS PROBLEMAS")
    print(f"  {'─'*55}\n")

    # Clientes afetados por funcionalidade
    print("  Clientes afetados por erros em cada funcionalidade:")
    ev_err_sess = ev[ev["teve_erro"] == True].merge(
        sess[["id_sessao", "id_cliente"]], on="id_sessao"
    )
    por_func_cli = (
        ev_err_sess.groupby("funcionalidade")["id_cliente"]
                   .nunique()
                   .sort_values(ascending=False)
    )
    total_cli = len(cli)
    for func, n_cli in por_func_cli.items():
        pct_cli = n_cli / total_cli * 100
        # Impacto no NPS
        av_func = av_com_sess[av_com_sess["funcionalidade"] == func] \
                  if len(av_com_sess) > 0 else pd.DataFrame()
        nps_impacto = f"NPS {av_func['nps'].mean():.1f}" if len(av_func) > 0 else "—"
        print(f"    {func:<15}  {n_cli:>5,} clientes  ({pct_cli:.1f}%)  |  {nps_impacto}")

    # Ranking de prioridade (volume de clientes afetados × queda no NPS)
    print("\n  Ranking de prioridade (score = clientes_afetados × impacto_nps):")
    max_nps = 10.0
    ranking = []
    for func, n_cli in por_func_cli.items():
        av_func = av_com_sess[av_com_sess["funcionalidade"] == func] \
                  if len(av_com_sess) > 0 else pd.DataFrame()
        if len(av_func) > 0:
            nps_medio_func = av_func["nps"].mean()
            impacto_nps    = max_nps - nps_medio_func   # quanto cai vs máximo
            score_prior    = n_cli * impacto_nps
            ranking.append((func, n_cli, nps_medio_func, score_prior))

    ranking.sort(key=lambda x: x[3], reverse=True)
    for i, (func, n_cli, nps_med, score) in enumerate(ranking, 1):
        print(f"    {i}º  {func:<15}  clientes: {n_cli:>5,}  "
              f"NPS médio: {nps_med:.1f}  score: {score:,.0f}")

    # Versão de app com mais problemas
    print("\n  Versão do app com maior volume de erros:")
    err_versao = err.merge(sess[["id_sessao", "versao_app"]], on="id_sessao")
    for ver, n in err_versao["versao_app"].value_counts().items():
        pct = n / total_err * 100
        print(f"    v{ver}  {n:>5,} erros  ({pct:.1f}%)")

    # ------------------------------------------------------------------
    # RESUMO EXECUTIVO
    # ------------------------------------------------------------------
    print(f"\n  {'═'*55}")
    print(f"  RESUMO EXECUTIVO")
    print(f"  {'═'*55}")

    top_func_erro   = taxa_erro.index[0]
    top_func_vol    = ev[ev["teve_erro"]==True]["funcionalidade"].value_counts().index[0]
    persona_pior    = sess_cli.groupby("persona")["score_experiencia"].mean().idxmin()
    persona_mais_ab = sess_cli.groupby("persona")["abandonada"].mean().idxmax()
    top_prioridade  = ranking[0][0] if ranking else "—"
    versao_pior     = err_versao["versao_app"].value_counts().index[0]

    print(f"""
  • Funcionalidade com maior TAXA de erro:    {top_func_erro} ({taxa_erro[top_func_erro]*100:.2f}%)
  • Funcionalidade com maior VOLUME de erros: {top_func_vol}
  • Tipo de erro dominante:                   TIMEOUT ({err['tipo_erro'].value_counts().iloc[0] / total_err*100:.1f}%)
  • Persona com PIOR experiência:             {persona_pior}
  • Persona com maior taxa de ABANDONO:       {persona_mais_ab}
  • NPS Score geral:                          {nps_score:+.1f}
  • CSAT médio geral:                         {av_aceitas['csat'].mean():.2f}
  • Funcionalidade de MAIOR PRIORIDADE:       {top_prioridade}
  • Versão do app com mais erros:             v{versao_pior}
  • % de sessões com pelo menos 1 erro:       {(sess['score_experiencia'] < 100).mean()*100:.1f}%
""")

    print(_sep('═'))


# =============================================================================
# 5. MODO REPORT-ONLY (lê CSVs existentes)
# =============================================================================

def carregar_csvs() -> dict[str, pd.DataFrame]:
    """Carrega os CSVs já gerados sem rodar o pipeline novamente."""
    print(f"\n[generator] Carregando CSVs existentes de {cfg.OUTPUT_DIR}...")
    dfs = {}
    mapeamento = {
        "clientes":   cfg.OUTPUT_CLIENTES,
        "sessoes":    cfg.OUTPUT_SESSOES,
        "eventos":    cfg.OUTPUT_EVENTOS,
        "erros":      cfg.OUTPUT_ERROS,
        "avaliacoes": cfg.OUTPUT_AVALIACOES,
    }
    for nome, path in mapeamento.items():
        if not os.path.exists(path):
            print(f"  ✗  {path} não encontrado. Execute sem --report-only primeiro.")
            sys.exit(1)
        print(f"  Lendo {path}...", end=" ", flush=True)
        dfs[nome] = pd.read_csv(path)
        print(f"{len(dfs[nome]):,} linhas")
    return dfs


# =============================================================================
# 6. ENTRY POINT
# =============================================================================

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Customer Journey Intelligence — Gerador de Dados Sintéticos"
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Pula a geração se todos os CSVs já existirem.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Apenas lê os CSVs existentes e imprime o relatório de síntese.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Executa o pipeline mas não imprime o relatório de síntese.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    csvs_existem = all(os.path.exists(p) for p in [
        cfg.OUTPUT_CLIENTES, cfg.OUTPUT_SESSOES, cfg.OUTPUT_EVENTOS,
        cfg.OUTPUT_ERROS, cfg.OUTPUT_AVALIACOES,
    ])

    if args.report_only:
        dfs = carregar_csvs()
    elif args.skip_if_exists and csvs_existem:
        print("[generator] CSVs já existem. Carregando sem regenerar...")
        dfs = carregar_csvs()
    else:
        dfs = executar_pipeline()

    integridade_ok = validar_integridade(dfs)

    if not args.no_report:
        imprimir_relatorio(dfs)

    sys.exit(0 if integridade_ok else 1)