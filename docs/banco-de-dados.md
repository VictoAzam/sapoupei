# Banco de dados

## SGBD e mapeamento

O sistema usa SQLAlchemy via Flask-SQLAlchemy. A URL é montada em `config.py` como `mysql+pymysql`; a configuração padrão é MySQL local, e o projeto também documenta MySQL Aiven. O certificado TLS é aplicado quando `DB_SSL_CA` contém um caminho. O Docker Compose fornece um MySQL local independente.

## Diagrama entidade-relacionamento

```mermaid
erDiagram
    USUARIOS ||--o{ MOVIMENTACOES : registra
    USUARIOS ||--o{ CATEGORIAS : possui
    USUARIOS ||--o| PERFIS_FINANCEIROS : classificado_por
    CATEGORIAS o|--o{ MOVIMENTACOES : classifica

    USUARIOS {
        int id PK
        string full_name
        string email UK
        string password_hash
        string age_range
        string city
        decimal monthly_limit
        datetime consent_at
        string role
        datetime created_at
    }
    CATEGORIAS {
        int id PK
        int user_id FK "NULL significa global"
        string name
        string kind
    }
    MOVIMENTACOES {
        int id PK
        int user_id FK
        int category_id FK "opcional"
        string kind
        decimal amount
        string description
        date occurred_on
    }
    PERFIS_FINANCEIROS {
        int id PK
        int user_id FK_UK
        string profile_type
        datetime updated_at
    }
    DICAS {
        int id PK
        string title
        text content
        boolean is_active
    }
```

`DICAS` é independente das demais tabelas: o conteúdo é geral, e não há relação por usuário.

## Dicionário de dados

### `usuarios`

| Campo | Tipo lógico | Nulo? | Regra/uso |
| --- | --- | --- | --- |
| `id` | Integer | Não | Chave primária |
| `full_name` | String(120) | Não | Nome de exibição |
| `email` | String(255) | Não | Único; usado para autenticação |
| `password_hash` | String(255) | Não | Hash gerado pelo Werkzeug, nunca senha em texto puro |
| `age_range` | String(20) | Não | Faixa etária escolhida no cadastro |
| `city` | String(100) | Sim | Cidade opcional |
| `monthly_limit` | Numeric(12,2) | Sim | Limite pessoal de despesas; nulo significa não configurado |
| `consent_at` | DateTime | Não | Data/hora do consentimento registrado |
| `role` | String(20) | Não | Papel; padrão `user`, administrador usa `admin` |
| `created_at` | DateTime | Não | Criado em UTC |

### `categorias`

| Campo | Tipo lógico | Nulo? | Regra/uso |
| --- | --- | --- | --- |
| `id` | Integer | Não | Chave primária |
| `user_id` | Integer/FK | Sim | Referencia `usuarios.id`; nulo para categoria global |
| `name` | String(60) | Não | Nome da categoria |
| `kind` | String(10) | Não | `receita` ou `despesa` |

Há unicidade composta em (`user_id`, `name`, `kind`). A rota de criação também consulta categorias globais para impedir colisões com a categoria da própria conta.

### `movimentacoes`

| Campo | Tipo lógico | Nulo? | Regra/uso |
| --- | --- | --- | --- |
| `id` | Integer | Não | Chave primária |
| `user_id` | Integer/FK | Não | Dono do registro; referencia `usuarios.id` com exclusão em cascata |
| `category_id` | Integer/FK | Sim | Referencia `categorias.id` |
| `kind` | String(10) | Não | `receita` ou `despesa` |
| `amount` | Numeric(12,2) | Não | Valor positivo com precisão decimal |
| `description` | String(160) | Não | Descrição informada pela pessoa |
| `occurred_on` | Date | Não | Data da movimentação; padrão: data atual |

### `perfis_financeiros`

| Campo | Tipo lógico | Nulo? | Regra/uso |
| --- | --- | --- | --- |
| `id` | Integer | Não | Chave primária |
| `user_id` | Integer/FK | Não | Referencia `usuarios.id`; único, um perfil por usuário |
| `profile_type` | String(30) | Não | Classificação educativa |
| `updated_at` | DateTime | Não | Data/hora UTC da última atualização |

### `dicas`

| Campo | Tipo lógico | Nulo? | Regra/uso |
| --- | --- | --- | --- |
| `id` | Integer | Não | Chave primária |
| `title` | String(120) | Não | Título |
| `content` | Text | Não | Texto educativo |
| `is_active` | Boolean | Não | Apenas dicas ativas são apresentadas |

## Restrições, índices e cascatas

- `usuarios.email` é único e indexado.
- `categorias` possui unicidade por proprietário/nome/tipo.
- `perfis_financeiros.user_id` é único.
- `movimentacoes.user_id` referencia a conta e tem `ON DELETE CASCADE`.
- A relação ORM da conta também configura cascata de remoção para movimentações, categorias pessoais e perfil.
- Categorias globais usam `user_id = NULL` e não pertencem a uma conta específica.
- Não há soft delete: uma exclusão confirmada remove o registro.
- Não há índices secundários declarados em `movimentacoes`; se o volume crescer, medir consultas por usuário/data e avaliar índices compostos com uma migração.

## Migrações

As revisões ficam em `migrations/versions/`:

1. `0001_legacy_schema`: schema inicial antes de limite mensal e categorias pessoais.
2. `0002_limits_categories`: adiciona `usuarios.monthly_limit`, `categorias.user_id`, chave estrangeira e unicidade por proprietário. A revisão verifica itens existentes e usa batch alter para compatibilidade com SQLite.

A revisão `0002_limits_categories` não permite downgrade automático: remover a coluna de meta e a propriedade das categorias pode descartar informação. Para reverter uma mudança de negócio, crie uma nova revisão corretiva após backup.

Banco novo: `flask --app app db upgrade`, depois `flask --app app init-db` para semear categorias e dicas. Banco legado com tabelas já existentes: fazer backup, executar `flask --app app db stamp 0001_legacy_schema` e depois `flask --app app db upgrade`. O `stamp` só deve ser usado quando as tabelas base realmente já existem.

`init-db` atualmente semeia dados de referência; não cria nem altera tabelas. Mudanças futuras de schema devem ser revisões Alembic.