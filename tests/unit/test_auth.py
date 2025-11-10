"""
Unit Tests for Authentication Module

Tests API key hashing, validation, and security dependencies.
"""
import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from src.api.auth.api_key import (
    hash_api_key,
    validate_api_key_hash,
    verify_api_key,
    get_optional_api_key,
    get_api_key_info,
    generate_api_key_hash
)


class TestAPIKeyHashing:
    """Test API key hashing functions."""
    
    def test_hash_api_key_consistency(self):
        """Test that hashing same key produces same hash."""
        key = "test_key_123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
    
    def test_hash_api_key_different_keys(self):
        """Test that different keys produce different hashes."""
        key1 = "test_key_1"
        key2 = "test_key_2"
        
        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)
        
        assert hash1 != hash2
    
    def test_hash_api_key_empty_string(self):
        """Test hashing empty string."""
        key = ""
        hash_result = hash_api_key(key)
        
        assert len(hash_result) == 64
        # Empty string SHA-256 hash
        assert hash_result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    def test_hash_api_key_special_characters(self):
        """Test hashing keys with special characters."""
        key = "test!@#$%^&*()_+-=[]{}|;:',.<>?/"
        hash_result = hash_api_key(key)
        
        assert len(hash_result) == 64
    
    def test_known_hash_value(self):
        """Test against known hash value."""
        key = "test_key"
        expected_hash = "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655"
        
        assert hash_api_key(key) == expected_hash


class TestAPIKeyValidation:
    """Test API key validation."""
    
    @patch('src.api.auth.api_key.settings')
    def test_validate_valid_key(self, mock_settings):
        """Test validating a valid API key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        is_valid, description = validate_api_key_hash("test_key")
        
        assert is_valid is True
        assert description == "test_key"
    
    @patch('src.api.auth.api_key.settings')
    def test_validate_invalid_key(self, mock_settings):
        """Test validating an invalid API key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        is_valid, description = validate_api_key_hash("wrong_key")
        
        assert is_valid is False
        assert description is None
    
    @patch('src.api.auth.api_key.settings')
    def test_validate_multiple_keys(self, mock_settings):
        """Test validation with multiple configured keys."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key",
            "46d74f2e17ca9220713571e83c870725adf4213f952748f827c9804a38864dc3": "admin_key"
        }
        
        # Validate first key
        is_valid1, desc1 = validate_api_key_hash("test_key")
        assert is_valid1 is True
        assert desc1 == "test_key"
        
        # Validate second key
        is_valid2, desc2 = validate_api_key_hash("admin_key")
        assert is_valid2 is True
        assert desc2 == "admin_key"


class TestVerifyAPIKey:
    """Test verify_api_key dependency."""
    
    @pytest.mark.asyncio
    @patch('src.api.auth.api_key.settings')
    @patch('src.api.auth.api_key.log_authentication')
    async def test_verify_valid_key(self, mock_log, mock_settings):
        """Test verifying valid API key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        result = await verify_api_key("test_key")
        
        assert result == "test_key"
        mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.api.auth.api_key.log_authentication')
    async def test_verify_missing_key(self, mock_log):
        """Test verifying with no API key."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('src.api.auth.api_key.settings')
    @patch('src.api.auth.api_key.log_authentication')
    async def test_verify_invalid_key(self, mock_log, mock_settings):
        """Test verifying invalid API key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong_key")
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)


class TestOptionalAPIKey:
    """Test get_optional_api_key dependency."""
    
    @pytest.mark.asyncio
    @patch('src.api.auth.api_key.settings')
    @patch('src.api.auth.api_key.log_authentication')
    async def test_optional_with_valid_key(self, mock_log, mock_settings):
        """Test optional auth with valid key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        result = await get_optional_api_key("test_key")
        
        assert result == "test_key"
    
    @pytest.mark.asyncio
    async def test_optional_without_key(self):
        """Test optional auth without key."""
        result = await get_optional_api_key(None)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('src.api.auth.api_key.settings')
    @patch('src.api.auth.api_key.log_authentication')
    async def test_optional_with_invalid_key(self, mock_log, mock_settings):
        """Test optional auth with invalid key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        result = await get_optional_api_key("wrong_key")
        
        assert result is None


class TestAPIKeyInfo:
    """Test get_api_key_info function."""
    
    @patch('src.api.auth.api_key.settings')
    def test_get_info_valid_key(self, mock_settings):
        """Test getting info for valid key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        info = get_api_key_info("test_key")
        
        assert info["valid"] is True
        assert info["hash"] == "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655"
        assert info["description"] == "test_key"
    
    @patch('src.api.auth.api_key.settings')
    def test_get_info_invalid_key(self, mock_settings):
        """Test getting info for invalid key."""
        mock_settings.parsed_api_keys = {
            "92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655": "test_key"
        }
        
        info = get_api_key_info("wrong_key")
        
        assert info["valid"] is False
        assert info["description"] is None


class TestGenerateAPIKeyHash:
    """Test generate_api_key_hash helper."""
    
    def test_generate_hash_format(self):
        """Test generated hash format."""
        result = generate_api_key_hash("test_key", "Test Key")
        
        assert ":" in result
        hash_part, desc_part = result.split(":", 1)
        
        assert len(hash_part) == 64
        assert desc_part == "Test Key"
    
    def test_generate_hash_consistency(self):
        """Test same key produces same formatted hash."""
        result1 = generate_api_key_hash("test_key", "Test")
        result2 = generate_api_key_hash("test_key", "Test")
        
        assert result1 == result2
    
    def test_generate_hash_different_descriptions(self):
        """Test same key with different descriptions."""
        result1 = generate_api_key_hash("test_key", "Desc 1")
        result2 = generate_api_key_hash("test_key", "Desc 2")
        
        # Hash part should be same
        hash1 = result1.split(":")[0]
        hash2 = result2.split(":")[0]
        assert hash1 == hash2
        
        # Description part should differ
        assert result1 != result2


class TestSecurityProperties:
    """Test security-related properties."""
    
    def test_hash_one_way(self):
        """Test that hash is one-way (can't reverse)."""
        key = "secret_key_123"
        hash_result = hash_api_key(key)
        
        # No way to get original key from hash
        assert key not in hash_result
        assert len(hash_result) == 64
    
    def test_different_keys_no_collision(self):
        """Test that different keys don't produce same hash."""
        keys = [
            "key1", "key2", "key3", "test", "admin", 
            "secret", "password", "token", "api_key"
        ]
        
        hashes = [hash_api_key(k) for k in keys]
        
        # All hashes should be unique
        assert len(hashes) == len(set(hashes))
    
    def test_case_sensitivity(self):
        """Test that hashing is case-sensitive."""
        hash1 = hash_api_key("TestKey")
        hash2 = hash_api_key("testkey")
        hash3 = hash_api_key("TESTKEY")
        
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

