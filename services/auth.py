from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask import current_app


def gerar_token_recuperacao(email: str) -> str:
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="recuperacao-senha")


def verificar_token_recuperacao(token: str, expiracao: int = 3600) -> str | None:
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="recuperacao-senha", max_age=expiracao)
    except (BadSignature, TypeError):
        return None
    return email if isinstance(email, str) else None