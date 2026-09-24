#!/usr/bin/env python3
"""
Cache Warming Script
Manually trigger cache warming for VeriaGuide application
"""
import os
import sys

import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def warm_cache(
    base_url: str = "http://localhost:8000",
    api_key: str | None = None,
    post_type: str | None = None
):
    """
    Warm the application cache
    
    Args:
        base_url: Base URL of the application
        api_key: Admin API key for authentication
        post_type: Specific post type to warm (optional)
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.getenv("ADMIN_API_KEY")
        if not api_key:
            print("❌ Error: ADMIN_API_KEY not found in environment")
            print("   Set it with: export ADMIN_API_KEY=your_key")
            sys.exit(1)
    
    headers = {"X-API-Key": api_key}
    
    try:
        if post_type:
            # Warm specific post type
            print(f"🔥 Warming cache for post type: {post_type}...")
            url = f"{base_url}/admin/warm-cache/{post_type}"
        else:
            # Warm all caches
            print("🔥 Warming all caches...")
            url = f"{base_url}/admin/warm-cache"
        
        response = requests.post(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ Cache warming completed successfully!")
                
                if "total_items" in data:
                    print(f"   Total items: {data['total_items']}")
                    print(f"   Duration: {data['duration_seconds']}s")
                    print(f"   Warmed caches: {', '.join(data['warmed_caches'])}")
                    
                    if data.get("failed_caches"):
                        print(f"   ⚠️  Failed caches: {len(data['failed_caches'])}")
                        for failed in data['failed_caches']:
                            print(f"      - {failed['type']}: {failed['error']}")
                elif "items_count" in data:
                    print(f"   Items cached: {data['items_count']}")
            else:
                print(f"❌ Cache warming failed: {data.get('error', 'Unknown error')}")
                sys.exit(1)
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your ADMIN_API_KEY")
            sys.exit(1)
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {base_url}")
        print("   Make sure the application is running")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def invalidate_and_rewarm(
    post_type: str,
    base_url: str = "http://localhost:8000",
    api_key: str | None = None
):
    """
    Invalidate and rewarm cache for a specific post type
    
    Args:
        post_type: Post type to invalidate and rewarm
        base_url: Base URL of the application
        api_key: Admin API key for authentication
    """
    if not api_key:
        api_key = os.getenv("ADMIN_API_KEY")
        if not api_key:
            print("❌ Error: ADMIN_API_KEY not found in environment")
            sys.exit(1)
    
    headers = {"X-API-Key": api_key}
    
    try:
        print(f"🔄 Invalidating and rewarming cache for: {post_type}...")
        url = f"{base_url}/admin/invalidate-and-rewarm/{post_type}"
        
        response = requests.post(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ Cache invalidated and rewarmed successfully!")
                print(f"   Invalidated keys: {data.get('invalidated_keys', 0)}")
                print(f"   Items cached: {data.get('items_count', 0)}")
            else:
                print(f"❌ Operation failed: {data.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            print(f"❌ Request failed with status {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def check_status(
    base_url: str = "http://localhost:8000",
    api_key: str | None = None
):
    """Check cache warming status"""
    if not api_key:
        api_key = os.getenv("ADMIN_API_KEY")
        if not api_key:
            print("❌ Error: ADMIN_API_KEY not found in environment")
            sys.exit(1)
    
    headers = {"X-API-Key": api_key}
    
    try:
        print("📊 Checking cache warming status...")
        url = f"{base_url}/admin/cache-warming-status"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Cache Status:")
            print(f"   Total cached items: {data.get('total_cached_items', 0)}")
            
            if data.get("cached_post_types"):
                print("\n   Cached post types:")
                for item in data["cached_post_types"]:
                    print(f"      - {item['type']}: {item['cache_keys']} cache keys")
            
            if data.get("missing_post_types"):
                print("\n   ⚠️  Missing post types:")
                for post_type in data["missing_post_types"]:
                    print(f"      - {post_type}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VeriaGuide Cache Warming Tool")
    parser.add_argument(
        "action",
        choices=["warm", "invalidate", "status"],
        help="Action to perform"
    )
    parser.add_argument(
        "--post-type",
        help="Specific post type to warm/invalidate"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the application (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--api-key",
        help="Admin API key (or set ADMIN_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    if args.action == "warm":
        warm_cache(args.url, args.api_key, args.post_type)
    elif args.action == "invalidate":
        if not args.post_type:
            print("❌ Error: --post-type is required for invalidate action")
            sys.exit(1)
        invalidate_and_rewarm(args.post_type, args.url, args.api_key)
    elif args.action == "status":
        check_status(args.url, args.api_key)
