# sapoupei

Aplicação web de educação financeira e controle de receitas e despesas. O projeto foi feito com Python, Flask, SQLAlchemy e MySQL, com duas áreas protegidas: a área pessoal de cada usuário e a área administrativa de análise agregada.

O objetivo é permitir que a pessoa registre sua movimentação financeira, acompanhe um resumo do próprio orçamento e consulte conteúdos educativos. A administração vê indicadores agrupados, sem exportar nomes, e-mails ou movimentações individuais.

## Funcionalidades

### Usuário

- Cadastro com nome, e-mail, senha, faixa etária, cidade opcional e registro de consentimento.
- Login, logout e senha armazenada como hash, nunca como texto puro.
- Painel com receitas, despesas, saldo, histórico recente e gráfico dos últimos seis meses.
- Meta opcional de gastos mensais, com barra de progresso e alerta ao chegar ou ultrapassar o limite.
- Criação, consulta, edição, exclusão e filtro de receitas e despesas.
- Histórico paginado em blocos de 20 movimentações.
- Instalação PWA em navegadores compatíveis; o cache offline contém apenas arquivos estáticos.
- Cada movimentação pertence à conta autenticada. Tentar acessar o registro de outra conta retorna `404`.
- Categorias globais e categorias pessoais para receitas e despesas; categorias pessoais são isoladas por conta.
- Perfil financeiro educativo calculado com as receitas e despesas dos últimos 30 dias.
- Dicas gerais e uma recomendação contextual baseada nos registros da própria conta.

### Administrador

- Acesso restrito a contas com papel `admin`.
- Indicadores de usuários comuns, receita e despesa média, saldo agregado, média mensal de despesas e percentual com saldo positivo.
- Gráficos de distribuição por faixa etária, despesa média por faixa, valor gasto e frequência por categoria, perfis financeiros e evolução mensal.
- Exportação CSV com indicadores e agrupamentos, sem dados pessoais identificáveis.
- Contas com papel `admin` são excluídas dos indicadores populacionais e financeiros.

## Tecnologias

| Tecnologia | Uso no projeto |
| --- | --- |
| Python 3 | Lógica da aplicação |
| Flask | Aplicação web, rotas e templates |
| Flask-SQLAlchemy / SQLAlchemy | Modelos e consultas ao banco |
| Flask-Migrate / Alembic | Migrações versionadas do schema |
| Flask-Login | Sessões e autenticação |
| Flask-WTF / WTForms | Formulários, validação e proteção CSRF |
| PyMySQL | Driver de conexão com MySQL |
| MySQL 8 / Aiven | Persistência dos dados |
| Jinja2, HTML e CSS | Páginas e interface responsiva |
| Chart.js | Gráficos no painel pessoal e administrativo |
| python-dotenv | Leitura da configuração local em `.env` |
| Docker Compose | Aplicação e MySQL local reproduzíveis |

O Chart.js e as fontes visuais são carregados por CDN, então os gráficos e fontes externas precisam de acesso à internet no navegador. A interface tem fontes de fallback.

## Estrutura do projeto

```text
financas-inteligentes/
├── app.py
├── config.py
├── extensions.py
├── forms.py
├── models.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── docs/                       # documentação do sistema
├── certs/
│   └── ca.pem                   # certificado CA do MySQL Aiven
├── migrations/
│   ├── env.py
│   └── versions/                # revisões Alembic versionadas
├── routes/
│   ├── admin.py
│   ├── auth.py
│   └── financeiro.py
├── services/
│   └── financial.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── icons/
│   ├── js/
│   ├── manifest.json
│   └── service-worker.js
├── templates/
│   ├── base.html
│   ├── painel.html
│   ├── admin/
│   │   └── dashboard.html
│   ├── auth/
│   │   ├── cadastro.html
│   │   └── login.html
│   └── financeiro/
│       ├── categoria_form.html
│       ├── dicas.html
│       ├── form.html
│       ├── meta_mensal.html
│       └── movimentacoes.html
```

A documentação para apresentação e manutenção está organizada em [`docs/README.md`](docs/README.md). Para estudar antes da banca, consulte o [Guia de estudos](docs/guia-de-estudos.md); os diagramas consolidados estão em [`docs/diagramas.md`](docs/diagramas.md). O `.venv/` e `__pycache__/` são locais/gerados, ignorados pelo Git e não fazem parte da estrutura versionada.

