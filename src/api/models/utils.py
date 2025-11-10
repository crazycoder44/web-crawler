"""
Model Utilities

Helper functions for working with API models and database documents.
"""

from typing import Dict, Any, List
from bson import ObjectId
from src.api.models.schemas import BookResponse, ChangeResponse, PaginationMeta


def mongo_doc_to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to a JSON-serializable dictionary.
    
    Converts ObjectId to string and handles other MongoDB-specific types.
    
    Args:
        doc: MongoDB document
        
    Returns:
        Dictionary with serializable values
    """
    if doc is None:
        return None
    
    # Convert ObjectId to string
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    
    # Recursively convert nested ObjectIds
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = mongo_doc_to_dict(value)
        elif isinstance(value, list):
            doc[key] = [mongo_doc_to_dict(item) if isinstance(item, dict) else item for item in value]
    
    return doc


def mongo_doc_to_book(doc: Dict[str, Any]) -> BookResponse:
    """
    Convert MongoDB document to BookResponse model.
    
    Args:
        doc: MongoDB document from books collection
        
    Returns:
        BookResponse instance
    """
    # Convert ObjectId to string
    doc_dict = mongo_doc_to_dict(doc.copy())
    return BookResponse(**doc_dict)


def mongo_docs_to_books(docs: List[Dict[str, Any]]) -> List[BookResponse]:
    """
    Convert list of MongoDB documents to list of BookResponse models.
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of BookResponse instances
    """
    return [mongo_doc_to_book(doc) for doc in docs]


def mongo_doc_to_change(doc: Dict[str, Any]) -> ChangeResponse:
    """
    Convert MongoDB document to ChangeResponse model.
    
    Args:
        doc: MongoDB document from changes collection
        
    Returns:
        ChangeResponse instance
    """
    doc_dict = mongo_doc_to_dict(doc.copy())
    return ChangeResponse(**doc_dict)


def mongo_docs_to_changes(docs: List[Dict[str, Any]]) -> List[ChangeResponse]:
    """
    Convert list of MongoDB documents to list of ChangeResponse models.
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of ChangeResponse instances
    """
    return [mongo_doc_to_change(doc) for doc in docs]


def create_pagination_meta(
    total: int,
    page: int,
    page_size: int
) -> PaginationMeta:
    """
    Create pagination metadata from query results.
    
    Args:
        total: Total number of items
        page: Current page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        PaginationMeta instance
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


def validate_object_id(book_id: str) -> bool:
    """
    Validate if a string is a valid MongoDB ObjectId.
    
    Args:
        book_id: String to validate
        
    Returns:
        True if valid ObjectId format, False otherwise
    """
    return ObjectId.is_valid(book_id)


def str_to_object_id(book_id: str) -> ObjectId:
    """
    Convert string to ObjectId with validation.
    
    Args:
        book_id: String representation of ObjectId
        
    Returns:
        ObjectId instance
        
    Raises:
        ValueError: If string is not a valid ObjectId
    """
    if not validate_object_id(book_id):
        raise ValueError(f"Invalid ObjectId format: {book_id}")
    return ObjectId(book_id)
