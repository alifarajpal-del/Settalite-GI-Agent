"""
Test Sentinel Hub connection with configured credentials
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.services.sentinelhub_fetcher import SentinelHubFetcher
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sentinelhub_connection():
    """Test Sentinel Hub fetcher initialization and connection."""
    
    print("="*60)
    print("SENTINEL HUB CONNECTION TEST")
    print("="*60)
    
    # Load config
    print("\n[1/3] Loading configuration...")
    config = load_config()
    
    # Check credentials
    sh_config = config.get('sentinelhub', {})
    print(f"   Client ID configured: {'✓' if sh_config.get('client_id') else '✗'}")
    print(f"   Client Secret configured: {'✓' if sh_config.get('client_secret') else '✗'}")
    
    if not sh_config.get('client_id') or not sh_config.get('client_secret'):
        print("\n❌ ERROR: Sentinel Hub credentials not found!")
        print("   Add to .streamlit/secrets.toml:")
        print("   [sentinelhub]")
        print("   client_id = 'your-client-id'")
        print("   client_secret = 'your-client-secret'")
        return False
    
    # Initialize fetcher
    print("\n[2/3] Initializing Sentinel Hub fetcher...")
    fetcher = SentinelHubFetcher(config, logger)
    
    if not fetcher.available:
        print("   ❌ Fetcher not available")
        return False
    
    print("   ✓ Fetcher initialized")
    
    # Test connection
    print("\n[3/3] Testing connection...")
    try:
        connection_ok = fetcher.test_connection()
        if connection_ok:
            print("   ✓ Connection successful!")
            return True
        else:
            print("   ❌ Connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = test_sentinelhub_connection()
        
        print("\n" + "="*60)
        if success:
            print("✓ ALL TESTS PASSED")
            print("\nSentinel Hub is ready to use in Live mode!")
        else:
            print("✗ TESTS FAILED")
            print("\nCheck credentials and try again.")
        print("="*60)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
