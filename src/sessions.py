# =============================================================================
# sessions.py
# Customer Journey Intelligence — Gerador da Tabela Sessões
#
# Responsabilidade única: para cada cliente do DataFrame de clientes, decidir
# quantas sessões ele terá, quando acontecerão e quais atributos de contexto
# (dispositivo, versão, conexão) cada sessão carregará.
#
# A tabela de sessões NÃO contém eventos nem avaliações — apenas o envelope
# temporal e técnico dentro do qual os eventos serão gerados por events.py.
#
# Saída: data/raw/sessoes.csv
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
# 1. PRÉ-COMPUTAÇÃO DO CALENDÁRIO DE PESOS
#
# Monta uma tabela com o peso de cada (data, hora) do ano — mais eficiente do
# que recalcular durante a geração de cada sessão.
# =============================================================================

def _construir_calendario_pesos() -> tuple[list[datetime], list[float]]:
    """
    Retorna dois arrays paralelos:
        - slots : lista de datetimes (um por hora do ano)
        - pesos : peso relativo de cada slot para sorteio

    Peso de um slot = peso_hora × peso_dia_semana × fator_mes × fator_dia_pico
    """
    inicio = datetime(cfg.DATA_INICIO.year, cfg.DATA_INICIO.month, cfg.DATA_INICIO.day)
    fim    = datetime(cfg.DATA_FIM.year,    cfg.DATA_FIM.month,    cfg.DATA_FIM.day, 23)

    slots: list[datetime] = []
    pesos: list[float]    = []

    cursor = inicio
    while cursor <= fim:
        hora       = cursor.hour
        dia_semana = cursor.weekday()   # 0 = segunda, 6 = domingo
        dia_mes    = cursor.day
        mes        = cursor.month

        w_hora   = cfg.PESO_HORA[hora]
        w_semana = cfg.PESO_DIA_SEMANA[dia_semana]
        w_mes    = cfg.FATOR_MES_BAIXO if mes in cfg.MESES_BAIXO_VOLUME else 1.0
        w_pico   = cfg.FATOR_DIA_PICO  if dia_mes in cfg.DIAS_PICO_MES  else 1.0

        slots.append(cursor)
        pesos.append(w_hora * w_semana * w_mes * w_pico)
        cursor += timedelta(hours=1)

    return slots, pesos


# Pré-computa uma única vez para todo o módulo
_SLOTS_ANO, _PESOS_ANO = _construir_calendario_pesos()
_PESOS_ANO_NP = np.array(_PESOS_ANO, dtype=np.float64)
_PESOS_ANO_NP /= _PESOS_ANO_NP.sum()   # distribução de probabilidade normalizada


# =============================================================================
# 2. ALOCAÇÃO DE SESSÕES POR PERSONA
#
# Em vez de escalar os parâmetros comportamentais (que refletem a realidade),
# distribuímos N_SESSOES proporcionalmente entre personas com base em:
#     peso_popup = PERSONA_PESOS[p] × PERSONA_SESSOES_MES[p]
#
# Isso preserva as proporções relativas de atividade entre personas enquanto
# respeita o volume total configurado.
# =============================================================================

def _calcular_sessoes_por_persona(n_total: int) -> dict[str, int]:
    """
    Distribui n_total sessões entre personas proporcionalmente à
    atividade esperada (peso populacional × frequência de uso).

    Retorna dict {persona: n_sessoes_totais_para_a_persona}.
    """
    pesos: dict[str, float] = {
        p: cfg.PERSONA_PESOS[p] * cfg.PERSONA_SESSOES_MES[p]
        for p in cfg.PERSONA_PESOS
    }
    soma = sum(pesos.values())

    alocacao: dict[str, int] = {}
    alocado = 0
    personas = list(pesos.keys())

    for i, persona in enumerate(personas):
        if i == len(personas) - 1:
            # Última persona recebe o restante (evita arredondamento acumulado)
            alocacao[persona] = n_total - alocado
        else:
            n = round(n_total * pesos[persona] / soma)
            alocacao[persona] = n
            alocado += n

    return alocacao


