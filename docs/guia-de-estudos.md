# Guia de estudos para apresentar o sapoupei

Este guia é um material de preparação: explica o sistema em linguagem simples, indica o que estudar no código e prepara respostas para perguntas comuns. Para ver os desenhos, abra [Diagramas do sistema](diagramas.md) no preview Markdown.

## 1. Apresentação em 30 segundos

> O sapoupei é uma aplicação web de educação e organização financeira pessoal. A pessoa cria uma conta, registra receitas e despesas, acompanha totais e uma meta mensal e consulta dicas. O sistema também tem uma área administrativa com indicadores agregados. Foi desenvolvido com Flask, SQLAlchemy e MySQL, com autenticação, proteção CSRF e isolamento das movimentações por usuário. Não acessa contas bancárias nem realiza pagamentos.

## 2. Trilha de estudo

Estude nesta ordem; cada etapa prepara a próxima:

1. **Produto e escopo:** leia [Visão geral e requisitos](visao-geral.md). Saiba dizer qual problema o app resolve e o que não promete.
2. **Demonstração:** percorra login, painel, nova movimentação, histórico, filtros, meta e dicas. Prepare conta de demonstração e valores fictícios.
3. **Arquitetura:** estude [Arquitetura e fluxos](arquitetura.md) e os [diagramas do sistema](diagramas.md). Consiga explicar a viagem de uma requisição, do navegador até o banco e de volta ao template.
4. **Dados:** memorize as cinco tabelas, suas relações e o significado de categoria global/pessoal. Consulte [Banco de dados](banco-de-dados.md).
5. **Código:** use [Referência técnica](referencia-tecnica.md) para localizar rotas, formulários, modelos e serviços.
6. **Segurança:** revise [Segurança e operação](seguranca-operacao.md), sobretudo hash de senha, sessão, CSRF, autorização e isolamento por proprietário.
7. **Limitações:** seja transparente sobre funcionalidades ausentes e o que seria necessário antes de produção.

## 3. O que o produto faz

### Para visitante

- Cria uma conta com nome, e-mail, faixa etária, senha e consentimento.
- Entra, sai e solicita recuperação de senha por e-mail.

### Para usuário autenticado

- Vê o painel com receitas, despesas, saldo, limite mensal, perfil educativo e movimentações recentes.
- Registra, edita, filtra, pagina e exclui as próprias movimentações.
- Usa categorias globais ou cria categoria pessoal.
- Configura ou remove o limite mensal.
- Consulta dicas e uma recomendação calculada a partir dos totais registrados.

### Para administrador

- Acessa o painel administrativo após autenticação e autorização pelo papel `admin`.
- Consulta valores e gráficos agregados.
- Baixa CSV agregado; não há exportação de lista nominal nem de transações individuais.

## 4. Como explicar a arquitetura

Use esta sequência verbal:

1. O navegador envia uma requisição HTTP para o Flask.
2. Um **blueprint** encaminha a requisição para a área responsável: autenticação, finanças ou administração.
3. A rota valida formulários com WTForms/Flask-WTF e verifica sessão/permissão.
4. A rota chama modelos SQLAlchemy e, quando há regra reutilizável, funções de `services/`.
5. SQLAlchemy transforma objetos e consultas em operações no MySQL.
6. Para páginas comuns, Flask/Jinja monta o HTML e devolve a resposta ao navegador.

O app é renderizado no servidor, não é uma SPA nem uma API REST pública. O browser faz requisições HTTP normais e o servidor devolve páginas HTML.

### Conceitos para saber explicar

| Termo | Explicação curta |
| --- | --- |
| Flask | Framework Python que recebe requisições e conecta URLs a funções |
| Blueprint | Agrupamento modular de rotas por área funcional |
| ORM | Mapeia classes Python a tabelas e objetos a registros SQL |
| SQLAlchemy | Biblioteca de persistência e construção de consultas |
| WTForms | Define campos e validações executadas no servidor |
| CSRF | Ataque que tenta induzir uma sessão autenticada a enviar ação indevida; token valida o formulário |
| Flask-Login | Mantém sessão autenticada e fornece o usuário atual à aplicação |
| Alembic/Flask-Migrate | Versiona alterações estruturais do banco e aplica revisões ordenadas |
| Service worker/PWA | Permite instalar o site e cachear recursos; neste app somente arquivos estáticos ficam offline |
| SMTP | Protocolo/serviço usado para enviar o e-mail de redefinição |

## 5. Banco de dados: o que memorizar

