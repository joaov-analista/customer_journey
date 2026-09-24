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
OBS: o dashboard está disponivel [Aqui]().  
Verifique todos os arquivos Python e altere os diretórios de entrada e saída dos dados

Baixe os arquivos Python [Aqui]() e deixe todos na mesma pasta.    
No editor de código de sua preferência (recomendado VS Code), execute os arquivos Python nessa ordem:  
1. customers.py → gera clientes.csv  
2. sessions.py → lê clientes.csv, gera sessoes.csv  
3. events.py → lê sessoes.csv e clientes.csv, gera eventos.csv, erros.csv e atualiza sessoes.csv  
4. ratings.py → lê sessoes.csv, clientes.csv e eventos.csv, gera avaliacoes.csv  
5. generator.py → orquestra tudo acima em sequência e exporta todos os CSVs com um único comando.
6. validacoes.py → valida os dados gerados pelo python.
7. transformacao.py → aplica limpeza de espaços vazios, transforma valores categoricos e tipos de dados e verifica outliers. Gera CSVs tratados.  
Importe os arquivos CSV gerados para a interfacie BD de sua preferência (recomendado o PG Admin).  
Baixe os arquivos SQL [Aqui]().  
Execute o arquivo  
Execute o arquivo
Importe as views geradas em SQL para o Power BI (é necessário um conector postgreSQL) e monte o dashboard como quiser.  

## Estrutura de pastas  
customer_journey_inteligence/  
├── README.md  
├── docs/  
│   ├── dicionario_de_dados.md  
│   ├── regras_de_negocio.md  
│   ├── documentacao_views.md  
│   ├── decisoes_tecnicas.md  
│   ├── lineage.md  
│   └── erd.png  
│  
├── src/  
│   ├── config.py  
│   ├── customers.py  
│   ├── sessions.py  
│   ├── events.py  
│   ├── ratings.py  
│   └── generator.py  
│  
├── sql/  
│   ├── criacao_tabelas.sql  
|   ├── index.sql  
│   └── views/  
│       ├── views.sql  
|
├── data/  
│   └── raw/        ← CSVs gerados (ou .gitignore se forem grandes)
│  
└── dashboard/  
    └── customer_journey.pbix  

## Autor e contato  
João Vítor - Analista de dados  
[Linkedin](https://www.linkedin.com/in/jo%C3%A3ovitoranalista/)
