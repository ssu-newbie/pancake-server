"""Uvicorn entry point: python -m uvicorn pancake_server:app."""

from pancake.application import create_app

app = create_app()
