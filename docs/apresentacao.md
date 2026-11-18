# Roteiro de apresentação

## Sugestão de apresentação de 5 minutos

### 1. Problema e objetivo — 40 segundos

“O sapoupei foi pensado para ajudar uma pessoa a registrar receitas e despesas e enxergar o próprio orçamento em um único lugar. O sistema combina acompanhamento simples com conteúdo educativo; não acessa bancos nem realiza pagamentos.”

### 2. Funcionalidades — 60 segundos

Mostrar login/cadastro, painel, limite mensal, histórico paginado, filtro, criação/edição/exclusão de movimentação, categorias pessoais e recuperação de senha. Destacar que cada movimentação pertence à conta autenticada.

### 3. Arquitetura — 60 segundos

Apresentar o diagrama de [Arquitetura e fluxos](arquitetura.md): Flask recebe requisições, blueprints coordenam casos de uso, WTForms valida entradas, serviços executam regras financeiras, SQLAlchemy persiste no MySQL e Jinja renderiza a interface.

### 4. Banco de dados — 60 segundos

Mostrar o ERD de [Banco de dados](banco-de-dados.md). Explicar a relação um-para-muitos entre usuários e movimentações, categoria opcional, categoria global versus pessoal e perfil único por usuário. Comentar que Alembic controla alterações de schema.

### 5. Segurança e análise — 60 segundos

Destacar senha armazenada como hash, CSRF, autorização administrativa no servidor, filtro das consultas pelo dono do registro e token de recuperação temporário. A área admin apresenta métricas agregadas e exporta CSV sem dados identificáveis.

### 6. Encerramento — 20 segundos

“O projeto cobre os principais fluxos de organização financeira pessoal e deixa explícitas suas fronteiras atuais: não integra bancos, o perfil é educativo, e a experiência offline se limita aos arquivos estáticos. A arquitetura separa áreas para evoluir o produto com testes e monitoramento.”

## Demonstração ao vivo

1. Entrar com uma conta de demonstração previamente preparada; não exibir credenciais reais.
2. Mostrar o painel e a meta mensal.
3. Registrar uma despesa e uma receita de valores fictícios.
4. Abrir o histórico, aplicar filtro e navegar para a próxima página se houver registros suficientes.
5. Mostrar o diálogo de confirmação sem confirmar uma exclusão importante.
6. Abrir a área administrativa com conta de demonstração admin e mostrar gráficos/CSV agregado.
7. Apresentar o ERD e a sequência de migrações nos documentos.

## Perguntas técnicas possíveis

| Pergunta | Resposta sugerida |
| --- | --- |
| Como impede acesso à movimentação de outra pessoa? | A busca consulta simultaneamente pelo ID do registro e pelo ID do usuário autenticado; se não encontrar, responde 404. |
| Onde ficam as senhas? | Apenas hashes gerados pelo Werkzeug, nunca a senha original. |
| Como o schema evolui? | Revisões Alembic versionadas e aplicadas por `flask db upgrade`, com backup antes de mudanças compartilhadas. |
| O sistema funciona offline? | O service worker guarda assets estáticos; dados e operações precisam de conexão. |
| O perfil é aconselhamento financeiro? | Não. É uma classificação educativa simples baseada em movimentações de uma janela de 30 dias. |
| O que falta para produção? | Testes automatizados, rate limiting, política de segurança/privacidade, configuração de cabeçalhos e infraestrutura de observabilidade/backup. |