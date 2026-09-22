# =============================================================================
# config.py
# Customer Journey Intelligence — Simulador de Jornada em App Bancário
#
# Centraliza todas as constantes, probabilidades e parâmetros da simulação.
# Nenhum valor mágico deve existir fora deste arquivo.
# =============================================================================

from datetime import date

# =============================================================================
# 1. PARÂMETROS GERAIS DA SIMULAÇÃO
# =============================================================================

RANDOM_SEED = 42  # Reprodutibilidade

# Volume de dados gerados
N_CLIENTES   = 20_000
N_SESSOES    = 200_000   # Alvo aproximado; varia por comportamento de persona
N_EVENTOS_ESTIMADOS = 1_000_000  # Referência de capacidade

# Janela temporal da simulação
DATA_INICIO = date(2024, 1, 1)
DATA_FIM    = date(2024, 12, 31)

# Caminhos de saída
OUTPUT_DIR = "C:\\Projetos banco de dados\\aplicativo bancario\\"
OUTPUT_CLIENTES    = OUTPUT_DIR + "clientes.csv"
OUTPUT_SESSOES     = OUTPUT_DIR + "sessoes.csv"
OUTPUT_EVENTOS     = OUTPUT_DIR + "eventos.csv"
OUTPUT_ERROS       = OUTPUT_DIR + "erros.csv"
OUTPUT_AVALIACOES  = OUTPUT_DIR + "avaliacoes.csv"


# =============================================================================
# 2. PERFIL DE CLIENTES
# =============================================================================

SEGMENTOS = ["Varejo", "Uniclass", "Personnalité"]

SEGMENTO_PESOS = {
    "Varejo":        0.70,
    "Uniclass":      0.22,
    "Personnalité":  0.08,
}

TIPOS_CONTA = ["Corrente", "Digital", "Salário"]

TIPOS_CONTA_PESOS = {
    "Corrente": 0.45,
    "Digital":  0.35,
    "Salário":  0.20,
}

DISPOSITIVOS = ["Android", "iOS"]

DISPOSITIVO_PESOS = {
    "Android": 0.62,
    "iOS":     0.38,
}

FAIXAS_RENDA = [
    "Até R$ 2.000",
    "R$ 2.001 – R$ 5.000",
    "R$ 5.001 – R$ 10.000",
    "R$ 10.001 – R$ 20.000",
    "Acima de R$ 20.000",
]

FAIXA_RENDA_PESOS = [0.25, 0.32, 0.22, 0.13, 0.08]

# UF com peso proporcional à população bancarizada (simplificado)
UFS_PESOS = {
    "SP": 0.22, "MG": 0.10, "RJ": 0.09, "BA": 0.07, "RS": 0.06,
    "PR": 0.06, "PE": 0.05, "CE": 0.05, "GO": 0.04, "MA": 0.03,
    "SC": 0.04, "PB": 0.02, "ES": 0.02, "AM": 0.02, "MT": 0.02,
    "MS": 0.02, "RN": 0.02, "AL": 0.01, "PA": 0.02, "DF": 0.02,
    "PI": 0.01, "TO": 0.01, "RO": 0.01, "AC": 0.01, "AP": 0.01,
    "RR": 0.01, "SE": 0.01,
}


# =============================================================================
# 3. PERSONAS
# =============================================================================

# Mapeamento persona → faixa etária
PERSONA_IDADE = {
    "Jovem Digital":        (18, 30),
    "Cliente Tradicional":  (31, 50),
    "Investidor":           (31, 55),
    "Idoso":                (60, 85),
    "Premium":              (30, 60),
}

# Probabilidade de cada persona na base de clientes
PERSONA_PESOS = {
    "Jovem Digital":        0.28,
    "Cliente Tradicional":  0.35,
    "Investidor":           0.15,
    "Idoso":                0.12,
    "Premium":              0.10,
}

# Segmento predominante por persona (guia a geração, não é exclusivo)
PERSONA_SEGMENTO_PREDOMINANTE = {
    "Jovem Digital":        "Digital",
    "Cliente Tradicional":  "Varejo",
    "Investidor":           "Uniclass",
    "Idoso":                "Varejo",
    "Premium":              "Personnalité",
}

# Sessões médias por mês por persona
PERSONA_SESSOES_MES = {
    "Jovem Digital":        18,
    "Cliente Tradicional":  10,
    "Investidor":           22,
    "Idoso":                5,
    "Premium":              16,
}

