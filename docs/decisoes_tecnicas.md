# Decisões Técnicas e Trade-offs

---

## 1. Por que dados sintéticos?

Dados reais de aplicativos bancários são sigilosos e protegidos por LGPD.
A simulação com regras de negócio realistas permite demonstrar as mesmas
capacidades analíticas sem violar privacidade ou depender de acesso
corporativo. O motor de simulação foi projetado para reproduzir padrões
comportamentais que ocorrem em aplicativos financeiros reais.

**Trade-off:** dados sintéticos não capturam comportamentos emergentes
imprevistos. Correlações e anomalias que surgiriam em dados reais não
aparecem aqui por construção.

---

## 2. Por que views em vez de tabelas materializadas?

As views foram escolhidas por simplicidade — o dataset é estático
(gerado uma única vez) e o volume não justifica materialização.

Em um ambiente de produção com dados atualizados diariamente,
a recomendação seria usar **materialized views** com refresh
agendado via Airflow ou pg_cron, reduzindo o tempo de resposta
das queries no Power BI.

---

## 3. Por que score calculado em vez de NPS direto?

Gerar NPS aleatório produziria uma distribuição artificial sem
correlação com o comportamento do cliente. O score intermediário
(0–100) permite acumular penalizações e bônus ao longo da sessão,
tornando o NPS final uma consequência da experiência e não um
número independente. Isso torna o dataset analiticamente coerente.

---

## 4. Por que separar erros em tabela própria?

Eventos com erro poderiam ter todos os campos de erro embutidos
na tabela `eventos`. A separação foi escolhida por três motivos:

- Mantém a tabela `eventos` enxuta para queries de volume
- Permite análises exclusivas de erros sem filtrar a tabela maior
- Reflete modelagem real de sistemas de log em produção

---

## 5. Limitações do projeto

- Dataset estático — não há pipeline de atualização automática
- Comentários sintéticos têm vocabulário limitado aos templates
  definidos em `config.py`
- Não modela multicanalidade (agência, telefone, internet banking)

---

## 6. Próximos passos

- Pipeline de ingestão com Apache Airflow
- Camada de dados com dbt para transformações versionadas
- Análise de sentimento nos comentários com Python (VADER ou BERT)
- Modelo preditivo de abandono de sessão
