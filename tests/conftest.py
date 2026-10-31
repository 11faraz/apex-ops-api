import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"), api_key="test-key", version="9.9.9")
    app.testing = True
    return app.test_client()
