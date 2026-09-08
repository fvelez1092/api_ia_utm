"""Inicialización de la API Flask."""

import click
from flask import Flask
from flask_cors import CORS

from app.config import DevelopmentConfig, ProductionConfig
from app.extensions import bcrypt_instance, db, jwt, limiter
from app.utils.error_handler import handle_error
from app.utils.response import create_response


def _validate_config(app: Flask) -> None:
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Debe configurar SECRET_KEY.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Debe configurar DEV_DATABASE_URI o PROD_DATABASE_URI.")

    algorithm = app.config.get("JWT_ALGORITHM", "RS256")
    if algorithm.startswith("RS") and not (
        app.config.get("JWT_PRIVATE_KEY") and app.config.get("JWT_PUBLIC_KEY")
    ):
        raise RuntimeError(
            "JWT RS256 requiere JWT_PRIVATE_KEY_PATH y JWT_PUBLIC_KEY_PATH."
        )
    if algorithm.startswith("HS") and not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT simétrico requiere JWT_SECRET_KEY.")


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    environment = __import__("os").environ.get("ENVIRONMENT", "DEV").upper()
    app.config.from_object(
        ProductionConfig if environment == "PROD" else DevelopmentConfig
    )
    if test_config:
        app.config.update(test_config)

    _validate_config(app)
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", []),
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    db.init_app(app)
    jwt.init_app(app)
    bcrypt_instance.init_app(app)
    limiter.init_app(app)
    app.register_error_handler(Exception, handle_error)

    from app.controllers import BLUEPRINTS
    from app.models.token_block_list import TokenBlockList
    from app.models.user import User

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    with app.app_context():
        if app.config.get("AUTO_CREATE_TABLES"):
            db.create_all()

    @app.get("/")
    def health_check():
        return create_response(
            "success",
            data={"service": "api-ia-utm", "status": "healthy"},
            status_code=200,
        )

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, password):
        """Crea el primer usuario administrador."""
        from app.services.user_service import create

        user, reason = create(username=username, password=password, role="admin")
        if user is None:
            raise click.ClickException(reason)
        click.echo(f"Administrador '{username}' creado correctamente.")

    @app.cli.command("promote-user")
    @click.option("--username", prompt=True)
    def promote_user(username):
        """Convierte un usuario existente en administrador."""
        user = db.session.query(User).filter_by(username=username, status=True).first()
        if user is None:
            raise click.ClickException("Usuario no encontrado.")
        user.role = "admin"
        db.session.commit()
        click.echo(f"Usuario '{username}' promovido a administrador.")

    @app.cli.command("reindex-documents")
    def reindex_documents():
        """Reconstruye el índice vectorial usando los PDF existentes."""
        from app.services.document_service import DocumentService

        try:
            result = DocumentService(
                upload_folder=app.config["UPLOAD_FOLDER"]
            ).reindex_all()
        except Exception as error:
            raise click.ClickException(str(error)) from error
        click.echo(
            f"Reindexación completa: {result['documents']} documentos, "
            f"{result['chunks']} fragmentos."
        )

    return app


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return create_response(
        "error",
        message="El token fue revocado. Inicie sesión nuevamente.",
        status_code=401,
    )


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return create_response(
        "error",
        message="El token caducó. Inicie sesión nuevamente.",
        status_code=401,
    )


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return create_response("error", message="Token inválido.", status_code=401)


@jwt.unauthorized_loader
def missing_token_callback(error):
    return create_response(
        "error", message="La solicitud no contiene un token de acceso.", status_code=401
    )


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.token_block_list import TokenBlockList

    return db.session.query(TokenBlockList.id).filter_by(jti=jwt_payload["jti"]).first() is not None


app = create_app()
