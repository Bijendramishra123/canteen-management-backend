#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenAPI Specification Generator
Generate OpenAPI JSON file from FastAPI application
"""

import sys
import os
import json

# Add parent directory to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
except ImportError:
    # Agar app folder mein ho toh
    from app.main import app

def generate_openapi():
    try:
        print("🔄 Generating OpenAPI specification...")
        
        # Get OpenAPI spec
        openapi_spec = app.openapi()
        
        # Save to file with pretty formatting
        with open('openapi.json', 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        print("✅ OpenAPI specification generated successfully!")
        print(f"📁 File: openapi.json")
        print(f"📊 Size: {len(json.dumps(openapi_spec))} bytes")
        print(f"📝 Endpoints: {len(openapi_spec.get('paths', {}))}")
        
        # Print first few endpoints for verification
        paths = list(openapi_spec.get('paths', {}).keys())
        if paths:
            print("\n📋 Available endpoints:")
            for path in paths[:5]:
                print(f"   - {path}")
            if len(paths) > 5:
                print(f"   ... and {len(paths) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating OpenAPI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_openapi()
    sys.exit(0 if success else 1)