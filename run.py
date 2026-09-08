"""Punto de entrada para desarrollo local."""

from app import app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
