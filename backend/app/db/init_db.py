from app.db.base import Base
from app.db.session import engine

from app.models.user import User          # noqa: F401
from app.models.api_key import ApiKey     # noqa: F401
from app.models.audit_log import AuditLog # noqa: F401
from app.models.nonce import Nonce        # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)