### Responsabilidade de cada arquivo e pasta

- `app.py`: ponto de entrada. Cria o Flask, registra extensões e rotas, monta o painel pessoal e define os comandos `init-db` e `promote-admin`.
- `config.py`: lê as variáveis de ambiente, monta a URL SQLAlchemy e configura TLS para MySQL quando `DB_SSL_CA` está definido. Sem configuração, os padrões de banco são locais (`localhost`).
- `extensions.py`: cria as instâncias compartilhadas de SQLAlchemy, Flask-Migrate, Flask-Login, Flask-Mail e proteção CSRF.
- `forms.py`: campos e validações de cadastro, login, movimentação, categoria, exclusão e meta mensal.
- `models.py`: tabelas, campos e relacionamentos SQLAlchemy.
- `routes/auth.py`: cadastro, login e logout.
- `routes/financeiro.py`: lista, cria, edita e exclui movimentações; cria categorias pessoais; gerencia a meta mensal e apresenta dicas.
- `routes/admin.py`: autorização de administrador, agregação de métricas e exportação CSV.
- `services/financial.py`: totalização, regras de classificação, textos educativos e histórico mensal.
- `templates/`: HTML Jinja2 dividido entre autenticação, usuário, financeiro e administração. `base.html` contém a estrutura comum e navegação.
- `static/css/style.css`: estilos da interface, estados responsivos e gráficos.
- `static/manifest.json` e `static/service-worker.js`: instalação PWA e cache de assets estáticos, sem armazenar páginas financeiras.
- `static/icons/` e `static/js/`: ícone da marca e interações da interface.
- `migrations/`: histórico versionado do schema gerenciado pelo Alembic.
- `Dockerfile`, `docker-compose.yml` e `.dockerignore`: execução local com Gunicorn/MySQL e exclusão de arquivos privados do build.
- `certs/ca.pem`: certificado público CA baixado do Aiven, usado para validar a conexão TLS.
- `.env.example`: referência das variáveis necessárias. Deve conter apenas exemplos, sem senhas nem chaves reais.
- `.env`: configuração privada local. Está listado em `.gitignore`; nunca compartilhe nem faça commit desse arquivo.
- `.venv/` e `__pycache__/`: arquivos locais/gerados, ignorados pelo Git e não fazem parte da estrutura do projeto.

## Banco de dados

O banco configurado é definido pelas variáveis `DB_*`; o exemplo de produção documentado usa MySQL Aiven e o Docker Compose fornece MySQL local. O schema é criado/evoluído por `flask db upgrade`; `init-db` insere apenas categorias e dicas padrão.

| Tabela | Conteúdo e relação |
| --- | --- |
| `usuarios` | Nome, e-mail único, hash da senha, faixa etária, cidade, consentimento, papel (`user` ou `admin`) e data de cadastro. |
| `categorias` | Categorias globais (`user_id=NULL`) ou pertencentes a uma conta. A combinação de proprietário, nome e tipo é única. |
| `movimentacoes` | Tipo, descrição, valor decimal, data, categoria opcional e `user_id`. Uma conta tem várias movimentações. |
| `dicas` | Conteúdo educativo e estado ativo/inativo. |
| `perfis_financeiros` | Um perfil por usuário, com classificação e data da última atualização. |

A tabela `usuarios` também possui o campo opcional `monthly_limit DECIMAL(12,2)`, configurado individualmente por conta.

O papel administrativo é armazenado em `usuarios.role`; não existe uma tabela separada `administradores`. A relação principal é `usuarios.id` para `movimentacoes.user_id` e `perfis_financeiros.user_id`, além de `categorias.id` para `movimentacoes.category_id`.

### Perfil financeiro

A classificação é uma regra educativa simples sobre os totais acumulados registrados; não é avaliação definitiva nem aconselhamento financeiro:

| Perfil | Regra atual |
| --- | --- |
| Em formação | Ainda não há receita registrada. |
| Gastador | As despesas acumuladas superam as receitas acumuladas. |
| Poupador | Pelo menos 20% das receitas acumuladas permanecem após as despesas. |
| Equilibrado | As despesas chegam a pelo menos 90% das receitas, sem ultrapassá-las. |
| Organizado | As despesas ficam abaixo das receitas, com economia inferior a 20%. |

A classificação é baseada em movimentações com `occurred_on >= hoje - 30 dias`, incluindo a data de corte. É recalculada ao criar, editar ou excluir lançamentos e ao abrir o painel ou as dicas; o painel administrativo aplica a mesma janela.

