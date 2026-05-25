from functools import lru_cache

from app.services.statement_service import StatementService


@lru_cache
def get_statement_service() -> StatementService:
    return StatementService()