def _calcular_sessoes_por_cliente(
    df_clientes: pd.DataFrame,
    alocacao_persona: dict[str, int],
) -> pd.Series:
    """
    Para cada cliente, sorteia quantas sessões ele terá dentro da cota
    da sua persona usando distribuição de Poisson com variação individual
    via fator Gamma (simula heterogeneidade: heavy users vs light users).

    Retorna pd.Series indexada por id_cliente com a contagem de sessões.
    """
    contagens: dict[int, int] = {}

    for persona, n_sessoes_persona in alocacao_persona.items():
        df_p = df_clientes[df_clientes["persona"] == persona]
        n_clientes_p = len(df_p)

        if n_clientes_p == 0:
            continue

        # Média de sessões por cliente desta persona
        media_por_cliente = max(1.0, n_sessoes_persona / n_clientes_p)

        # Fator individual Gamma(2, 0.5): E=1.0, permite heavy users na cauda
        fatores = np.random.gamma(shape=2.0, scale=0.5, size=n_clientes_p)
        medias_individuais = np.maximum(1.0, media_por_cliente * fatores)

        # Poisson para contagem inteira por cliente
        n_sessoes_clientes = np.random.poisson(lam=medias_individuais).astype(int)
        n_sessoes_clientes = np.maximum(1, n_sessoes_clientes)

        # Ajusta total para bater exatamente n_sessoes_persona
        diff = n_sessoes_persona - n_sessoes_clientes.sum()
        if diff > 0:
            # Adiciona sessões extras distribuídas aleatoriamente
            idx_extras = np.random.choice(n_clientes_p, size=min(diff, n_clientes_p), replace=False)
            n_sessoes_clientes[idx_extras] += 1
        elif diff < 0:
            # Remove sessões excedentes (apenas de clientes com > 1 sessão)
            candidatos = np.where(n_sessoes_clientes > 1)[0]
            n_remover  = min(abs(diff), len(candidatos))
            idx_remover = np.random.choice(candidatos, size=n_remover, replace=False)
            n_sessoes_clientes[idx_remover] -= 1

        for id_cli, n in zip(df_p["id_cliente"].values, n_sessoes_clientes):
            contagens[id_cli] = int(n)

    return pd.Series(contagens, name="n_sessoes")


# =============================================================================
# 3. ATRIBUTOS CONTEXTUAIS DE SESSÃO
# =============================================================================

# Pesos de versão do app por persona:
# Jovem Digital e Investidor migram mais rápido para versões novas.
_VERSAO_PESOS_PERSONA: dict[str, dict[str, float]] = {
    "Jovem Digital":        {"5.8": 0.02, "5.9": 0.08, "6.0": 0.40, "6.1": 0.50},
    "Cliente Tradicional":  {"5.8": 0.06, "5.9": 0.18, "6.0": 0.48, "6.1": 0.28},
    "Investidor":           {"5.8": 0.02, "5.9": 0.10, "6.0": 0.42, "6.1": 0.46},
    "Idoso":                {"5.8": 0.12, "5.9": 0.28, "6.0": 0.42, "6.1": 0.18},
    "Premium":              {"5.8": 0.02, "5.9": 0.08, "6.0": 0.38, "6.1": 0.52},
}

# Pesos de qualidade de conexão por persona:
# Idoso tende a usar conexões mais instáveis (redes domésticas mais antigas).
_QUALIDADE_PESOS_PERSONA: dict[str, dict[str, float]] = {
    "Jovem Digital":        {"Excelente": 0.35, "Boa": 0.46, "Regular": 0.14, "Ruim": 0.05},
    "Cliente Tradicional":  {"Excelente": 0.28, "Boa": 0.46, "Regular": 0.19, "Ruim": 0.07},
    "Investidor":           {"Excelente": 0.38, "Boa": 0.45, "Regular": 0.13, "Ruim": 0.04},
    "Idoso":                {"Excelente": 0.18, "Boa": 0.40, "Regular": 0.28, "Ruim": 0.14},
    "Premium":              {"Excelente": 0.42, "Boa": 0.46, "Regular": 0.10, "Ruim": 0.02},
}


def _sortear_versao(persona: str) -> str:
    d = _VERSAO_PESOS_PERSONA[persona]
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


def _sortear_qualidade(persona: str) -> str:
    d = _QUALIDADE_PESOS_PERSONA[persona]
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


def _sortear_dispositivo(app_favorito: str) -> str:
    """
    O cliente usa preferencialmente o dispositivo cadastrado, mas pode ocasionalmente
    usar outro (ex.: tablet de familiar, troca recente de celular).
    """
    if random.random() < 0.92:
        return app_favorito
    return "iOS" if app_favorito == "Android" else "Android"


# =============================================================================
# 4. TIMESTAMPS DAS SESSÕES
# =============================================================================

