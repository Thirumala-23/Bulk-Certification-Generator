"""Pytest configuration and test fixtures."""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
import app.database as app_database
from app.main import app
import app.config as config
import app.services.job_processor as job_processor_module
import app.routes.certificates as cert_routes_module


@pytest.fixture(scope="function")
def test_env(tmp_path: Path):
    """
    Sets up an isolated test database and temporary storage directory
    for each test function to guarantee zero side-effects.
    """
    # 1. Setup isolated SQLite test DB
    test_db_path = tmp_path / "test_bulk_certificates.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    Base.metadata.create_all(bind=test_engine)

    # 2. Setup isolated certificates directory
    test_certs_dir = tmp_path / "test_certificates"
    test_certs_dir.mkdir(parents=True, exist_ok=True)

    # 3. Patch app config and processor references
    orig_cert_dir = config.CERTIFICATES_DIR
    orig_base_dir = config.BASE_DIR
    orig_db_factory = app_database.SessionLocal
    orig_processor_dir = job_processor_module.CERTIFICATES_DIR
    orig_processor_base = job_processor_module.BASE_DIR
    orig_cert_routes_base = cert_routes_module.BASE_DIR

    config.CERTIFICATES_DIR = test_certs_dir
    config.BASE_DIR = tmp_path
    app_database.SessionLocal = TestingSessionLocal
    job_processor_module.CERTIFICATES_DIR = test_certs_dir
    job_processor_module.BASE_DIR = tmp_path
    cert_routes_module.BASE_DIR = tmp_path

    # 4. Dependency override for get_db
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "db_factory": TestingSessionLocal,
        "engine": test_engine,
        "certs_dir": test_certs_dir,
        "tmp_path": tmp_path,
    }

    # Teardown
    app.dependency_overrides.clear()
    config.CERTIFICATES_DIR = orig_cert_dir
    config.BASE_DIR = orig_base_dir
    app_database.SessionLocal = orig_db_factory
    job_processor_module.CERTIFICATES_DIR = orig_processor_dir
    job_processor_module.BASE_DIR = orig_processor_base
    cert_routes_module.BASE_DIR = orig_cert_routes_base
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_env) -> TestClient:
    """FastAPI TestClient fixture configured with isolated environment."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session(test_env):
    """Direct database session fixture for inspecting or pre-seeding test data."""
    session = test_env["db_factory"]()
    try:
        yield session
    finally:
        session.close()
