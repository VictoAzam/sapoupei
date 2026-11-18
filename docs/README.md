# Documentação do sapoupei

Este diretório reúne a documentação funcional e técnica do sistema. Os documentos descrevem o comportamento encontrado no código atual; quando houver diferença entre documentação e implementação, a implementação deve ser tratada como referência até que uma mudança seja aprovada.

## Guias

| Documento | Conteúdo | Uso principal |
| --- | --- | --- |
| [Visão geral e requisitos](visao-geral.md) | Objetivo, usuários, escopo, requisitos funcionais e regras de negócio | Apresentar o problema e o que o sistema entrega |
| [Diagramas do sistema](diagramas.md) | Casos de uso, arquitetura, banco, classes, fluxos e implantação | Usar diretamente nos slides e na explicação visual |
| [Arquitetura e fluxos](arquitetura.md) | Camadas, componentes, rotas e diagramas de sequência | Explicar como as partes se comunicam |
| [Banco de dados](banco-de-dados.md) | Modelo entidade-relacionamento, tabelas, campos e migrações | Apresentar o desenho e a evolução do schema |
| [Referência técnica](referencia-tecnica.md) | Classes, formulários, serviços, funções e comandos | Apoiar manutenção e avaliação técnica |
| [Segurança e operação](seguranca-operacao.md) | Controles, configuração, execução, migração e testes | Demonstrar cuidados e instruções operacionais |
| [Roteiro de apresentação](apresentacao.md) | Sequência sugerida de slides e demonstração | Preparar uma apresentação oral curta |
| [Guia de estudos](guia-de-estudos.md) | Trilha de estudo, conceitos explicados, perguntas e respostas | Estudar o sistema e se preparar para a banca |

## Resumo executivo

O sapoupei é uma aplicação web para controle pessoal de receitas e despesas. Usuários autenticados registram movimentações, acompanham totais e metas mensais e consultam dicas. Administradores acessam indicadores agregados e exportam um relatório CSV sem dados nominais ou transações individuais.

Para visualizar os desenhos no VS Code, abra [Diagramas do sistema](diagramas.md) e use **Markdown: Open Preview** (`Ctrl+Shift+V`).

## Tecnologias

- Python e Flask para aplicação web e rotas.
- Flask-Login para sessão/autenticação e Flask-WTF para formulários e CSRF.
- Flask-SQLAlchemy e SQLAlchemy para persistência; MySQL é o banco configurado por padrão.
- Flask-Migrate/Alembic para versionamento de schema.
- Flask-Mail e itsdangerous para recuperação de senha por e-mail.
- Jinja, CSS e JavaScript para interface; Chart.js para gráficos administrativos.
- Manifesto e service worker para instalação PWA e cache apenas de arquivos estáticos.
- Docker Compose para execução local com MySQL e Gunicorn.

## Escopo e limites

O sistema é um projeto de educação e organização financeira pessoal. O perfil é uma classificação simples, não é aconselhamento financeiro. A aplicação não integra contas bancárias, não processa pagamentos e não funciona offline para páginas ou dados financeiros. Veja [Visão geral e requisitos](visao-geral.md) e [Segurança e operação](seguranca-operacao.md) para detalhes.