def _sortear_timestamps(n_sessoes: int) -> list[datetime]:
    """
    Sorteia n_sessoes timestamps ao longo do ano, respeitando a sazonalidade
    hora × dia_semana × mês × dia_pico pré-computada.

    Retorna lista ordenada cronologicamente.
    """
    indices = np.random.choice(
        len(_SLOTS_ANO),
        size=n_sessoes,
        replace=True,
        p=_PESOS_ANO_NP,
    )

    timestamps = []
    for idx in indices:
        base     = _SLOTS_ANO[idx]
        minutos  = random.randint(0, 59)
        segundos = random.randint(0, 59)
        timestamps.append(base + timedelta(minutes=minutos, seconds=segundos))

    return sorted(timestamps)


# =============================================================================
# 5. DURAÇÃO ESTIMADA DA SESSÃO
# =============================================================================

_DURACAO_MEDIA_SESSAO: dict[str, int] = {
    "Jovem Digital":        90,
    "Cliente Tradicional":  150,
    "Investidor":           240,
    "Idoso":                300,
    "Premium":              210,
}

_DURACAO_CONEXAO_MULT: dict[str, float] = {
    "Excelente": 0.90,
    "Boa":       1.00,
    "Regular":   1.25,
    "Ruim":      1.60,
}


def _estimar_duracao(persona: str, qualidade: str) -> int:
    """
    Estima a duração da sessão em segundos via distribuição log-normal:
    garante valores positivos e produz cauda longa realista.
    A duração real será sobrescrita por events.py após a geração dos eventos.
    """
    media_base = _DURACAO_MEDIA_SESSAO[persona]
    media      = media_base * _DURACAO_CONEXAO_MULT[qualidade]

    cv    = 0.50   # coeficiente de variação
    sigma = np.sqrt(np.log(1 + cv**2))
    mu    = np.log(media) - sigma**2 / 2

    duracao = int(np.random.lognormal(mean=mu, sigma=sigma))
    return max(10, duracao)


# =============================================================================
# 6. MOTIVO DE ENCERRAMENTO
# =============================================================================

_PROB_ABANDONO_BASE: dict[str, float] = {
    "Jovem Digital":        0.12,
    "Cliente Tradicional":  0.07,
    "Investidor":           0.05,
    "Idoso":                0.15,
    "Premium":              0.06,
}

_ABANDONO_CONEXAO_MULT: dict[str, float] = {
    "Excelente": 0.5,
    "Boa":       1.0,
    "Regular":   1.5,
    "Ruim":      2.5,
}


def _sortear_motivo_encerramento(persona: str, qualidade: str) -> tuple[str, bool]:
    """
    Retorna (motivo_encerramento, abandonada).
    motivo_encerramento : 'Logout' | 'Abandono' | 'Timeout'
    abandonada          : bool
    """
    p_base     = _PROB_ABANDONO_BASE[persona]
    mult       = _ABANDONO_CONEXAO_MULT[qualidade]
    p_abandono = min(0.60, p_base * mult)

    r = random.random()
    if r < p_abandono:
        return "Abandono", True
    elif r < p_abandono + 0.05:
        return "Timeout", True
    else:
        return "Logout", False


# =============================================================================
# 7. GERADOR DE UMA SESSÃO
# =============================================================================

def _gerar_sessao(
    id_sessao:        int,
    id_cliente:       int,
    persona:          str,
    app_favorito:     str,
    timestamp_inicio: datetime,
) -> dict:
    """
    Gera um único registro de sessão com todos os atributos de contexto.
    """
    dispositivo          = _sortear_dispositivo(app_favorito)
    versao_app           = _sortear_versao(persona)
    qualidade            = _sortear_qualidade(persona)
    duracao              = _estimar_duracao(persona, qualidade)
    motivo, abandonada   = _sortear_motivo_encerramento(persona, qualidade)
    timestamp_fim        = timestamp_inicio + timedelta(seconds=duracao)

    return {
        "id_sessao":           id_sessao,
        "id_cliente":          id_cliente,
        "data_hora_inicio":    timestamp_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_fim":       timestamp_fim.strftime("%Y-%m-%d %H:%M:%S"),
        "duracao_segundos":    duracao,
        "dispositivo":         dispositivo,
        "versao_app":          versao_app,
        "qualidade_conexao":   qualidade,
        "abandonada":          abandonada,
        "motivo_encerramento": motivo,
    }


# =============================================================================
# 8. FUNÇÃO PÚBLICA
# =============================================================================

