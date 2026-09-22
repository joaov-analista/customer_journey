# =============================================================================
# customers.py
# Customer Journey Intelligence — Gerador da Tabela Clientes
#
# Responsabilidade única: gerar o DataFrame `clientes` com 20.000 registros,
# respeitando as correlações de negócio entre persona, segmento, renda,
# tipo de conta e comportamento esperado.
#
# Saída: data/raw/clientes.csv
# =============================================================================

import random
import numpy as np
import pandas as pd
from faker import Faker

import config as cfg

# ---------------------------------------------------------------------------
# Inicialização dos geradores de aleatoriedade (reprodutíveis)
# ---------------------------------------------------------------------------
random.seed(cfg.RANDOM_SEED)
np.random.seed(cfg.RANDOM_SEED)
fake = Faker("pt_BR")
Faker.seed(cfg.RANDOM_SEED)


# =============================================================================
# 1. DADOS GEOGRÁFICOS
# Faker pt_BR produz fragmentos de cidade quebrados; usamos lista curada.
# Cada UF tem entre 4 e 10 cidades representativas de diferentes portes.
# =============================================================================

CIDADES_POR_UF: dict[str, list[str]] = {
    "SP": ["São Paulo", "Campinas", "Santos", "Ribeirão Preto", "São Bernardo do Campo",
           "Guarulhos", "Osasco", "Sorocaba", "Mauá", "Bauru"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Montes Claros",
           "Uberaba", "Betim", "Governador Valadares"],
    "RJ": ["Rio de Janeiro", "Niterói", "Nova Iguaçu", "Duque de Caxias",
           "São Gonçalo", "Petrópolis", "Campos dos Goytacazes"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari",
           "Ilhéus", "Juazeiro", "Lauro de Freitas"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas",
           "Santa Maria", "Gravataí", "Novo Hamburgo"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa",
           "Cascavel", "São José dos Pinhais", "Foz do Iguaçu"],
    "PE": ["Recife", "Caruaru", "Olinda", "Petrolina",
           "Paulista", "Jaboatão dos Guararapes", "Garanhuns"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú",
           "Sobral", "Crato", "Iguatu"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis",
           "Rio Verde", "Luziânia", "Águas Lindas de Goiás"],
    "MA": ["São Luís", "Imperatriz", "Timon", "Caxias", "Codó"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José",
           "Criciúma", "Chapecó", "Itajaí"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos", "Bayeux"],
    "ES": ["Vitória", "Vila Velha", "Serra", "Cariacica", "Cachoeiro de Itapemirim"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante"],
    "AL": ["Maceió", "Arapiraca", "Rio Largo", "Palmeira dos Índios"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Castanhal"],
    "DF": ["Brasília", "Ceilândia", "Samambaia", "Taguatinga", "Planaltina"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Floriano"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Vilhena"],
    "AC": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira"],
    "AP": ["Macapá", "Santana", "Laranjal do Jari"],
    "RR": ["Boa Vista", "Rorainópolis", "Caracaraí"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "Itabaiana"],
}


# =============================================================================
# 2. REGRAS DE CORRELAÇÃO
# Cada persona possui distribuições próprias de segmento, renda e tipo de conta.
# Isso produz correlações naturais nos dados sem tornar nada determinístico.
# =============================================================================

# Pesos de segmento por persona (linhas somam 1.0)
#                              Varejo  Uniclass  Personnalité
SEGMENTO_POR_PERSONA: dict[str, list[float]] = {
    "Jovem Digital":        [0.75,    0.20,     0.05],
    "Cliente Tradicional":  [0.80,    0.17,     0.03],
    "Investidor":           [0.35,    0.50,     0.15],
    "Idoso":                [0.82,    0.15,     0.03],
    "Premium":              [0.10,    0.35,     0.55],
}

# Pesos de faixa de renda por persona
#                              ≤2k   2-5k  5-10k  10-20k  >20k
RENDA_POR_PERSONA: dict[str, list[float]] = {
    "Jovem Digital":        [0.35,  0.40,  0.18,   0.05,  0.02],
    "Cliente Tradicional":  [0.25,  0.38,  0.25,   0.09,  0.03],
    "Investidor":           [0.05,  0.20,  0.35,   0.28,  0.12],
    "Idoso":                [0.30,  0.35,  0.22,   0.10,  0.03],
    "Premium":              [0.02,  0.08,  0.20,   0.35,  0.35],
}

# Pesos de tipo de conta por persona
#                              Corrente  Digital  Salário
CONTA_POR_PERSONA: dict[str, list[float]] = {
    "Jovem Digital":        [0.25,     0.65,    0.10],
    "Cliente Tradicional":  [0.55,     0.20,    0.25],
    "Investidor":           [0.60,     0.30,    0.10],
    "Idoso":                [0.65,     0.10,    0.25],
    "Premium":              [0.75,     0.20,    0.05],
}

# Pesos de dispositivo por persona
#                              Android  iOS
DISPOSITIVO_POR_PERSONA: dict[str, list[float]] = {
    "Jovem Digital":        [0.55,    0.45],
    "Cliente Tradicional":  [0.65,    0.35],
    "Investidor":           [0.55,    0.45],
    "Idoso":                [0.72,    0.28],
    "Premium":              [0.40,    0.60],
}

# Labels para cada lista acima (mantém a ordem das colunas)
_SEGMENTOS     = ["Varejo", "Uniclass", "Personnalité"]
_FAIXAS_RENDA  = cfg.FAIXAS_RENDA
_TIPOS_CONTA   = ["Corrente", "Digital", "Salário"]
_DISPOSITIVOS  = ["Android", "iOS"]


# =============================================================================
# 3. FUNÇÕES AUXILIARES
# =============================================================================

def _escolher(opcoes: list, pesos: list) -> str:
    """Escolha ponderada sem replace."""
    return random.choices(opcoes, weights=pesos, k=1)[0]


def _gerar_uf() -> str:
    """Sorteia uma UF conforme os pesos populacionais definidos em config."""
    ufs   = list(cfg.UFS_PESOS.keys())
    pesos = list(cfg.UFS_PESOS.values())
    return _escolher(ufs, pesos)


def _gerar_cidade(uf: str) -> str:
    """Retorna uma cidade aleatória da UF sorteada."""
    cidades = CIDADES_POR_UF.get(uf, ["Capital"])
    return random.choice(cidades)


def _gerar_idade(persona: str) -> int:
    """Sorteia idade dentro da faixa da persona, com distribuição normal truncada."""
    idade_min, idade_max = cfg.PERSONA_IDADE[persona]
    media  = (idade_min + idade_max) / 2
    std    = (idade_max - idade_min) / 5   # ~99% dentro da faixa
    idade  = int(np.random.normal(media, std))
    return max(idade_min, min(idade_max, idade))


def _gerar_tempo_relacionamento(idade: int, tipo_conta: str) -> int:
    """
    Tempo de relacionamento (em anos) correlacionado com a idade do cliente.
    Clientes mais velhos tendem a ter relacionamentos mais longos.
    Conta Salário implica vínculo empregatício, geralmente mais recente.
    """
    max_rel     = max(1, idade - 18)          # não pode ter mais anos que a vida adulta
    media_anos  = max_rel * 0.45              # em média 45% da vida adulta
    std_anos    = max(1.0, media_anos * 0.40)
    anos        = int(np.random.normal(media_anos, std_anos))
    anos        = max(0, min(anos, max_rel))

    if tipo_conta == "Salário":
        anos = min(anos, 5)   # conta salário raramente ultrapassa o emprego atual

    return anos


def _gerar_sexo() -> str:
    """Distribuição aproximada da população bancarizada brasileira."""
    return random.choices(["M", "F"], weights=[0.51, 0.49], k=1)[0]


# =============================================================================
# 4. GERADOR PRINCIPAL
# =============================================================================

def gerar_cliente(id_cliente: int) -> dict:
    """
    Gera um único registro de cliente com todos os campos correlacionados.

    Fluxo de decisão:
        1. Sorteia a persona (define o perfil comportamental).
        2. Sorteia atributos demográficos correlacionados à persona.
        3. Preenche campos independentes.
        4. Retorna dicionário pronto para o DataFrame.
    """
    # --- Persona ---------------------------------------------------------
    personas = list(cfg.PERSONA_PESOS.keys())
    pesos_p  = list(cfg.PERSONA_PESOS.values())
    persona  = _escolher(personas, pesos_p)

    # --- Atributos correlacionados à persona -----------------------------
    segmento    = _escolher(_SEGMENTOS,    SEGMENTO_POR_PERSONA[persona])
    faixa_renda = _escolher(_FAIXAS_RENDA, RENDA_POR_PERSONA[persona])
    tipo_conta  = _escolher(_TIPOS_CONTA,  CONTA_POR_PERSONA[persona])
    dispositivo = _escolher(_DISPOSITIVOS, DISPOSITIVO_POR_PERSONA[persona])

    # --- Atributos demográficos ------------------------------------------
    idade                = _gerar_idade(persona)
    sexo                 = _gerar_sexo()
    uf                   = _gerar_uf()
    cidade               = _gerar_cidade(uf)
    tempo_relacionamento = _gerar_tempo_relacionamento(idade, tipo_conta)

    # --- Nome (apenas para enriquecer visualizações; não usado no modelo) -
    nome = fake.first_name() + " " + fake.last_name()

    return {
        "id_cliente":            id_cliente,
        "nome":                  nome,
        "idade":                 idade,
        "sexo":                  sexo,
        "cidade":                cidade,
        "uf":                    uf,
        "segmento":              segmento,
        "tempo_relacionamento":  tempo_relacionamento,
        "faixa_renda":           faixa_renda,
        "tipo_conta":            tipo_conta,
        "app_favorito":          dispositivo,
        "persona":               persona,
    }


# =============================================================================
# 5. FUNÇÃO PÚBLICA
# =============================================================================

def gerar_clientes(n: int = cfg.N_CLIENTES) -> pd.DataFrame:
    """
    Gera a tabela completa de clientes.

    Parâmetros
    ----------
    n : int
        Quantidade de clientes a gerar (padrão: cfg.N_CLIENTES).

    Retorna
    -------
    pd.DataFrame com colunas:
        id_cliente, nome, idade, sexo, cidade, uf, segmento,
        tempo_relacionamento, faixa_renda, tipo_conta,
        app_favorito, persona
    """
    print(f"[customers] Gerando {n:,} clientes...")

    registros = [gerar_cliente(i + 1) for i in range(n)]
    df        = pd.DataFrame(registros)

    _validar(df)
    _exibir_resumo(df)

    return df


# =============================================================================
# 6. VALIDAÇÕES INTERNAS
# =============================================================================

def _validar(df: pd.DataFrame) -> None:
    """
    Garante integridade mínima do DataFrame gerado.
    Levanta ValueError em caso de violação.
    """
    assert df["id_cliente"].is_unique, "IDs de cliente duplicados."
    assert df["id_cliente"].notna().all(), "IDs nulos encontrados."

    assert df["idade"].between(18, 85).all(), \
        f"Idades fora do intervalo permitido: {df.loc[~df['idade'].between(18, 85), 'idade'].unique()}"

    assert df["sexo"].isin(["M", "F"]).all(), "Valores inválidos em 'sexo'."

    assert df["segmento"].isin(_SEGMENTOS).all(), "Segmento inválido."
    assert df["tipo_conta"].isin(_TIPOS_CONTA).all(), "Tipo de conta inválido."
    assert df["app_favorito"].isin(_DISPOSITIVOS).all(), "Dispositivo inválido."
    assert df["persona"].isin(list(cfg.PERSONA_PESOS.keys())).all(), "Persona inválida."

    assert (df["tempo_relacionamento"] >= 0).all(), \
        "Tempo de relacionamento negativo encontrado."

    print("[customers] ✓ Validações concluídas sem erros.")


def _exibir_resumo(df: pd.DataFrame) -> None:
    """Imprime um resumo estatístico para inspeção rápida."""
    total = len(df)
    print(f"\n{'─'*50}")
    print(f"  RESUMO DA TABELA CLIENTES  ({total:,} registros)")
    print(f"{'─'*50}")

    print("\n  Distribuição por Persona:")
    for persona, qtd in df["persona"].value_counts().items():
        pct = qtd / total * 100
        print(f"    {persona:<25} {qtd:>6,}  ({pct:.1f}%)")

    print("\n  Distribuição por Segmento:")
    for seg, qtd in df["segmento"].value_counts().items():
        pct = qtd / total * 100
        print(f"    {seg:<25} {qtd:>6,}  ({pct:.1f}%)")

    print("\n  Distribuição por Tipo de Conta:")
    for conta, qtd in df["tipo_conta"].value_counts().items():
        pct = qtd / total * 100
        print(f"    {conta:<25} {qtd:>6,}  ({pct:.1f}%)")

    print("\n  Distribuição por Dispositivo:")
    for disp, qtd in df["app_favorito"].value_counts().items():
        pct = qtd / total * 100
        print(f"    {disp:<25} {qtd:>6,}  ({pct:.1f}%)")

    print("\n  Estatísticas de Idade:")
    print(f"    Média:   {df['idade'].mean():.1f} anos")
    print(f"    Mediana: {df['idade'].median():.0f} anos")
    print(f"    Min/Max: {df['idade'].min()} / {df['idade'].max()}")

    print("\n  Estatísticas de Tempo de Relacionamento:")
    print(f"    Média:   {df['tempo_relacionamento'].mean():.1f} anos")
    print(f"    Mediana: {df['tempo_relacionamento'].median():.0f} anos")

    print(f"\n  Top 5 UFs:")
    for uf, qtd in df["uf"].value_counts().head(5).items():
        pct = qtd / total * 100
        print(f"    {uf}  {qtd:>6,}  ({pct:.1f}%)")

    print(f"{'─'*50}\n")


# =============================================================================
# 7. EXECUÇÃO DIRETA (modo standalone)
# =============================================================================

if __name__ == "__main__":
    import os

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    df_clientes = gerar_clientes()
    df_clientes.to_csv(cfg.OUTPUT_CLIENTES, index=False, encoding="utf-8")

    print(f"[customers] Arquivo salvo em: {cfg.OUTPUT_CLIENTES}")
    print(f"[customers] Shape: {df_clientes.shape}")
    print(f"\n  Primeiros registros:\n")
    print(df_clientes.head(5).to_string(index=False))
