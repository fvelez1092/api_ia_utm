# API IA UTM

API Flask para cargar documentos PDF, indexarlos en ChromaDB y responder preguntas mediante un modelo local de Ollama.

## Requisitos

- Python 3.11
- PostgreSQL
- Ollama
- Pipenv

## Preparación local

```bash
cp .env.example .env
./scripts/generate_jwt_keys.sh
pipenv sync
```

Edite `.env` y configure, como mínimo, `SECRET_KEY`, `DEV_DATABASE_URI`, los modelos de Ollama y los orígenes permitidos por CORS.

Los ajustes de velocidad y calidad del RAG están explicados en [`docs/RAG_CONFIGURATION.md`](docs/RAG_CONFIGURATION.md).

Descargue los modelos configurados:

```bash
ollama pull nomic-embed-text
ollama pull deepseek-r1:8b
```

Para una base nueva, `AUTO_CREATE_TABLES=true` crea las tablas durante el desarrollo. Para una base existente ejecute primero:

```bash
psql "postgresql://USUARIO:CLAVE@HOST:5432/BASE" -f migrations/manual/001_add_roles_and_constraints.sql
```

Cree el primer administrador:

```bash
pipenv run flask --app app create-admin
```

Si ya existe un usuario que debe convertirse en administrador:

```bash
pipenv run flask --app app promote-user --username NOMBRE
```

Inicie la API:

```bash
pipenv run python run.py
```

El servicio estará disponible en `http://localhost:5000`.

## Pruebas automatizadas

Las pruebas usan SQLite, claves JWT temporales y servicios simulados; no modifican PostgreSQL ni ChromaDB:

```bash
pipenv run python -m unittest discover -s tests -v
```

## Pruebas con Postman

Importe estos dos archivos:

- `postman/API_IA_UTM.postman_collection.json`
- `postman/API_IA_UTM.postman_environment.json`

Seleccione el entorno **API IA UTM - Local**, cambie `admin_password` y ejecute las solicitudes en orden. En la solicitud **06 - Subir PDF como administrador** debe seleccionar manualmente un PDF. Los scripts guardan automáticamente los tokens JWT.

## Rutas

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/` | Público |
| POST | `/auth/login` | Público, limitado |
| DELETE | `/auth/logout` | Autenticado |
| GET/POST/PUT/DELETE | `/user/*` | Administrador |
| POST | `/document/` | Administrador, limitado |
| GET | `/document/` | Autenticado |
| GET | `/document/view?name=archivo.pdf` | Autenticado |
| POST | `/rag/ask` | Autenticado, limitado |

## Seguridad

- Las claves JWT deben almacenarse fuera del repositorio y configurarse mediante `JWT_PRIVATE_KEY_PATH` y `JWT_PUBLIC_KEY_PATH`.
- Los PDF cargados y la base Chroma están excluidos de Git.
- En producción use un almacenamiento compartido para los límites, por ejemplo Redis mediante `RATELIMIT_STORAGE_URI`.
- Las claves que estuvieron versionadas deben revocarse. Retirarlas del último commit no las elimina del historial; la limpieza del historial debe coordinarse antes de forzar cambios sobre el repositorio remoto.

## Producción

Configure `ENVIRONMENT=PROD`, `PROD_DATABASE_URI`, `AUTO_CREATE_TABLES=false`, claves nuevas y CORS restringido. Ejemplo de ejecución:

```bash
pipenv run gunicorn --workers 2 --bind 0.0.0.0:5000 "app:app"
```
