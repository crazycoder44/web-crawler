"""
API Key Generator Utility

Generates secure API keys and their hashed versions for storage in .env file.

Usage:
    python scripts/generate_api_key.py
    python scripts/generate_api_key.py --count 5 --length 32
"""

import secrets
import hashlib
import argparse


def generate_api_key(length: int = 32) -> tuple[str, str]:
    """
    Generate a secure API key and its SHA-256 hash.
    
    Args:
        length: Length of the generated key (default: 32)
        
    Returns:
        tuple: (api_key, hashed_key)
    """
    # Generate URL-safe random key
    api_key = secrets.token_urlsafe(length)
    
    # Generate SHA-256 hash
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash


def main():
    """Main function to run the key generator."""
    parser = argparse.ArgumentParser(
        description="Generate secure API keys for Books to Scrape API"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of API keys to generate (default: 1)"
    )
    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Length of each API key (default: 32)"
    )
    parser.add_argument(
        "--client-name",
        type=str,
        default="client",
        help="Client name prefix for key descriptions"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("API Key Generator - Books to Scrape API")
    print("=" * 80)
    print()
    
    keys_for_env = []
    
    for i in range(args.count):
        api_key, key_hash = generate_api_key(args.length)
        client_name = f"{args.client_name}_{i + 1}" if args.count > 1 else args.client_name
        
        print(f"Key #{i + 1}: {client_name}")
        print("-" * 80)
        print(f"API Key (give to client):  {api_key}")
        print(f"Hash (store in .env):      {key_hash}")
        print()
        
        keys_for_env.append(f"{key_hash}:{client_name}")
    
    print("=" * 80)
    print("Add to your .env file:")
    print("=" * 80)
    print(f"API_KEYS={','.join(keys_for_env)}")
    print()
    print("=" * 80)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 80)
    print("1. Give the API Key to the client (they use it in X-API-Key header)")
    print("2. Store only the Hash in your .env file (never the plain key)")
    print("3. Keep the .env file secure and never commit it to version control")
    print("4. Clients should store their API keys securely (environment variables)")
    print("=" * 80)


if __name__ == "__main__":
    main()
