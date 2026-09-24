# Regras de Negócio

## 1. Personas

Cada cliente pertence a uma persona que define seu comportamento dentro do app.

| Persona | Faixa etária | Característica principal |
|---|---|---|
| Jovem Digital | 18–30 | Alta frequência de PIX, baixa paciência com erros |
| Cliente Tradicional | 31–50 | Usa saldo, pagamento e cartão |
| Investidor | 31–55 | Alta frequência, foco em investimentos |
| Idoso | 60–85 | Maior tempo em tela, mais erros de login, maior abandono |
| Premium | 30–60 | Segmento Personnalité, usa investimentos e cartão |

---

## 2. Fluxo de Navegação

Toda sessão segue obrigatoriamente esta ordem:

LOGIN → HOME → [funcionalidade] → HOME → [funcionalidade] → HOME → LOGOUT

- Nenhuma funcionalidade pode ser acessada antes do LOGIN
- Não existe navegação direta entre funcionalidades (ex: PIX → INVESTIMENTOS)
- O cliente sempre retorna ao HOME antes de acessar outra funcionalidade

---

## 3. Funcionalidades Disponíveis

| Código | Funcionalidade |
|---|---|
| LOGIN | Autenticação |
| HOME | Tela inicial |
| SALDO | Consulta de saldo e extrato |
| PIX | Transferência via PIX |
| PAGAMENTO | Pagamento de boletos |
| CARTAO | Cartões e fatura |
| INVESTIMENTOS | Carteira de investimentos |
| CHAT | Atendimento ao cliente |
| LOGOUT | Encerramento da sessão |

---

## 4. Probabilidade de Uso por Persona

| Funcionalidade | Jovem Digital | Tradicional | Investidor | Idoso | Premium |
|---|---|---|---|---|---|
| SALDO | 20% | 45% | 20% | 35% | 15% |
| PIX | 65% | 30% | 20% | 25% | 35% |
| PAGAMENTO | 5% | 15% | 5% | 20% | 5% |
| CARTAO | 5% | 5% | 10% | 5% | 10% |
| INVESTIMENTOS | 2% | 2% | 40% | 2% | 30% |
| CHAT | 3% | 3% | 5% | 13% | 5% |

---

## 5. Probabilidade de Erro

A taxa de erro de cada evento é calculada pela combinação de quatro fatores:

P(erro) = taxa_base × mult_persona × mult_versao × mult_conexao

**Taxa base por funcionalidade:**

| Funcionalidade | Taxa base |
|---|---|
| LOGIN | 2,0% |
| PIX | 1,5% |
| INVESTIMENTOS | 1,2% |
| PAGAMENTO | 1,0% |
| CARTAO | 0,8% |
| SALDO | 0,5% |
| CHAT | 0,3% |
| HOME | 0,1% |
| LOGOUT | 0,0% |

**Multiplicadores de versão do app:**

| Versão | Multiplicador |
|---|---|
| 5.8 | 2,8× |
| 5.9 | 1,6× |
| 6.0 | 1,0× |
| 6.1 | 0,8× |

**Multiplicadores de qualidade de conexão:**

| Qualidade | Multiplicador |
|---|---|
| Excelente | 0,5× |
| Boa | 1,0× |
| Regular | 2,0× |
| Ruim | 4,5× |

---

## 6. Tipos de Erro por Funcionalidade

| Tipo de Erro | Funcionalidades compatíveis |
|---|---|
| TIMEOUT | LOGIN, SALDO, PIX, PAGAMENTO, CARTAO, INVESTIMENTOS, CHAT |
| FALHA_AUTENTICACAO | LOGIN |
| ERRO_INTERNO | SALDO, PIX, PAGAMENTO, CARTAO, INVESTIMENTOS, HOME |
| CONEXAO_INTERROMPIDA | PAGAMENTO, CHAT |
| SERVICO_INDISPONIVEL | LOGIN, PIX, PAGAMENTO, INVESTIMENTOS |

---

## 7. Comportamento Pós-Erro

Após um erro, o cliente pode tentar novamente ou abandonar.

- Máximo de 3 tentativas por evento
- A probabilidade de abandono varia por persona:

| Persona | Abandono pós-erro |
|---|---|
| Jovem Digital | 55% |
| Idoso | 45% |
| Cliente Tradicional | 30% |
| Premium | 25% |
| Investidor | 20% |

---

## 8. Cálculo do Score de Experiência

Cada sessão inicia com 100 pontos e sofre penalizações conforme os eventos.

**Penalizações:**

| Evento | Pontos |
|---|---|
| Erro genérico | −20 |
| Falha de autenticação | −25 |
| Serviço indisponível | −30 |
| Timeout | −15 |
| Abandono de funcionalidade | −20 |
| Abandono de sessão | −35 |
| Repetição de ação | −10 |
| Uso do chat | −10 |
| Tempo excessivo na tela | −10 |
| Sessão muito longa (> 10 min) | −10 |

**Bônus:**

| Evento | Pontos |
|---|---|
| Funcionalidade concluída sem erro | +5 |
| Logout realizado | +5 |
| Sessão com ≤ 2 funcionalidades | +3 |

---

## 9. Conversão Score → NPS e CSAT

| Score | NPS | CSAT |
|---|---|---|
| 85–100 | 10 | 5 |
| 75–84 | 9 | 5 |
| 65–74 | 8 | 4 |
| 55–64 | 7 | 4 |
| 45–54 | 6 | 3 |
| 35–44 | 5 | 3 |
| 25–34 | 4 | 2 |
| 15–24 | 3 | 2 |
| 8–14 | 2 | 1 |
| 2–7 | 1 | 1 |
| 0–1 | 0 | 1 |

O NPS e CSAT finais recebem um ruído de ±1 para simular subjetividade humana.

---

## 10. Avaliações

- 25% das sessões são convidadas a responder a pesquisa
- A aceitação varia por persona (Premium: 60%, Idoso: 55%, Jovem Digital: 30%)
- Comentários são gerados apenas quando NPS ≤ 6 ou CSAT ≤ 3
- Sessões com score < 45 têm probabilidade de aceite aumentada em 40%

---

## 11. Sazonalidade

- Pico de sessões: 19h–20h e 7h–9h
- Dias úteis geram mais sessões que fins de semana (Segunda: 1,2× vs Domingo: 0,55×)
- Janeiro e julho têm volume 15% menor
- Dias 1, 2, 3, 4, 5, 10, 15, 20 e 25 do mês têm volume 40% maior
- PIX e Saldo têm boost no período da manhã (7h–9h)
- Pagamento tem boost no almoço (12h–14h)
- PIX, Saldo e Investimentos têm boost à noite (18h–22h)