| Tabela | Como explicar |
| --- | --- |
| `usuarios` | Conta, hash da senha, papel, consentimento e meta mensal opcional |
| `movimentacoes` | Receita/despesa, valor, descrição, data, dono obrigatório e categoria opcional |
| `categorias` | Tipo/nome; `user_id` nulo indica categoria global, preenchido indica categoria pessoal |
| `perfis_financeiros` | Uma classificação educativa por usuário e instante de atualização |
| `dicas` | Conteúdo educativo geral, sem relação com uma conta específica |

Relações fundamentais: uma conta pode ter várias movimentações e categorias pessoais; uma movimentação pertence a uma conta e pode apontar para uma categoria; cada conta tem no máximo um perfil. O e-mail do usuário e `perfis_financeiros.user_id` são únicos; categorias têm restrição composta de proprietário/nome/tipo.

**Por que usar `DECIMAL`/`Numeric` para dinheiro?** Para representar centavos com precisão decimal. Ponto flutuante binário pode introduzir diferenças de arredondamento.

**Como o banco evolui?** Cada revisão Alembic descreve uma mudança. `flask db upgrade` aplica revisões pendentes. Em banco legado é necessário fazer backup e seguir o procedimento de `stamp` descrito no guia do banco; não se deve aplicar `stamp` a banco vazio.

## 6. Regras financeiras

- Valor de receita/despesa deve ser positivo, com duas casas decimais.
- Totais gerais mostram o acumulado dos registros do usuário.
- Limite mensal compara despesas do primeiro dia do mês até hoje.
- Perfil financeiro considera a janela móvel dos últimos 30 dias, incluindo a data de corte.
- “Em formação”: sem receita; “Gastador”: despesas acima da receita; “Poupador”: sobra igual ou maior que 20% das receitas; “Equilibrado”: despesas de pelo menos 90% da receita, sem ultrapassá-la; os demais casos com receita são “Organizado”.
- A classificação é educativa e não representa diagnóstico nem recomendação profissional.

## 7. Como são calculados os indicadores administrativos

Esta parte costuma gerar perguntas. Diferencie os períodos:

| Indicador | Cálculo implementado |
| --- | --- |
| Total de usuários | Contas com `role = user`; administradores são excluídos |
| Receita/despesa média por usuário | Soma acumulada de cada tipo dividida pelo número de contas comuns |
| Usuários por faixa etária | Contagem de contas comuns agrupada por faixa |
| Despesa média por faixa | Despesas da janela de 30 dias divididas pelo número de usuários da faixa |
| Perfis financeiros | Classificação de cada conta usando receitas/despesas dos últimos 30 dias |
| Percentual com saldo positivo | Contas comuns com receita maior que zero e maior que as despesas na janela de 30 dias |
| Gastos por categoria | Despesas acumuladas agrupadas por categoria; o gráfico mostra até oito grupos de maior valor |
| Frequência por categoria | Quantidade de movimentações nos grupos exibidos no resumo de categorias |
| Evolução mensal | Receitas e despesas dos seis meses recentes |
| Média mensal de despesas | Total dos seis meses apresentados dividido por seis |

O relatório é agregado por grupo e não leva e-mail, nome ou descrição de movimentação.

## 8. Segurança: respostas curtas e corretas

**A senha fica guardada?** Sim, mas como hash do Werkzeug. A aplicação compara a senha digitada ao hash; não precisa recuperar a senha original.

**Como uma conta não acessa a movimentação de outra?** As consultas de edição/exclusão procuram pelo ID da movimentação e pelo ID da conta atual. Se não houver correspondência, respondem 404.

**Como o administrador é protegido?** A rota exige usuário autenticado e verifica `role == "admin"` no servidor. Esconder um link na interface não seria autorização suficiente.

**Como protege POST?** Flask-WTF/CSRFProtect coloca token nos formulários e valida os envios.

**A recuperação confirma se o e-mail existe?** Não na resposta mostrada ao solicitante. Para conta existente, gera token assinado com `SECRET_KEY`, validade de uma hora e envia e-mail.

**O app está pronto para produção?** Não se deve afirmar isso sem ressalvas. Antes são necessários, entre outros itens, segredo forte, HTTPS, configuração de cookies/cabeçalhos, rate limiting, backup/restore testado, monitoramento e suíte automatizada.

Consulte a lista completa em [Segurança e operação](seguranca-operacao.md).

## 9. Tecnologias: que papel cada uma desempenha