# Paciência: probabilidade de ABANDONAR após um erro (em vez de tentar novamente)
PERSONA_PROB_ABANDONO_POS_ERRO = {
    "Jovem Digital":        0.55,
    "Cliente Tradicional":  0.30,
    "Investidor":           0.20,
    "Idoso":                0.45,
    "Premium":              0.25,
}

# Número médio de funcionalidades usadas por sessão
PERSONA_FUNCS_POR_SESSAO = {
    "Jovem Digital":        2.5,
    "Cliente Tradicional":  2.0,
    "Investidor":           3.2,
    "Idoso":                1.5,
    "Premium":              3.0,
}


# =============================================================================
# 4. FUNCIONALIDADES DO APLICATIVO
# =============================================================================

FUNCIONALIDADES = [
    "LOGIN",
    "HOME",
    "SALDO",
    "PIX",
    "PAGAMENTO",
    "CARTAO",
    "INVESTIMENTOS",
    "CHAT",
    "LOGOUT",
]

# Funcionalidades navegáveis a partir de HOME (excluindo LOGIN/HOME/LOGOUT)
FUNCIONALIDADES_NAVEGAVEIS = [
    "SALDO",
    "PIX",
    "PAGAMENTO",
    "CARTAO",
    "INVESTIMENTOS",
    "CHAT",
]

# Fluxo obrigatório: LOGIN → HOME → [funcionalidade] → HOME → LOGOUT
# Não existe navegação direta entre funcionalidades (ex.: PIX → INVESTIMENTOS)
FLUXO_OBRIGATORIO = {
    "inicio": ["LOGIN", "HOME"],
    "fim":    ["HOME", "LOGOUT"],
}

# Probabilidade de uso de cada funcionalidade por persona (soma deve ser ≈ 1.0)
PROB_FUNCIONALIDADE = {
    #                     SALDO   PIX     PAGTO   CARTAO  INVEST  CHAT
    "Jovem Digital":      [0.20,  0.65,   0.05,   0.05,   0.02,   0.03],
    "Cliente Tradicional":[0.45,  0.30,   0.15,   0.05,   0.02,   0.03],
    "Investidor":         [0.20,  0.20,   0.05,   0.10,   0.40,   0.05],
    "Idoso":              [0.35,  0.25,   0.20,   0.05,   0.02,   0.13],
    "Premium":            [0.15,  0.35,   0.05,   0.10,   0.30,   0.05],
}

# Garante a ordem das colunas acima
FUNCIONALIDADES_NAVEGAVEIS_ORDER = [
    "SALDO", "PIX", "PAGAMENTO", "CARTAO", "INVESTIMENTOS", "CHAT"
]


# =============================================================================
# 5. TEMPO POR FUNCIONALIDADE (em segundos)
# =============================================================================

# Tempo médio esperado em condições normais
TEMPO_MEDIO_FUNCIONALIDADE = {
    "LOGIN":        8,
    "HOME":         5,
    "SALDO":        12,
    "PIX":          20,
    "PAGAMENTO":    28,
    "CARTAO":       18,
    "INVESTIMENTOS":35,
    "CHAT":         120,
    "LOGOUT":       3,
}

# Multiplicadores de tempo por situação
TEMPO_MULTIPLICADOR = {
    "normal":          1.0,
    "com_erro":        2.2,
    "pos_repeticao":   3.5,
    "conexao_ruim":    1.8,
    "conexao_regular": 1.3,
}

# Multiplicadores de tempo por persona (reflexo de familiaridade digital)
TEMPO_MULTIPLICADOR_PERSONA = {
    "Jovem Digital":        0.80,
    "Cliente Tradicional":  1.10,
    "Investidor":           0.90,
    "Idoso":                1.60,
    "Premium":              0.95,
}

# Desvio padrão como proporção do tempo médio (para variação natural)
TEMPO_STD_PROPORCAO = 0.25


# =============================================================================
# 6. QUALIDADE DE CONEXÃO
# =============================================================================

QUALIDADES_CONEXAO = ["Excelente", "Boa", "Regular", "Ruim"]

QUALIDADE_PESOS = {
    "Excelente": 0.30,
    "Boa":       0.45,
    "Regular":   0.18,
    "Ruim":      0.07,
}