### Indicadores administrativos

- Receita e despesa médias por usuário: totais acumulados divididos pelo número de contas com papel `user`.
- Despesa média por faixa etária: total acumulado da faixa dividido pelo número de usuários daquela faixa, incluindo quem ainda não registrou despesas.
- Usuários com saldo positivo: percentual de contas com receita maior que zero e maior que as despesas acumuladas.
- Média mensal de despesas: total de despesas dos últimos seis meses dividido por seis.
- Categorias: o gráfico ordena pelo valor gasto; a lista e o CSV também mostram a quantidade de lançamentos.
- Evolução mensal: compara receitas e despesas dos últimos seis meses.

O relatório CSV é agregado de propósito. Ele não inclui cadastro nominal nem descrição de transação individual.

## Rotas

| Caminho | Método | Função |
| --- | --- | --- |
| `/` | GET | Direciona para o painel ou login. |
| `/cadastro` | GET, POST | Criar conta. |
| `/login` | GET, POST | Entrar; admins são encaminhados ao admin. |
| `/logout` | POST | Encerrar sessão, com CSRF. |
| `/painel` | GET | Resumo privado, gráfico, perfil e histórico recente. |
| `/meta-mensal` | GET, POST | Definir, atualizar ou remover o limite mensal da conta autenticada. |
| `/categorias/nova` | GET, POST | Criar categoria pessoal vinculada à conta autenticada. |
| `/movimentacoes` | GET | Histórico próprio, com filtro por tipo e 20 itens por página. |
| `/movimentacoes/nova?tipo=receita` | GET, POST | Registrar receita; use `tipo=despesa` para uma despesa. |
| `/movimentacoes/<id>/editar` | GET, POST | Editar um lançamento pertencente à conta atual. |
| `/movimentacoes/<id>/excluir` | POST | Excluir lançamento próprio, com CSRF. |
| `/dicas` | GET | Dicas gerais e sugestão contextual para a conta atual. |
| `/admin/` | GET | Painel administrativo protegido. |
| `/admin/relatorio.csv` | GET | Baixar relatório agregado, apenas para admin. |
| `/teste-banco` | GET | Executar `SELECT 1` para verificar a conexão. |

## Instalação e execução no Windows

Abra o PowerShell na pasta do projeto.

### 1. Criar e ativar o ambiente

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Prompt de Comando, a ativação é:

```bat
.venv\Scripts\activate.bat
```

### 2. Instalar dependências

```powershell
python -m pip install -r requirements.txt
```

### 3. Configurar o MySQL Aiven

Crie ou confirme o arquivo `.env` na raiz, no mesmo nível de `app.py`. Configure nele as variáveis abaixo usando os dados atuais mostrados no painel Aiven. Não coloque a senha real em documentação ou no `.env.example`.

```dotenv
SECRET_KEY=uma-chave-secreta-local
DB_HOST=host-do-seu-mysql.aivencloud.com
DB_PORT=27502
DB_USER=avnadmin
DB_PASSWORD=sua-senha-atual-do-aiven
DB_NAME=defaultdb
DB_SSL_CA=certs/ca.pem
```

Baixe o certificado CA do serviço Aiven e salve em `certs/ca.pem`. O arquivo CA é usado na validação TLS; não desative SSL para contornar erro de conexão. Se a senha ou a chave tiverem sido expostas, troque-as no Aiven e atualize somente o `.env` local.

### 4. Migrar o banco e inserir conteúdo inicial

```powershell
python -m flask --app app db upgrade
python -m flask --app app init-db
```

`db upgrade` aplica as revisões em `migrations/`; `init-db` insere apenas categorias e dicas padrão ausentes e pode ser repetido sem apagar dados.

Para um banco legado que já possui as tabelas do app e ainda não usa Flask-Migrate, faça backup e marque o schema atual como linha de base antes de aplicar a revisão seguinte:

```powershell
python -m flask --app app db stamp 0001_legacy_schema
python -m flask --app app db upgrade
```

Essa sequência é para bancos que já têm as tabelas-base. A revisão seguinte verifica colunas e constraints existentes, preserva categorias antigas como globais e adiciona `monthly_limit`/proprietário de categoria quando necessário. Faça backup antes de migrar um banco real.

Para criar uma revisão depois de mudar os modelos:

