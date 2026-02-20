"""Pytest configuration and shared fixtures."""
import os
import sys
import pytest

# Ensure backend package root is importable in tests
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
	sys.path.insert(0, BACKEND_ROOT)

from app.main import create_app


@pytest.fixture
def app():
	"""Create a Flask app in testing mode."""
	flask_app = create_app(config_name='testing')
	return flask_app


@pytest.fixture
def client(app):
	"""Create a Flask test client."""
	return app.test_client()