# Multiplicador de probabilidade de erro por qualidade de conexão
QUALIDADE_ERRO_MULTIPLICADOR = {
    "Excelente": 0.5,
    "Boa":       1.0,
    "Regular":   2.0,
    "Ruim":      4.5,
}


# =============================================================================
# 7. VERSÕES DO APLICATIVO
# =============================================================================

VERSOES_APP = ["5.8", "5.9", "6.0", "6.1"]

VERSAO_PESOS = {
    "5.8": 0.05,   # versão legada, minoria ainda em uso
    "5.9": 0.15,
    "6.0": 0.45,
    "6.1": 0.35,
}

# Multiplicador de probabilidade de erro por versão
VERSAO_ERRO_MULTIPLICADOR = {
    "5.8": 2.8,
    "5.9": 1.6,
    "6.0": 1.0,
    "6.1": 0.8,
}


# =============================================================================
# 8. PROBABILIDADE DE ERROS
# =============================================================================

# Taxa base de erro por funcionalidade (sem ajustes de contexto)
PROB_ERRO_BASE = {
    "LOGIN":        0.020,
    "SALDO":        0.005,
    "PIX":          0.015,
    "PAGAMENTO":    0.010,
    "CARTAO":       0.008,
    "INVESTIMENTOS":0.012,
    "CHAT":         0.003,
    "HOME":         0.001,
    "LOGOUT":       0.000,
}

# Multiplicador de erro por persona (ex.: Idoso erra login com maior frequência)
PERSONA_ERRO_MULTIPLICADOR = {
    "LOGIN": {
        "Jovem Digital":        1.0,
        "Cliente Tradicional":  1.2,
        "Investidor":           0.9,
        "Idoso":                2.5,   # credencial incorreta com maior frequência
        "Premium":              0.8,
    },
    "DEFAULT": {
        "Jovem Digital":        1.0,
        "Cliente Tradicional":  1.1,
        "Investidor":           0.9,
        "Idoso":                1.3,
        "Premium":              0.7,
    },
}

# Tipos de erro compatíveis por funcionalidade
ERROS_POR_FUNCIONALIDADE = {
    "LOGIN": [
        "FALHA_AUTENTICACAO",
        "TIMEOUT",
        "SERVICO_INDISPONIVEL",
    ],
    "SALDO": [
        "TIMEOUT",
        "ERRO_INTERNO",
    ],
    "PIX": [
        "TIMEOUT",
        "SERVICO_INDISPONIVEL",
        "ERRO_INTERNO",
    ],
    "PAGAMENTO": [
        "TIMEOUT",
        "SERVICO_INDISPONIVEL",
        "ERRO_INTERNO",
        "CONEXAO_INTERROMPIDA",
    ],
    "CARTAO": [
        "TIMEOUT",
        "ERRO_INTERNO",
    ],
    "INVESTIMENTOS": [
        "TIMEOUT",
        "SERVICO_INDISPONIVEL",
        "ERRO_INTERNO",
    ],
    "CHAT": [
        "CONEXAO_INTERROMPIDA",
        "TIMEOUT",
    ],
    "HOME": [
        "ERRO_INTERNO",
    ],
}

# Pesos relativos dos tipos de erro (distribuição dentro de cada funcionalidade)
ERRO_TIPO_PESOS = {
    "TIMEOUT":              0.40,
    "FALHA_AUTENTICACAO":   0.25,
    "ERRO_INTERNO":         0.20,
    "CONEXAO_INTERROMPIDA": 0.10,
    "SERVICO_INDISPONIVEL": 0.05,
}

# Códigos de erro por tipo
ERRO_CODIGOS = {
    "TIMEOUT":              ["ERR_TIMEOUT_408", "ERR_GATEWAY_TIMEOUT_504"],
    "FALHA_AUTENTICACAO":   ["ERR_AUTH_401", "ERR_CREDENTIALS_INVALID"],
    "ERRO_INTERNO":         ["ERR_INTERNAL_500", "ERR_UNEXPECTED"],
    "CONEXAO_INTERROMPIDA": ["ERR_CONNECTION_LOST", "ERR_NETWORK_UNREACHABLE"],
    "SERVICO_INDISPONIVEL": ["ERR_SERVICE_503", "ERR_MAINTENANCE"],
}

# Probabilidade de resolução (nova tentativa bem-sucedida) por tipo de erro
PROB_ERRO_RESOLVIDO = {
    "TIMEOUT":              0.70,
    "FALHA_AUTENTICACAO":   0.80,
    "ERRO_INTERNO":         0.55,
    "CONEXAO_INTERROMPIDA": 0.60,
    "SERVICO_INDISPONIVEL": 0.30,
}