```powershell
python -m flask --app app db migrate -m "descrever a mudança"
python -m flask --app app db upgrade
```

### 5. Iniciar e abrir localmente

```powershell
python -m flask --app app run --debug
```

Abra [http://127.0.0.1:5000/](http://127.0.0.1:5000/). Crie uma conta ou entre. O servidor Flask em modo `--debug` é apenas para desenvolvimento local; não o publique como servidor de produção.

### Executar com Docker

Com Docker Desktop aberto, na raiz do projeto:

```powershell
docker compose up --build
```

O Compose inicia um MySQL local persistente, espera o banco ficar saudável, aplica migrações e dados iniciais e sobe o Gunicorn em [http://127.0.0.1:8000/](http://127.0.0.1:8000/). As configurações SMTP são opcionais para executar o app, mas necessárias para envio de e-mail. Os valores padrão do Compose são apenas para desenvolvimento local.

O PWA pode ser instalado em dispositivos/navegadores compatíveis quando acessado por HTTPS ou por `localhost`. O service worker mantém apenas assets estáticos em cache; páginas com dados da conta continuam dependendo de rede.

## Criar acesso administrativo

1. Crie uma conta normalmente pela página `/cadastro`.
2. No terminal, na raiz do projeto, promova apenas o e-mail autorizado:

   ```powershell
   python -m flask --app app promote-admin seu-email@exemplo.com
   ```

3. Saia e entre novamente. A conta será encaminhada para `/admin/` e verá o link “Administração”.

Esse comando não cria senhas nem recebe credenciais; ele altera o papel de uma conta já cadastrada no banco. O formulário público não permite que uma pessoa se torne administradora.

## Uso básico

1. Entre na conta em `/login`.
2. No painel, use `＋ Receita` ou `＋ Despesa` para registrar valor, data, descrição e categoria.
3. Na tela de movimentação, use “Criar uma categoria pessoal” quando precisar de uma categoria própria.
4. Acesse “Movimentações” para filtrar, editar ou excluir seus lançamentos.
5. Consulte “Dicas” para ler o conteúdo educativo e a recomendação baseada nos próprios totais.
6. Se for admin, acesse “Administração” para consultar os gráficos e baixar o CSV.

## Privacidade e segurança

- Senhas são armazenadas com hash do Werkzeug.
- Formulários POST usam proteção CSRF.
- Consultas de movimentação exigem login e filtram pelo identificador da conta autenticada.
- A autorização administrativa é verificada no servidor, não apenas escondida na interface.
- Relatórios administrativos excluem contas admin e não exportam nomes, e-mails ou transações individuais.
- `.env` e ambientes virtuais estão no `.gitignore`; confirme isso antes de publicar o repositório.
- Use consentimento e colete apenas dados necessários. O consentimento atual é um registro básico e não substitui uma política de privacidade ou revisão jurídica para uso real.

## Limitações atuais

- O modo offline do PWA cobre apenas assets estáticos; operações e dados financeiros exigem conexão.
- Usuários podem criar categorias pessoais; a edição e exclusão de categorias ainda não foram implementadas.
- Dicas são semeadas pelo comando `init-db`; ainda não existe interface administrativa para editá-las.
- A exportação é CSV agregado, não há arquivo Excel nem exportação de uma lista nominal de contas.
- O perfil financeiro usa uma janela móvel de 30 dias e regras simples, apenas para educação.
- O papel admin fica na tabela `usuarios`; não há tabela `administradores` independente.
- Não há ainda uma suíte de testes automatizados versionada em `tests/`; os fluxos devem ser testados ao evoluir o projeto.

## Diagnóstico rápido

- Erro de conexão menciona `localhost`: confira se `.env` está salvo na raiz e se `DB_HOST` não está sendo sobrescrito por uma variável do sistema.
- Erro `Table ... doesn't exist`: execute `python -m flask --app app db upgrade` e depois `python -m flask --app app init-db` no diretório do projeto. Em banco legado, siga antes o procedimento de `stamp` descrito acima.
- `/painel` redireciona ao login: esse comportamento é esperado sem sessão. Entre ou crie uma conta primeiro.
- Admin recebe `403`: confirme o papel com `promote-admin`, depois saia e entre novamente.
- `/dicas` está vazio: execute `init-db` para inserir o conteúdo educativo inicial.
- Gráficos vazios: verifique se existem movimentações e se o navegador consegue carregar Chart.js pela CDN.