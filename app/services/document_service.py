# # import os
# import hashlib
# from werkzeug.utils import secure_filename
# from app.services.embedding_service import EmbeddingService
# from app.services.chroma_service import ChromaService
# from app.config import config
# from app.extensions import logger_app


# class DocumentService:
#     def __init__(self):
#         self.pdfs_directory = config.UPLOAD_FOLDER
#         os.makedirs(self.pdfs_directory, exist_ok=True)

#         self.embedding_service = EmbeddingService()
#         self.chroma_service = ChromaService()

#     def _calculate_hash_from_content(self, content: bytes) -> str:
#         return hashlib.md5(content).hexdigest()

#     def save_pdf(self, file):
#         """
#         Guarda PDF si no es duplicado, retorna path o None
#         """
#         filename = secure_filename(file.filename)
#         content = file.read()
#         file_hash = self._calculate_hash_from_content(content)

#         for existing in os.listdir(self.pdfs_directory):
#             existing_path = os.path.join(self.pdfs_directory, existing)
#             with open(existing_path, "rb") as f:
#                 existing_hash = hashlib.md5(f.read()).hexdigest()
#             if file_hash == existing_hash:
#                 logger_app.info(f"Documento duplicado detectado: {filename}")
#                 return None

#         file_path = os.path.join(self.pdfs_directory, filename)
#         with open(file_path, "wb") as f:
#             f.write(content)

#         logger_app.info(f"Documento guardado: {file_path}")
#         return file_path

#     def upload_and_vectorize(self, file):
#         try:
#             saved_path = self.save_pdf(file)
#             if saved_path is None:
#                 return {"status": "duplicate", "message": "El documento ya existe"}

#             # Generamos chunks (textos) y metadatos
#             chunks, metadatas = self.embedding_service.generate_embeddings(saved_path)

#             # Añadimos los textos a Chroma (él calcula embeddings automáticamente)
#             self.chroma_service.add_embeddings(chunks, metadatas)

#             return {
#                 "status": "success",
#                 "message": "Documento subido y vectorizado correctamente",
#                 "file_path": saved_path,
#                 "num_chunks": len(chunks),
#             }

#         except Exception as e:
#             logger_app.error(f"Error en upload_and_vectorize: {str(e)}")
#             return {
#                 "status": "error",
#                 "message": "Ocurrió un error al vectorizar el documento",
#                 "detail": str(e),
#             }

#     def list_documents(self, page=1, per_page=10):
#         files = os.listdir(self.pdfs_directory)
#         files.sort()
#         total = len(files)
#         start = (page - 1) * per_page
#         end = start + per_page
#         return {
#             "page": page,
#             "per_page": per_page,
#             "total": total,
#             "documents": files[start:end],
#         }

import os
import hashlib
from werkzeug.utils import secure_filename
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService
from app.config import config
from app.extensions import logger_app


class DocumentService:
    def __init__(self):
        # Crear directorio de almacenamiento de PDFs si no existe
        self.pdfs_directory = config.UPLOAD_FOLDER
        os.makedirs(self.pdfs_directory, exist_ok=True)

        # Inicialización de servicios
        self.embedding_service = EmbeddingService()
        self.chroma_service = ChromaService()

    def _calculate_hash_from_content(self, content: bytes) -> str:
        """
        Calcula el hash SHA256 de un archivo para detectar duplicados.
        """
        return hashlib.sha256(content).hexdigest()

    def save_pdf(self, file, original_filename=None):
        """
        Guarda el archivo PDF si no es duplicado, retorna la ruta del archivo guardado o None si es duplicado.
        """
        filename = original_filename or secure_filename(file.filename)
        content = file.read()
        file_hash = self._calculate_hash_from_content(content)

        # Verificar si el archivo ya existe comparando el hash
        for existing in os.listdir(self.pdfs_directory):
            existing_path = os.path.join(self.pdfs_directory, existing)
            with open(existing_path, "rb") as f:
                existing_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash == existing_hash:
                logger_app.info(f"Documento duplicado detectado: {filename}")
                return None

        # Guardar el archivo si no es duplicado
        file_path = os.path.join(self.pdfs_directory, filename)
        with open(file_path, "wb") as f:
            f.write(content)

        logger_app.info(f"Documento guardado en: {file_path}")
        return file_path

    def upload_and_vectorize(self, file, original_filename=None):
        """
        Sube y vectoriza el documento PDF.
        """
        try:
            # Guardar el archivo y verificar si es duplicado
            saved_path = self.save_pdf(file, original_filename)
            if saved_path is None:
                return {"status": "duplicate", "message": "El documento ya existe"}

            # Generar los embeddings y metadatos
            chunks, metadatas = self.embedding_service.generate_embeddings(saved_path)

            # Añadir embeddings a Chroma
            self.chroma_service.add_embeddings(chunks, metadatas)

            return {
                "status": "success",
                "message": "Documento subido y vectorizado correctamente",
                "file_path": saved_path,
                "num_chunks": len(chunks),
            }

        except Exception as e:
            logger_app.error(f"Error en upload_and_vectorize: {str(e)}")
            return {
                "status": "error",
                "message": "Ocurrió un error al vectorizar el documento",
                "detail": str(e),
            }

    # def list_documents(self, page=1, per_page=10):
    #     """
    #     Lista documentos PDF con paginación.
    #     """
    #     files = os.listdir(self.pdfs_directory)
    #     files.sort()  # Para ordenar alfabéticamente
    #     total = len(files)

    #     # Cálculo de los documentos a mostrar para paginación
    #     start = (page - 1) * per_page
    #     end = start + per_page
    #     documents = files[start:end]

    #     # Retorna un diccionario con la información de la paginación
    #     return {
    #         "page": page,
    #         "per_page": per_page,
    #         "total": total,
    #         "documents": documents,
    #     }

    def list_documents(self, page=1, per_page=10):
        files = sorted(os.listdir(self.pdfs_directory))
        total = len(files)
        start = (page - 1) * per_page
        end = start + per_page
        docs = []
        for fname in files[start:end]:
            fpath = os.path.join(self.pdfs_directory, fname)
            stat = os.stat(fpath)
            docs.append(
                {
                    "filename": fname,
                    "modified_at": stat.st_mtime,  # epoch seconds
                }
            )
        return {"page": page, "per_page": per_page, "total": total, "documents": docs}