- **Python:** linguagem da aplicação e regras de negócio.
- **Flask:** servidor web, roteamento e renderização.
- **Jinja:** templates HTML preenchidos com dados do servidor.
- **Flask-SQLAlchemy/SQLAlchemy:** modelos e consultas ao banco.
- **MySQL/PyMySQL:** armazenamento persistente e driver.
- **Flask-Login:** sessão e usuário autenticado.
- **Flask-WTF/WTForms:** campos, validação e CSRF.
- **Flask-Migrate/Alembic:** histórico de schema.
- **Flask-Mail/itsdangerous:** e-mail e tokens assinados de recuperação.
- **Chart.js:** gráficos do painel administrativo.
- **Docker Compose/Gunicorn:** ambiente local reprodutível e servidor WSGI no container.

## 10. Limitações para declarar sem constrangimento

- Não existe integração bancária, importação automática, pagamento ou transferência.
- O perfil financeiro é baseado em regras simples e não é aconselhamento.
- PWA não mantém páginas ou dados privados offline.
- Categorias não podem ser editadas ou removidas pela interface; dicas não têm painel administrativo de edição.
- Não há suíte de testes automatizados versionada em `tests/`.
- O serviço depende de MySQL e de internet para operações; envio de recuperação depende de SMTP configurado.
- Não há rate limiting documentado para login/recuperação; tokens não têm revogação individual antes de expirar.

Apresente limitações como decisões/próximos passos, não como funcionalidades existentes.

## 11. Roteiro de demonstração

Antes da apresentação:

- Prepare uma conta comum e uma conta admin com dados fictícios.
- Confirme banco, SMTP se for demonstrar recuperação e conexão com internet para Chart.js/CDN.
- Abra a aplicação e deixe o preview de [Diagramas do sistema](diagramas.md) preparado.
- Evite mostrar credenciais, `.env`, e-mails pessoais, dados financeiros reais ou Debugger PIN.

Durante a demo:

1. Entre na conta comum e explique os totais do painel.
2. Abra uma movimentação; registre uma receita/despesa fictícia.
3. Mostre o histórico, filtro, paginação e edição.
4. Abra a meta mensal e explique sua comparação com despesas desde o início do mês.
5. Mostre as dicas e ressalte que o perfil é educativo.
6. Entre como admin e explique os agregados sem abrir/mostrar dados identificáveis.
7. Termine com o ERD e a arquitetura.

Não exclua um registro real ao demonstrar o modal; use um item de teste.

## 12. Perguntas que podem fazer

| Pergunta | Resposta sugerida |
| --- | --- |
| Por que separou `routes`, `services`, `models` e `forms`? | Para deixar HTTP, regras reutilizáveis, persistência e validação em responsabilidades distintas. |
| Por que `Category.user_id` pode ser nulo? | O nulo representa uma categoria global; valor preenchido limita a categoria à conta proprietária. |
| Por que a movimentação guarda `user_id` diretamente? | Permite isolar e consultar registros pelo proprietário e manter a relação explícita no banco. |
| Para que existe `FinancialProfile` se o perfil pode ser calculado? | Armazena a classificação e a data de atualização para reaproveitar o resultado; é atualizado após mutações e no máximo uma vez por dia em leitura. |
| O que `init-db` faz? | Insere categorias e dicas padrão ausentes; não cria tabelas. O schema é responsabilidade de Alembic. |
| Como evita exposição de contas na recuperação de senha? | Responde com o mesmo texto para e-mail existente ou não; não revela a consulta. |
| O que seria feito para escalar? | Medir consultas em produção, adicionar índices orientados por métricas, cachear apenas conteúdo seguro, paginar demais listagens e instrumentar latência. |
| Como testar uma alteração do schema? | Gerar/revisar migração, aplicar em banco descartável, verificar upgrade/downgrade possível e fazer backup antes de banco compartilhado. |

## 13. Revisão final antes de apresentar

- [ ] Consigo explicar o objetivo sem ler o documento.
- [ ] Sei desenhar as relações principais entre as cinco tabelas.
- [ ] Sei explicar uma requisição desde o navegador até o MySQL.
- [ ] Sei descrever cadastro/login e recuperação de senha.
- [ ] Sei explicar isolamento de dados e papel admin.
- [ ] Sei diferenciar totais acumulados de indicadores de 30 dias e de seis meses.
- [ ] Sei rodar a demonstração com contas e dados fictícios.
- [ ] Sei dizer pelo menos três limitações reais e próximos passos.
- [ ] Não vou exibir `.env`, credenciais, dados reais ou detalhes privados.