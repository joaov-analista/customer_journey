# Decisões Técnicas e Trade-offs

---

## 1. Por que dados sintéticos?

Dados reais de aplicativos bancários são sigilosos e protegidos por LGPD.
A simulação com regras de negócio realistas permite demonstrar as mesmas
capacidades analíticas sem violar privacidade ou depender de acesso
corporativo. O motor de simulação foi projetado para reproduzir padrões
comportamentais observados em aplicativos financeiros reais.

**Trade-off:** dados sintéticos não capturam comportamentos emergentes
imprevistos. Correlações e anomalias que surgiriam em dados reais não
aparecem aqui por construção.

---

## 2. Por que PostgreSQL em vez de MySQL?

| Critério | PostgreSQL | MySQL |
|---|---|---|
| Índices parciais | ✅ Suportado | ❌ Não suportado |
| Tipo BOOLEAN nativo | ✅ Sim | ❌ Usa TINYINT |
| Encoding padrão | UTF-8 | Requer configuração |
| Performance analítica | Superior | Inferior em queries complexas |
| Funções de janela | Completas | Limitadas em versões antigas |

Para um projeto analítico com 1,6 milhão de eventos e queries com
múltiplos JOINs e agregações, PostgreSQL é a escolha mais adequada.

---

## 3. Por que views em vez de tabelas materializadas?

As views foram escolhidas por simplicidade — o dataset é estático
(gerado uma única vez) e o volume não justifica materialização.

Em um ambiente de produção com dados atualizados diariamente,
a recomendação seria usar **materialized views** com refresh
agendado via Airflow ou pg_cron, reduzindo o tempo de resposta
das queries no Power BI.

---

## 4. Por que score calculado em vez de NPS direto?

Gerar NPS aleatório produziria uma distribuição artificial sem
correlação com o comportamento do cliente. O score intermediário
(0–100) permite acumular penalizações e bônus ao longo da sessão,
tornando o NPS final uma consequência da experiência — não um
número independente. Isso torna o dataset analiticamente coerente.

---

## 5. Por que separar erros em tabela própria?

Eventos com erro poderiam ter todos os campos de erro embutidos
na tabela `eventos`. A separação foi escolhida por três motivos:

- Mantém a tabela `eventos` enxuta para queries de volume
- Permite análises exclusivas de erros sem filtrar a tabela maior
- Reflete modelagem real de sistemas de log em produção

---

## 6. Por que o campo id_sessao foi adicionado na tabela erros?

Por regra relacional, bastaria o `id_evento` para chegar à sessão
via JOIN. O `id_sessao` foi adicionado como atalho para evitar
JOINs desnecessários nas queries analíticas mais frequentes,
melhorando performance nas views de priorização e sazonalidade.

---

## 7. Limitações do projeto

- Dataset estático — não há pipeline de atualização automática
- Comentários sintéticos têm vocabulário limitado aos templates
  definidos em `config.py` — análise de NLP real exigiria
  comentários orgânicos
- Ausência de análise de coorte temporal (retenção, churn)
- Não modela multicanalidade (agência, telefone, internet banking)
- Score de experiência não considera histórico do cliente —
  cada sessão é avaliada de forma independente

---

## 8. Próximos passos sugeridos

- Pipeline de ingestão com Apache Airflow
- Camada de dados com dbt para transformações versionadas
- Análise de sentimento nos comentários com Python (VADER ou BERT)
- Análise de coorte de retenção por persona
- Modelo preditivo de abandono de sessão
