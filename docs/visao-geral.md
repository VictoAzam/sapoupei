# Visão geral e requisitos

## Objetivo

O sapoupei oferece um local para registrar receitas e despesas, acompanhar um resumo do orçamento e consultar conteúdo educativo. A área administrativa apresenta tendências agregadas para apoiar a análise do uso do sistema, sem expor nomes, e-mails ou descrições de movimentações no relatório CSV.

## Atores

| Ator | Capacidades |
| --- | --- |
| Visitante | Criar conta, entrar e solicitar redefinição de senha |
| Usuário autenticado | Consultar painel, registrar/editar/excluir movimentações próprias, criar categorias pessoais, definir meta mensal e consultar dicas |
| Administrador | Acessar painel de indicadores e exportar CSV agregado; também pode usar as funções comuns da conta |

A função administrativa é um papel (`role`) armazenado no registro do usuário. O cadastro público cria contas comuns; a promoção é feita por comando administrativo no terminal.

## Requisitos funcionais

| ID | Requisito | Situação na implementação |
| --- | --- | --- |
| RF-01 | Cadastrar conta com nome, e-mail, faixa etária, senha e consentimento | Implementado; e-mail é normalizado para minúsculas e único |
| RF-02 | Autenticar e encerrar sessão | Implementado com Flask-Login; logout via POST com CSRF |
| RF-03 | Recuperar senha por link temporário enviado por e-mail | Implementado; token assinado com validade de 1 hora |
| RF-04 | Criar, consultar, editar e excluir movimentações | Implementado; cada operação filtra pelo usuário autenticado |
| RF-05 | Filtrar movimentações por receita/despesa e paginar resultados | Implementado; 20 registros por página |
| RF-06 | Associar movimentação a categoria global ou pessoal | Implementado; categoria é opcional |
| RF-07 | Definir ou remover limite mensal de despesas | Implementado; limite nulo representa ausência de meta |
| RF-08 | Exibir resumo financeiro, perfil e histórico recente | Implementado no painel do usuário |
| RF-09 | Apresentar dicas educativas e uma recomendação contextual | Implementado |
| RF-10 | Exibir indicadores administrativos e exportar relatório CSV agregado | Implementado; acesso restrito a administradores |
| RF-11 | Instalar o site como PWA em navegadores compatíveis | Implementado; cache offline cobre somente assets estáticos |
| RF-12 | Confirmar exclusão e fornecer feedback visual | Implementado com diálogo, flash e feedback no formulário |

## Regras de negócio

1. Valores de movimentação devem ser positivos e armazenados com duas casas decimais.
2. Cada movimentação pertence a exatamente um usuário e pode ter uma categoria.
3. Uma categoria com `user_id = NULL` é global; uma categoria com `user_id` definido é pessoal.
4. A combinação de proprietário, nome e tipo da categoria é única. A aplicação também impede conflito com categoria global do mesmo tipo.
5. O perfil financeiro usa os totais de receita e despesa dos últimos 30 dias, incluindo a data de corte.
6. Classificação: sem receita é “Em formação”; despesa acima da receita é “Gastador”; economia de pelo menos 20% é “Poupador”; despesa de pelo menos 90% da receita, sem ultrapassá-la, é “Equilibrado”; demais casos positivos são “Organizado”.
7. Uma conta administrativa não entra nos cálculos populacionais do relatório.
8. A mensagem de solicitação de recuperação de senha é genérica para não confirmar se um e-mail está cadastrado.

## Requisitos não funcionais e qualidade

- **Segurança:** hash de senha, sessão autenticada, proteção CSRF, autorização no servidor e isolamento dos registros por usuário.
- **Privacidade:** exportação administrativa agregada, sem nomes, e-mails ou transações individuais.
- **Integridade:** chaves estrangeiras, restrições únicas e migrações versionadas.
- **Usabilidade:** formulários com validação, filtros, paginação e confirmações para exclusão.
- **Portabilidade:** execução local em ambiente Python ou via Docker Compose.
- **Disponibilidade offline:** limitada a assets estáticos; consultas e ações financeiras exigem conexão.
- **Manutenibilidade:** separação entre rotas, formulários, modelos, serviços e migrações.

## Fora do escopo atual

- Open banking, importação automática de extratos ou integração com instituições financeiras.
- Pagamentos, transferências e aconselhamento financeiro profissional.
- Edição/exclusão de categorias pela interface.
- Administração de dicas pela interface.
- Aplicativo nativo e operações financeiras offline.
- Suíte automatizada versionada em `tests/`.