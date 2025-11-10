"""
Pydantic Models and Schemas

Request/response models for API endpoints and utility functions.
"""

from src.api.models.schemas import (
    BookResponse,
    BookListResponse,
    ChangeResponse,
    ChangeListResponse,
    ErrorResponse,
    PaginationMeta,
    HealthResponse
)

from src.api.models.utils import (
    mongo_doc_to_dict,
    mongo_doc_to_book,
    mongo_docs_to_books,
    mongo_doc_to_change,
    mongo_docs_to_changes,
    create_pagination_meta,
    validate_object_id,
    str_to_object_id
)

__all__ = [
    # Schemas
    "BookResponse",
    "BookListResponse",
    "ChangeResponse",
    "ChangeListResponse",
    "ErrorResponse",
    "PaginationMeta",
    "HealthResponse",
    # Utils
    "mongo_doc_to_dict",
    "mongo_doc_to_book",
    "mongo_docs_to_books",
    "mongo_doc_to_change",
    "mongo_docs_to_changes",
    "create_pagination_meta",
    "validate_object_id",
    "str_to_object_id",
]
