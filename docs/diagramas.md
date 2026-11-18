# Diagramas do sistema

Os diagramas abaixo estão em Mermaid. No VS Code, abra este arquivo e use **Markdown: Open Preview** (`Ctrl+Shift+V`) para visualizar os desenhos renderizados. Também podem ser copiados para ferramentas compatíveis com Mermaid.

## 1. Casos de uso

```mermaid
flowchart LR
    visitante[Visitante]
    usuario[Usuário autenticado]
    admin[Administrador]

    subgraph Sapoupei[ sapoupei ]
        cadastro[Criar conta]
        login[Entrar e sair]
        recuperar[Recuperar senha]
        painel[Consultar painel]
        movimento[Gerenciar movimentações]
        categoria[Criar categoria pessoal]
        meta[Definir meta mensal]
        dicas[Consultar dicas]
        dashboard[Consultar indicadores agregados]
        csv[Exportar CSV agregado]
    end

    visitante --> cadastro
    visitante --> login
    visitante --> recuperar
    usuario --> painel
    usuario --> movimento
    usuario --> categoria
    usuario --> meta
    usuario --> dicas
    admin --> painel
    admin --> movimento
    admin --> dashboard
    admin --> csv
```

## 2. Arquitetura lógica

```mermaid
flowchart TB
    browser[Navegador / PWA]
    templates[Templates Jinja]
    assets[CSS, JavaScript, ícone e service worker]
    app[Flask application factory]

    subgraph web[Camada web]
        auth[Blueprint de autenticação]
        finance[Blueprint financeiro]
        admin[Blueprint administrativo]
    end

    forms[Flask-WTF / validação / CSRF]
    services[Serviços de autenticação e regras financeiras]
    models[Modelos ORM]
    orm[Flask-SQLAlchemy / SQLAlchemy]
    database[(MySQL)]
    smtp[SMTP para redefinição de senha]

    browser -->|HTTP e sessão| app
    app --> web
    app --> templates
    templates --> browser
    browser --> assets
    auth --> forms
    finance --> forms
    auth --> services
    finance --> services
    admin --> services
    auth --> models
    finance --> models
    admin --> models
    services --> models
    models --> orm
    orm --> database
    auth --> smtp
```

## 3. Modelo entidade-relacionamento

```mermaid
erDiagram
    USUARIOS ||--o{ MOVIMENTACOES : registra
    USUARIOS ||--o{ CATEGORIAS : possui
    USUARIOS ||--o| PERFIS_FINANCEIROS : possui
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
        int user_id FK "NULL para categoria global"
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

## 4. Diagrama de classes do domínio

```mermaid
classDiagram
    class User {
        +id: int
        +full_name: str
        +email: str
        +password_hash: str
        +role: str
        +monthly_limit: Decimal
        +set_password(password)
        +check_password(password) bool
    }
    class Movement {
        +id: int
        +user_id: int
        +category_id: int
        +kind: str
        +amount: Decimal
        +description: str
        +occurred_on: date
    }
    class Category {
        +id: int
        +user_id: int
        +name: str
        +kind: str
    }
    class FinancialProfile {
        +id: int
        +user_id: int
        +profile_type: str
        +updated_at: datetime
    }
    class Tip {
        +id: int
        +title: str
        +content: str
        +is_active: bool
    }

    User "1" --> "0..*" Movement : registra
    User "1" --> "0..*" Category : possui categorias pessoais
    Category "0..1" --> "0..*" Movement : classifica
    User "1" --> "0..1" FinancialProfile : possui perfil
```

## 5. Sequência de recuperação de senha

```mermaid
sequenceDiagram
    actor Pessoa
    participant Web as Flask / auth blueprint
    participant Token as Serviço de token
    participant DB as MySQL
    participant SMTP as Serviço de e-mail

    Pessoa->>Web: Envia e-mail cadastrado
    Web->>DB: Busca conta
    alt conta encontrada
        Web->>Token: Assina e-mail com validade de 1 hora
        Token-->>Web: Token assinado
        Web->>SMTP: Envia link de redefinição
    else conta não encontrada
        Web->>Web: Não envia mensagem
    end
    Web-->>Pessoa: Resposta genérica nos dois casos
    Pessoa->>Web: Abre link e informa nova senha
    Web->>Token: Valida assinatura e expiração
    Token-->>Web: E-mail confirmado ou token inválido
    Web->>DB: Persiste hash da nova senha
    Web-->>Pessoa: Confirma sucesso ou link inválido/expirado
```

## 6. Implantação local

```mermaid
flowchart LR
    user[Pessoa desenvolvedora]
    compose[Docker Compose]
    app[Container Flask + Gunicorn]
    db[(Container MySQL 8.4)]
    volume[(Volume mysql_data)]
    smtp[SMTP externo opcional]

    user -->|localhost:8000| app
    compose --> app
    compose --> db
    app -->|db upgrade e consultas| db
    db --> volume
    app -. recuperação de senha .-> smtp
```

No modo local sem Docker, o Flask roda no ambiente Python e usa o banco definido pelas variáveis `DB_*`. Em ambos os modos, o envio SMTP só funciona quando `MAIL_*` está configurado.