# Máximo de tentativas antes de desistir definitivamente
MAX_TENTATIVAS = 3


# =============================================================================
# 9. CÁLCULO DO SCORE DE EXPERIÊNCIA
# =============================================================================

# Score inicial (máximo possível)
SCORE_INICIAL = 100

# Penalizações aplicadas ao score durante a sessão
PENALIZACOES = {
    "erro_generico":            -20,
    "erro_timeout":             -15,
    "erro_falha_autenticacao":  -25,
    "erro_servico_indisponivel":-30,
    "abandono_funcionalidade":  -20,
    "abandono_sessao":          -35,
    "tempo_excessivo":          -10,   # acionado quando tempo > 2× a média
    "repeticao_acao":           -10,   # cada tentativa extra após a primeira
    "uso_chat":                 -10,   # indica que o cliente não achou o que precisava
    "sessao_muito_longa":       -10,   # > 10 min no total
}

# Bônus aplicados ao score
BONUS = {
    "sucesso_sem_erro":          +5,   # por funcionalidade concluída sem erro
    "logout_realizado":          +5,   # sessão encerrada corretamente
    "poucas_funcionalidades":    +3,   # sessão objetiva (≤ 2 funcionalidades)
}

# Conversão do score final (0–100) para NPS (0–10)
def score_para_nps(score: int) -> int:
    score = max(0, min(100, score))
    if score >= 85:
        return 10
    elif score >= 75:
        return 9
    elif score >= 65:
        return 8
    elif score >= 55:
        return 7
    elif score >= 45:
        return 6
    elif score >= 35:
        return 5
    elif score >= 25:
        return 4
    elif score >= 15:
        return 3
    elif score >= 8:
        return 2
    elif score >= 2:
        return 1
    else:
        return 0

# Conversão do score final (0–100) para CSAT (1–5)
def score_para_csat(score: int) -> int:
    score = max(0, min(100, score))
    if score >= 70:
        return 5
    elif score >= 50:
        return 4
    elif score >= 35:
        return 3
    elif score >= 20:
        return 2
    else:
        return 1


# =============================================================================
# 10. AVALIAÇÕES
# =============================================================================

# Percentual de sessões convidadas a responder a pesquisa
PROB_CONVIDADO_PESQUISA = 0.25

# Probabilidade de aceitar a pesquisa (dado que foi convidado)
PROB_ACEITAR_PESQUISA = {
    "Jovem Digital":        0.30,
    "Cliente Tradicional":  0.45,
    "Investidor":           0.50,
    "Idoso":                0.55,
    "Premium":              0.60,
}

# Comentário gerado apenas quando experiência ruim
NPS_LIMIAR_COMENTARIO  = 6   # NPS ≤ 6  gera comentário
CSAT_LIMIAR_COMENTARIO = 3   # CSAT ≤ 3 gera comentário

# Templates de comentário por funcionalidade problemática
# O gerador de comentários escolherá um template e personalizará levemente
COMENTARIOS_TEMPLATES = {
    "LOGIN": [
        "Não consigo acessar minha conta.",
        "Fiquei tentando fazer login várias vezes.",
        "O aplicativo não me deixa entrar.",
        "Tive problemas para autenticar.",
    ],
    "PIX": [
        "O PIX demorou muito para processar.",
        "Minha transferência via PIX falhou.",
        "O PIX não foi concluído e fiquei sem saber se o dinheiro saiu.",
        "Tive problemas ao realizar o PIX.",
    ],
    "PAGAMENTO": [
        "O pagamento do boleto não foi reconhecido.",
        "Demorei muito para conseguir pagar a conta.",
        "O aplicativo travou durante o pagamento.",
        "Meu pagamento ficou com status indefinido.",
    ],
    "SALDO": [
        "O saldo demorou para aparecer.",
        "A tela de extrato ficou carregando por muito tempo.",
        "Não consegui visualizar meu saldo.",
    ],
    "INVESTIMENTOS": [
        "A tela de investimentos demorou muito para carregar.",
        "Não consegui acessar minha carteira de investimentos.",
        "As informações de investimento estavam desatualizadas.",
    ],
    "CARTAO": [
        "Não consegui visualizar a fatura do cartão.",
        "O aplicativo travou na tela de cartões.",
        "As informações do cartão não carregaram.",
    ],
    "CHAT": [
        "O atendimento pelo chat demorou demais.",
        "Fiquei esperando por muito tempo no chat.",
        "O chat não funcionou corretamente.",
    ],
    "GERAL": [
        "O aplicativo está muito lento.",
        "Tive vários problemas durante o uso.",
        "A experiência poderia ser muito melhor.",
        "O app travou várias vezes.",
    ],
}


