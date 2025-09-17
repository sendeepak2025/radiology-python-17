import requests

# Check what endpoints are available
try:
    # Get OpenAPI spec
    r = requests.get('http://localhost:8000/openapi.json')
    if r.status_code == 200:
        openapi = r.json()
        paths = openapi.get('paths', {})
        
        print("Available endpoints:")
        for path in sorted(paths.keys()):
            methods = list(paths[path].keys())
            print(f"  {path} → {methods}")
        
        # Check specifically for upload endpoints
        upload_endpoints = [p for p in paths.keys() if 'upload' in p]
        print(f"\nUpload endpoints found: {upload_endpoints}")
        
    else:
        print(f"Failed to get OpenAPI spec: {r.status_code}")

except Exception as e:
    print(f"Error: {e}")