import io
import os
import tempfile
import unittest
from pathlib import Path


TEST_ROOT = tempfile.mkdtemp(prefix="api-ia-utm-tests-")
os.environ.update(
    {
        "ENVIRONMENT": "DEV",
        "DEV_DATABASE_URI": f"sqlite:///{TEST_ROOT}/test.db",
        "SECRET_KEY": "test-secret",
        "JWT_SECRET_KEY": "test-jwt-secret-with-at-least-32-bytes",
        "JWT_ALGORITHM": "HS256",
        "UPLOAD_FOLDER": f"{TEST_ROOT}/uploads",
        "CHROMA_PATH": f"{TEST_ROOT}/chroma",
        "AUTO_CREATE_TABLES": "true",
        "RATELIMIT_ENABLED": "false",
    }
)

from app import app
from app.extensions import db
from app.services import user_service
from app.services.document_service import DocumentService


class FakeDocumentService:
    def list_documents(self, page, per_page):
        return {"page": page, "per_page": per_page, "total": 0, "documents": []}

    def upload_and_vectorize(self, file, filename):
        if not file.read().startswith(b"%PDF-"):
            raise ValueError("El contenido no corresponde a un PDF válido.")
        return {
            "status": "success",
            "filename": filename,
            "num_chunks": 1,
            "document_hash": "abc",
            "message": "ok",
        }

    def resolve_document(self, name):
        return None


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        app.extensions["document_service"] = FakeDocumentService()
        with app.app_context():
            db.drop_all()
            db.create_all()
            user_service.create("admin", "Admin123!", "admin")
            user_service.create("usuario", "Usuario123!", "user")
        self.client = app.test_client()
        self.admin_token = self._login("admin", "Admin123!")
        self.user_token = self._login("usuario", "Usuario123!")

    def _login(self, username, password):
        response = self.client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()["data"]["auth"]["access_token"]

    @staticmethod
    def _auth(token):
        return {"Authorization": f"Bearer {token}"}

    def test_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["status"], "healthy")

    def test_documents_require_authentication(self):
        self.assertEqual(self.client.get("/document/").status_code, 401)
        self.assertEqual(
            self.client.get("/document/view?name=test.pdf").status_code, 401
        )
        self.assertEqual(
            self.client.post("/rag/ask", json={"question": "hola"}).status_code,
            401,
        )

    def test_regular_user_cannot_manage_users(self):
        response = self.client.post(
            "/user/",
            json={"username": "nuevo", "password": "Nuevo123!", "role": "user"},
            headers=self._auth(self.user_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_user_and_duplicates_conflict(self):
        body = {"username": "nuevo", "password": "Nuevo123!", "role": "user"}
        response = self.client.post(
            "/user/", json=body, headers=self._auth(self.admin_token)
        )
        self.assertEqual(response.status_code, 201)
        duplicate = self.client.post(
            "/user/", json=body, headers=self._auth(self.admin_token)
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_invalid_user_payload_returns_422(self):
        response = self.client.post(
            "/user/",
            json={"username": "x", "password": "123"},
            headers=self._auth(self.admin_token),
        )
        self.assertEqual(response.status_code, 422)

    def test_upload_requires_admin_and_valid_pdf(self):
        denied = self.client.post(
            "/document/",
            data={"file": (io.BytesIO(b"%PDF-1.4\n"), "test.pdf")},
            headers=self._auth(self.user_token),
        )
        self.assertEqual(denied.status_code, 403)

        invalid = self.client.post(
            "/document/",
            data={"file": (io.BytesIO(b"not a pdf"), "test.pdf")},
            headers=self._auth(self.admin_token),
        )
        self.assertEqual(invalid.status_code, 400)

        traversal = self.client.get(
            "/document/view?name=../secret.pdf", headers=self._auth(self.user_token)
        )
        self.assertEqual(traversal.status_code, 404)

    def test_rag_validates_boolean_and_handles_greeting(self):
        invalid = self.client.post(
            "/rag/ask",
            json={"question": "consulta", "use_scores": "incorrecto"},
            headers=self._auth(self.user_token),
        )
        self.assertEqual(invalid.status_code, 400)
        greeting = self.client.post(
            "/rag/ask",
            json={"question": "Hola"},
            headers=self._auth(self.user_token),
        )
        self.assertEqual(greeting.status_code, 200)
        self.assertEqual(greeting.get_json()["data"]["sources"], [])

    def test_logout_revokes_token(self):
        response = self.client.delete(
            "/auth/logout", headers=self._auth(self.user_token)
        )
        self.assertEqual(response.status_code, 200)
        revoked = self.client.get(
            "/document/", headers=self._auth(self.user_token)
        )
        self.assertEqual(revoked.status_code, 401)


class FakeEmbeddingService:
    def generate_embeddings(self, path):
        return ["contenido"], [{"page": 1}]


class FakeChromaService:
    def __init__(self, fail=False):
        self.fail = fail
        self.deleted = []
        self.reset_called = False
        self.embedding_function = type(
            "FakeEmbeddingFunction", (), {"embed_query": lambda self, text: [0.1]}
        )()

    def add_embeddings(self, texts, metadatas, ids=None):
        if self.fail:
            raise RuntimeError("chroma unavailable")
        return len(texts)

    def delete_by_document_hash(self, document_hash):
        self.deleted.append(document_hash)

    def reset(self):
        self.reset_called = True


class DocumentServiceTestCase(unittest.TestCase):
    def test_reindexes_existing_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "reglamento.pdf").write_bytes(b"%PDF-existing")
            chroma = FakeChromaService()
            service = DocumentService(directory, FakeEmbeddingService(), chroma)

            result = service.reindex_all()

            self.assertTrue(chroma.reset_called)
            self.assertEqual(result, {"documents": 1, "chunks": 1})

    def test_success_is_atomic_and_renames_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "manual.pdf").write_bytes(b"%PDF-old")
            service = DocumentService(
                directory, FakeEmbeddingService(), FakeChromaService()
            )
            upload = type(
                "Upload", (), {"filename": "manual.pdf", "read": lambda self: b"%PDF-new"}
            )()
            result = service.upload_and_vectorize(upload)
            self.assertRegex(result["filename"], r"manual-[0-9a-f]{8}\.pdf")
            self.assertTrue(Path(directory, result["filename"]).exists())
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_failed_indexing_does_not_leave_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            chroma = FakeChromaService(fail=True)
            service = DocumentService(
                directory, FakeEmbeddingService(), chroma
            )
            upload = type(
                "Upload", (), {"filename": "manual.pdf", "read": lambda self: b"%PDF-new"}
            )()
            with self.assertRaises(RuntimeError):
                service.upload_and_vectorize(upload)
            self.assertEqual(list(Path(directory).iterdir()), [])
            self.assertEqual(len(chroma.deleted), 1)


if __name__ == "__main__":
    unittest.main()
