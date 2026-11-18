# Segurança e operação

## Controles implementados

| Área | Controle atual |
| --- | --- |
| Senhas | `User.set_password` armazena hash do Werkzeug; a aplicação não persiste senha em texto puro |
| Sessão | Flask-Login mantém autenticação e carrega usuário por ID |
| Autorização | Rotas privadas usam `login_required`; rotas admin verificam `current_user.role` no servidor |
| Isolamento | Busca/edição/exclusão de movimentação combinam ID do registro e ID do usuário autenticado |
| CSRF | Flask-WTF/CSRFProtect protege formulários POST |
| Recuperação | Token assinado com `SECRET_KEY`, salt específico e expiração de 3.600 segundos; mensagem da solicitação é genérica |
| Validação | WTForms valida e-mail, tamanho, igualdade de senha, valor mínimo e campos obrigatórios |
| Banco | SQLAlchemy parametriza consultas; chaves e restrições protegem relações e unicidade |
| Relatório | CSV contém grupos e métricas agregadas, sem identificadores pessoais nem transações individuais |
| PWA | Service worker guarda somente assets estáticos, não páginas autenticadas nem dados financeiros |
| Segredos | `.env` é ignorado pelo Git e `.dockerignore` impede inclusão no build Docker |

## Pontos de atenção para produção

1. Substituir `SECRET_KEY` de desenvolvimento por valor aleatório forte e mantê-lo em secret manager/variável protegida. O padrão do código é apenas para desenvolvimento.
2. Não publicar o servidor Flask com `--debug`. Usar Gunicorn ou servidor WSGI equivalente atrás de HTTPS e proxy/reverse proxy configurado.
3. Configurar `MAIL_*` com credencial SMTP específica e remetente autorizado. Não versionar senha SMTP nem arquivo `.env`.
4. Manter MySQL acessível apenas por rede autorizada, com usuário de privilégios mínimos e TLS validado pelo certificado CA.
5. Fazer backup antes de migração. Migrações alteram estrutura, não substituem estratégia de backup/restauração.
6. Usar HTTPS para instalar o PWA fora de `localhost`.
7. Configurar retenção, acesso e exclusão de dados de acordo com a política de privacidade do produto. O campo de consentimento não substitui política ou avaliação jurídica.

## Limitações de segurança conhecidas

- Não há rate limiting documentado em login ou solicitação de recuperação de senha.
- O token de recuperação pode ser usado enquanto não expirar; não há registro de uso único/revogação por token.
- A aplicação registra no log uma exceção SMTP se o envio falhar. Logs de produção devem ter acesso e retenção controlados.
- Não há configuração de produção versionada para cookies seguros, HSTS, CSP ou demais cabeçalhos; isso deve ser definido na implantação HTTPS.
- O comando `promote-admin` depende de acesso administrativo ao ambiente e banco; proteja as credenciais do host.
- Não existe suíte de testes automatizados versionada em `tests/` neste momento.

## Configuração

Copie `.env.example` para `.env` e substitua placeholders localmente. Nunca cole o conteúdo do `.env` em documentação, chamados ou mensagens.

| Variável | Uso |
| --- | --- |
| `SECRET_KEY` | Assinatura de sessão e token |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Conexão MySQL |
| `DB_SSL_CA` | Caminho para certificado CA TLS, quando necessário |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` | Endpoint SMTP |
| `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | Credenciais e remetente SMTP |

O Compose usa MySQL local próprio e valores padrão explicitamente destinados a desenvolvimento. Não reutilize as senhas padrão do Compose em produção. Para produção, forneça variáveis secretas e altere as definições de rede, TLS e servidor conforme o ambiente.

## Instalação local no Windows

Na pasta do projeto, no PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` com seus dados privados. Para banco novo, aplique schema e conteúdo inicial:

```powershell
python -m flask --app app db upgrade
python -m flask --app app init-db
python -m flask --app app run --debug
```

Para executar com Docker Desktop na raiz do projeto:

```powershell
docker compose up --build
```

O app local em Docker fica em `http://127.0.0.1:8000/`. Os dados MySQL ficam no volume `mysql_data`. Para parar os serviços sem apagar o volume, use `Ctrl+C` ou `docker compose down`. A remoção do volume apaga o banco local e deve ser intencional.

## Migração de banco legado

Se as tabelas-base já existem antes do Alembic, faça backup e confirme o schema antes de marcar revisão:

```powershell
python -m flask --app app db stamp 0001_legacy_schema
python -m flask --app app db upgrade
```

Não execute `stamp` em banco vazio. Para banco novo, use `db upgrade` sem `stamp`. Para mudanças futuras em modelos:

```powershell
python -m flask --app app db migrate -m "descricao-da-mudanca"
python -m flask --app app db upgrade
```

Revise toda migração autogerada antes de aplicá-la em qualquer banco compartilhado ou de produção. `init-db` adiciona dados padrão ausentes e não altera schema.

## Comandos operacionais

| Comando | Efeito |
| --- | --- |
| `python -m flask --app app db upgrade` | Aplica migrações pendentes |
| `python -m flask --app app db current` | Mostra revisão registrada no banco |
| `python -m flask --app app db history` | Lista revisões disponíveis |
| `python -m flask --app app init-db` | Semeia categorias e dicas padrão ausentes |
| `python -m flask --app app promote-admin email@exemplo.com` | Promove conta existente a admin |
| `python -m flask --app app run --debug` | Servidor de desenvolvimento local, não produção |

## Checklist de testes manuais

1. Criar conta com dados válidos; repetir e-mail e conferir rejeição.
2. Tentar cadastrar com senha menor que 10 caracteres, confirmação diferente e consentimento ausente.
3. Entrar com credencial incorreta e correta; verificar destino de usuário e admin.
4. Criar receita e despesa, filtrar e paginar o histórico, editar e excluir uma movimentação.
5. Como usuário A, tentar abrir URL de movimentação pertencente ao usuário B; resultado esperado: 404.
6. Criar categoria pessoal e validar que ela não aparece para outra conta.
7. Definir, atualizar e remover a meta mensal.
8. Solicitar recuperação para e-mail existente e inexistente; mensagem externa deve ser igual. Verificar link válido, inválido e expirado.
9. Acessar `/admin/` como usuário comum (403) e como admin; validar que CSV não contém PII nem linhas de transações individuais.
10. Rodar `db upgrade` em banco descartável e verificar manifest/service worker em HTTPS ou localhost.

Os testes de integração executados durante o desenvolvimento usaram SQLite em memória; eles não substituem testes na versão/configuração final de MySQL.