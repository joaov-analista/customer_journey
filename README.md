# customer_journey

## Descrição do problema de negócio  

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
## Como reproduzir o projeto (passo a passo)  
OBS: o dashboard está disponivel [Aqui]().  

Baixe os arquivos Python [Aqui]() e deixe todos na mesma pasta.    
Execute os arquivos nessa ordem no editor de código de sua preferência (recomendado VS Code):    
Importe os arquivos CSV gerados para o SGBD de sua preferência (recomendado o PG Admin).  
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
│   ├── ddl_criacao_tabelas.sql  
│   └── views/  
│       ├── vw_dificuldade_p_funcionalidade.sql  
│       ├── vw_frustracao_por_funcionalidade.sql  
│       └── ...  
│  
├── data/  
│   └── raw/        ← CSVs gerados (ou .gitignore se forem grandes)
│  
└── dashboard/  
    └── customer_journey.pbix  

## Autor e contato  
João Vítor - Analista de dados  
[Linkedin](https://www.linkedin.com/in/jo%C3%A3ovitoranalista/)