# =============================================================================
# 11. SAZONALIDADE
# =============================================================================

# Peso relativo de cada hora do dia para volume de sessões (índice 0 = 00h)
PESO_HORA = {
    0:  0.3,  1:  0.2,  2:  0.1,  3:  0.1,  4:  0.1,  5:  0.2,
    6:  0.5,  7:  1.2,  8:  1.8,  9:  1.6,  10: 1.4,  11: 1.3,
    12: 1.5,  13: 1.4,  14: 1.2,  15: 1.2,  16: 1.3,  17: 1.4,
    18: 1.8,  19: 2.0,  20: 1.9,  21: 1.7,  22: 1.2,  23: 0.7,
}

# Fator de volume por dia da semana (0 = segunda, 6 = domingo)
PESO_DIA_SEMANA = {
    0: 1.20,   # segunda
    1: 1.15,   # terça
    2: 1.15,   # quarta
    3: 1.10,   # quinta
    4: 1.05,   # sexta
    5: 0.70,   # sábado
    6: 0.55,   # domingo
}

# Dias do mês com maior volume (início do mês e dias de pagamento comuns)
DIAS_PICO_MES = [1, 2, 3, 4, 5, 10, 15, 20, 25]
FATOR_DIA_PICO = 1.40

# Funcionalidades com maior uso nos picos matinais (7h–9h)
BOOST_MANHA = {
    "SALDO": 1.5,
    "PIX":   1.3,
}

# Funcionalidades com maior uso no horário de almoço (12h–14h)
BOOST_ALMOCO = {
    "PAGAMENTO": 1.6,
    "PIX":       1.2,
}

# Funcionalidades com maior uso no período noturno (18h–22h)
BOOST_NOITE = {
    "PIX":          1.4,
    "SALDO":        1.2,
    "INVESTIMENTOS":1.3,
}

# Meses com volume levemente inferior (férias, menor atividade financeira)
MESES_BAIXO_VOLUME = [1, 7]
FATOR_MES_BAIXO = 0.85


# =============================================================================
# 12. AÇÕES REGISTRADAS NOS EVENTOS
# =============================================================================

ACOES = {
    "LOGIN":        ["ABRIR", "INSERIR_CREDENCIAL", "CONFIRMAR", "ERRO", "REPETIR"],
    "HOME":         ["ABRIR", "NAVEGAR"],
    "SALDO":        ["ABRIR", "VISUALIZAR", "ERRO"],
    "PIX":          ["ABRIR", "INSERIR_DADOS", "CONFIRMAR", "ERRO", "REPETIR"],
    "PAGAMENTO":    ["ABRIR", "ESCANEAR_BOLETO", "CONFIRMAR", "ERRO", "REPETIR"],
    "CARTAO":       ["ABRIR", "VISUALIZAR_FATURA", "ERRO"],
    "INVESTIMENTOS":["ABRIR", "VISUALIZAR_CARTEIRA", "SIMULAR", "ERRO"],
    "CHAT":         ["ABRIR", "DIGITAR_MENSAGEM", "AGUARDAR_RESPOSTA", "ENCERRAR"],
    "LOGOUT":       ["CONFIRMAR"],
}

# Status possíveis de um evento
STATUS_EVENTO = ["SUCESSO", "ERRO", "ABANDONO"]


# =============================================================================
# 13. LIMITES E THRESHOLDS OPERACIONAIS
# =============================================================================

# Tempo máximo de inatividade antes de considerar sessão encerrada por timeout (segundos)
TIMEOUT_INATIVIDADE = 300  # 5 minutos

# Tempo total de sessão considerado "muito longo" (aciona penalização)
SESSAO_LONGA_THRESHOLD = 600  # 10 minutos

# Tempo por funcionalidade considerado "excessivo" (múltiplo do tempo médio)
TEMPO_EXCESSIVO_FATOR = 2.0

# Quantidade mínima de sessões por cliente para entrar na análise de cohort
MIN_SESSOES_COHORT = 3
