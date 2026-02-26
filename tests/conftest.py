import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from litestar_permissions.models import create_models


class Base(DeclarativeBase):
    pass


# Create models once at module level to avoid duplicate table registration
_rbac_models = create_models(Base)


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def rbac_models():
    return _rbac_models