def gerar_sessoes(
    df_clientes: pd.DataFrame,
    n_sessoes: int = cfg.N_SESSOES,
) -> pd.DataFrame:
    """
    Gera a tabela completa de sessões para todos os clientes.

    Parâmetros
    ----------
    df_clientes : pd.DataFrame
        Saída de customers.gerar_clientes(). Deve conter:
        id_cliente, persona, app_favorito.
    n_sessoes : int
        Número total alvo de sessões a gerar (default: cfg.N_SESSOES).

    Retorna
    -------
    pd.DataFrame com colunas:
        id_sessao, id_cliente, data_hora_inicio, data_hora_fim,
        duracao_segundos, dispositivo, versao_app, qualidade_conexao,
        abandonada, motivo_encerramento
    """
    print(f"[sessions] Distribuindo {n_sessoes:,} sessões entre "
          f"{len(df_clientes):,} clientes...")

    # Passo 1: quantas sessões cabe para cada persona
    alocacao_persona = _calcular_sessoes_por_persona(n_sessoes)
    print(f"\n  Alocação por persona:")
    for persona, n in alocacao_persona.items():
        n_cli = len(df_clientes[df_clientes["persona"] == persona])
        print(f"    {persona:<25}  {n:>7,} sessões  "
              f"({n/n_cli:.1f} sess/cliente)")

    # Passo 2: quantas sessões cada cliente terá
    print(f"\n[sessions] Sorteando sessões por cliente...")
    n_por_cliente = _calcular_sessoes_por_cliente(df_clientes, alocacao_persona)

    # Passo 3: gerar os registros
    print(f"[sessions] Gerando registros de sessão...")
    registros: list[dict] = []
    id_sessao_counter = 1

    total_clientes = len(df_clientes)
    checkpoint     = max(1, total_clientes // 10)

    # Cria lookup rápido de persona e app_favorito por id_cliente
    lookup = df_clientes.set_index("id_cliente")[["persona", "app_favorito"]].to_dict("index")

    for i, (id_cliente, n_sess) in enumerate(n_por_cliente.items(), start=1):
        if i % checkpoint == 0:
            pct = i / total_clientes * 100
            print(f"  [{pct:5.1f}%] {i:,}/{total_clientes:,} clientes  "
                  f"| sessões: {len(registros):,}")

        info         = lookup[id_cliente]
        persona      = info["persona"]
        app_favorito = info["app_favorito"]

        timestamps = _sortear_timestamps(n_sess)

        for ts in timestamps:
            sessao = _gerar_sessao(
                id_sessao        = id_sessao_counter,
                id_cliente       = id_cliente,
                persona          = persona,
                app_favorito     = app_favorito,
                timestamp_inicio = ts,
            )
            registros.append(sessao)
            id_sessao_counter += 1

    df = pd.DataFrame(registros)

    _validar(df, df_clientes)
    _exibir_resumo(df)

    return df


# =============================================================================
# 9. VALIDAÇÕES INTERNAS
# =============================================================================

def _validar(df: pd.DataFrame, df_clientes: pd.DataFrame) -> None:
    """Garante integridade referencial e consistência dos dados."""

    assert df["id_sessao"].is_unique, \
        "IDs de sessão duplicados."
    assert df["id_sessao"].notna().all(), \
        "IDs de sessão nulos."

    clientes_validos = set(df_clientes["id_cliente"])
    assert df["id_cliente"].isin(clientes_validos).all(), \
        "Sessões com id_cliente sem correspondência em clientes."

    assert df["dispositivo"].isin(cfg.DISPOSITIVOS).all(), \
        "Dispositivo inválido em sessões."
    assert df["versao_app"].isin(cfg.VERSOES_APP).all(), \
        "Versão de app inválida em sessões."
    assert df["qualidade_conexao"].isin(cfg.QUALIDADES_CONEXAO).all(), \
        "Qualidade de conexão inválida."
    assert df["motivo_encerramento"].isin(["Logout", "Abandono", "Timeout"]).all(), \
        "Motivo de encerramento inválido."

    assert (df["duracao_segundos"] >= 10).all(), \
        "Sessões com duração menor que 10 segundos."

    mask_abandonada = df["abandonada"] == True
    motivos_abandonados = df.loc[mask_abandonada, "motivo_encerramento"].unique()
    assert "Logout" not in motivos_abandonados, \
        "Sessão marcada como abandonada com motivo 'Logout'."

    # Toda sessão deve ocorrer dentro da janela temporal configurada
    datas = pd.to_datetime(df["data_hora_inicio"])
    data_min = pd.Timestamp(cfg.DATA_INICIO)
    data_max = pd.Timestamp(cfg.DATA_FIM) + pd.Timedelta(days=1)
    assert (datas >= data_min).all() and (datas < data_max).all(), \
        "Sessões fora da janela temporal configurada."

    print("[sessions] ✓ Validações concluídas sem erros.")


# =============================================================================
# 10. RESUMO ESTATÍSTICO
# =============================================================================

def _exibir_resumo(df: pd.DataFrame) -> None:
    total = len(df)

    print(f"\n{'─'*58}")
    print(f"  RESUMO DA TABELA SESSÕES  ({total:,} registros)")
    print(f"{'─'*58}")

    print(f"\n  Volume total de sessões:        {total:,}")
    n_clientes = df["id_cliente"].nunique()
    print(f"  Clientes com ao menos 1 sessão: {n_clientes:,}")
    print(f"  Média de sessões por cliente:   {total / n_clientes:.1f}")

    # Sessões por mês
    dts = pd.to_datetime(df["data_hora_inicio"])
    df_tmp = df.copy()
    df_tmp["_mes"]  = dts.dt.to_period("M")
    df_tmp["_hora"] = dts.dt.hour
    df_tmp["_dow"]  = dts.dt.dayofweek

    print(f"\n  Sessões por mês:")
    por_mes = df_tmp.groupby("_mes").size()
    barra_unit = max(1, total // 12 // 30)
    for mes, qtd in por_mes.items():
        pct  = qtd / total * 100
        barr = "█" * (qtd // barra_unit)
        print(f"    {str(mes):<10}  {qtd:>7,}  ({pct:4.1f}%)  {barr}")

    # Janelas horárias
    janelas = {
        "Madrugada 00–05h": (0,  5),
        "Manhã     06–11h": (6,  11),
        "Tarde     12–17h": (12, 17),
        "Noite     18–23h": (18, 23),
    }
    print(f"\n  Distribuição por janela horária:")
    for label, (h_ini, h_fim) in janelas.items():
        qtd = df_tmp["_hora"].between(h_ini, h_fim).sum()
        pct = qtd / total * 100
        print(f"    {label}  {qtd:>7,}  ({pct:.1f}%)")

    # Dia da semana
    nomes_dow = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    print(f"\n  Distribuição por dia da semana:")
    for dow, nome in enumerate(nomes_dow):
        qtd = (df_tmp["_dow"] == dow).sum()
        pct = qtd / total * 100
        print(f"    {nome}  {qtd:>7,}  ({pct:.1f}%)")

    # Dispositivo
    print(f"\n  Distribuição por Dispositivo:")
    for disp, qtd in df["dispositivo"].value_counts().items():
        print(f"    {disp:<12}  {qtd:>7,}  ({qtd/total*100:.1f}%)")

    # Versão
    print(f"\n  Distribuição por Versão do App:")
    for ver, qtd in df["versao_app"].value_counts().sort_index().items():
        print(f"    v{ver:<8}  {qtd:>7,}  ({qtd/total*100:.1f}%)")

    # Qualidade
    print(f"\n  Distribuição por Qualidade de Conexão:")
    for qual, qtd in df["qualidade_conexao"].value_counts().items():
        print(f"    {qual:<12}  {qtd:>7,}  ({qtd/total*100:.1f}%)")

    # Encerramento
    n_aband = df["abandonada"].sum()
    print(f"\n  Motivo de encerramento:")
    for motivo, qtd in df["motivo_encerramento"].value_counts().items():
        print(f"    {motivo:<12}  {qtd:>7,}  ({qtd/total*100:.1f}%)")
    print(f"    → Taxa de abandono + timeout: {n_aband/total*100:.1f}%")

    # Duração
    dur = df["duracao_segundos"]
    print(f"\n  Duração das sessões (segundos):")
    print(f"    Média:    {dur.mean():.0f}s")
    print(f"    Mediana:  {dur.median():.0f}s")
    print(f"    P10:      {dur.quantile(0.10):.0f}s")
    print(f"    P90:      {dur.quantile(0.90):.0f}s")
    print(f"    Máximo:   {dur.max():.0f}s")

    print(f"{'─'*58}\n")


# =============================================================================
# 11. EXECUÇÃO DIRETA (modo standalone)
# =============================================================================

if __name__ == "__main__":
    import os
    from customers import gerar_clientes

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    df_clientes = gerar_clientes()
    df_sessoes  = gerar_sessoes(df_clientes)

    df_sessoes.to_csv(cfg.OUTPUT_SESSOES, index=False, encoding="utf-8")

    print(f"[sessions] Arquivo salvo em: {cfg.OUTPUT_SESSOES}")
    print(f"[sessions] Shape: {df_sessoes.shape}")
    print(f"\n  Primeiros registros:\n")
    print(df_sessoes.head(8).to_string(index=False))
