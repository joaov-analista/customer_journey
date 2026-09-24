# Customer journey

## Descrição do problema de negócio  
A experiência do cliente em canais digitais é um dos principais vetores de retenção e satisfação no mercado. Falhas na jornada digital impactam diretamente o NPS, aumentam o volume de atendimento humano e elevam o risco de churn.

Este projeto simula a jornada de 20.000 clientes em um aplicativo bancário fictício ao longo de 12 meses, gerando mais de 1,6 milhão de eventos de navegação. O objetivo é identificar onde os clientes encontram mais dificuldades, quais perfis têm pior experiência e quais melhorias devem ser priorizadas com base no impacto real sobre o NPS.

## Objetivos e perguntas respondidas  
O objetivo desse projeto foi analisar o comportamento do usuário em aplicativos, mas que pode ser replicado em outras áreas também que são impostantes no mercado.  

**Pergunta central**: "Recebemos milhares de reclamações e milhões de eventos de navegação todos os dias. Como podemos identificar os principais pontos de fricção da jornada digital e priorizar melhorias que realmente aumentem a satisfação dos clientes?"

**Perguntas de negócio**  
Onde os clientes encontram mais dificuldades?  
Quais funcionalidades geram maior frustração?  
Quais perfis possuem pior experiência?  
Em qual etapa ocorre o maior abandono?  
Quanto tempo o usuário leva em cada funcionalidade?  
Quais caminhos levam a uma experiência positiva?  
Quais assuntos aparecem com maior frequência nas reclamações?  
O sentimento varia conforme a funcionalidade?  
Existem padrões recorrentes?  
Qual melhoria deve ser feita primeiro?  
Qual funcionalidade gera maior impacto no NPS?  
Quais problemas afetam mais clientes?  

## Principais Insights

### Experiência
- **LOGIN concentra 46% de todos os erros** e tem taxa de 2,91% — quase o dobro do PIX (1,69%), segunda colocada.  
- **Idosos têm taxa de abandono de 65,14%** contra 3,73% do segmento Premium — a maior disparidade entre perfis.  

### Jornada
- **79,53% dos abandonos acontecem no LOGIN** — o cliente desiste antes mesmo de entrar no app.   
- Sessões com erro duram em média **2,2× mais** do que sessões sem erro.  
- Chat tem o maior tempo mediano por funcionalidade: **227 segundos**

### Feedback
- Os termos mais frequentes nos comentários negativos são **"lento"**, **"travou"** e **"inaceitável"**
- Sessões encerradas por abandono têm score médio de 24 — contra 94 das sessões com logout normal
- Versão 5.8 do app gera **2,8× mais erros** que a versão 6.1

### Priorização
- **LOGIN é a prioridade máxima**: 5.254 clientes afetados,
  score médio de 51,23 e maior volume absoluto de abandono
- **PIX é a segunda prioridade**: 3.054 clientes afetados com
  score médio de 65,90 — impacto financeiro direto
- Melhorar a conexão de qualidade "ruim" para "boa" reduz
  a probabilidade de erro em 4,5×

---

## Recomendações

| Prioridade | Ação | Impacto esperado |
|---|---|---|
| 1 | Reduzir erros de autenticação no LOGIN | Elimina 79% dos abandonos de sessão |
| 2 | Melhorar estabilidade do PIX | Reduz insatisfação em 3.054 clientes |
| 3 | Programa de acessibilidade digital para idosos | Reduz abandono de 65% para próximo da média |
| 4 | Forçar atualização da versão 5.8 | Remove multiplicador de erro de 2,8× |
| 5 | Otimizar tempo de resposta do CHAT | Reduz tempo mediano de 227s |

## Arquitetura da solução (diagrama simples)  
<img width="700" height="698" alt="diagram_customer_journey" src="https://github.com/user-attachments/assets/62a606bc-9c15-47d7-9e1b-e3557058ba89" />

## Stack utilizada  
Linguagem: Python 3.11 para Simulação e geração dos dados.  
Simulação: pandas, numpy, faker	para Geração de dados sintéticos.  
Banco de dados: PostgreSQL para	Armazenamento e camada analítica.  
Interface BD: pgAdmin 4	para Administração e execução de queries.  
Visualização: Power BI Desktop para Dashboard e apresentação dos insights.  
Versionamento: GitHub para Controle de versão e portfólio.  

## Como reproduzir o projeto (passo a passo)  
OBS: o dashboard está disponivel [Aqui](https://github.com/joaov-analista/customer_journey/tree/main/dashboard).  
Verifique todos os arquivos Python e altere os diretórios de entrada e saída dos dados

Baixe os arquivos Python [Aqui](https://github.com/joaov-analista/customer_journey/tree/main/src) e deixe todos na mesma pasta.    
No editor de código de sua preferência (recomendado VS Code), execute os arquivos Python nessa ordem:  

1. customers.py → gera clientes.csv  
2. sessions.py → lê clientes.csv, gera sessoes.csv  
3. events.py → lê sessoes.csv e clientes.csv, gera eventos.csv, erros.csv e atualiza sessoes.csv  
4. ratings.py → lê sessoes.csv, clientes.csv e eventos.csv, gera avaliacoes.csv  
5. generator.py → orquestra tudo acima em sequência e exporta todos os CSVs com um único comando.
6. validacoes.py → valida os dados gerados pelo python.
7. transformacao.py → aplica limpeza de espaços vazios, transforma valores categoricos e tipos de dados e verifica outliers. Gera CSVs tratados.
  
Importe os arquivos CSV gerados por `transformacao.py` para a interfacie BD de sua preferência (recomendado o PG Admin).  
Baixe os arquivos SQL [Aqui](https://github.com/joaov-analista/customer_journey/tree/main/sql).  
Execute os arquivos SQL nessa ordem:  
1. `criar_tabelas.sql` → cria as tabelas e o database  
2. `index.sql` → cria os indices para melhor performance do BD  
3. `views.sql` → cria as views respondendo as perguntas de negócio
   
Importe as views geradas em SQL para o Power BI (é necessário um conector postgreSQL) e monte o dashboard como quiser.   

## Autor e contato  
João Vítor - Analista de dados  
[Linkedin](https://www.linkedin.com/in/jo%C3%A3ovitoranalista/)
