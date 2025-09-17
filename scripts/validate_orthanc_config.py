#!/usr/bin/env python3
"""
Validate Orthanc configuration for Kiro-mini system.
"""

import json
import sys
import os

def validate_orthanc_config(config_path="configs/orthanc.json"):
    """Validate Orthanc configuration file."""
    
    print("=== Orthanc Configuration Validator ===")
    print(f"Validating: {config_path}")
    print()
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"❌ Error: Configuration file not found: {config_path}")
        return False
    
    try:
        # Load and parse JSON
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ JSON syntax is valid")
        
        # Required settings validation
        required_settings = {
            "Name": str,
            "DicomServerEnabled": bool,
            "DicomPort": int,
            "HttpServerEnabled": bool,
            "HttpPort": int,
            "DicomAet": str,
            "StorageDirectory": str,
            "IndexDirectory": str
        }
        
        missing_settings = []
        invalid_types = []
        
        for setting, expected_type in required_settings.items():
            if setting not in config:
                missing_settings.append(setting)
            elif not isinstance(config[setting], expected_type):
                invalid_types.append(f"{setting} (expected {expected_type.__name__}, got {type(config[setting]).__name__})")
        
        if missing_settings:
            print(f"❌ Missing required settings: {', '.join(missing_settings)}")
            return False
        
        if invalid_types:
            print(f"❌ Invalid setting types: {', '.join(invalid_types)}")
            return False
        
        print("✅ All required settings present with correct types")
        
        # Validate specific settings
        if config.get("DicomPort") != 4242:
            print("⚠️  Warning: DICOM port is not 4242 (expected for Kiro-mini)")
        
        if config.get("HttpPort") != 8042:
            print("⚠️  Warning: HTTP port is not 8042 (expected for Kiro-mini)")
        
        if config.get("DicomAet") != "KIRO-MINI":
            print("⚠️  Warning: DICOM AET is not 'KIRO-MINI' (expected for Kiro-mini)")
        
        # Check webhook configuration
        if "Lua" not in config or not config["Lua"]:
            print("❌ Error: No Lua scripts configured for webhook integration")
            return False
        
        lua_script = "\n".join(config["Lua"])
        if "OnStoredInstance" not in lua_script:
            print("❌ Error: OnStoredInstance function not found in Lua scripts")
            return False
        
        if "backend:8000" not in lua_script:
            print("❌ Error: Backend webhook URL not configured in Lua scripts")
            return False
        
        print("✅ Webhook integration properly configured")
        
        # Check DicomWeb configuration
        if "DicomWeb" in config and config["DicomWeb"].get("Enable"):
            print("✅ DicomWeb enabled for image retrieval")
        else:
            print("⚠️  Warning: DicomWeb not enabled (may affect image viewing)")
        
        # Security warnings
        if config.get("RemoteAccessAllowed") and not config.get("AuthenticationEnabled"):
            print("⚠️  Security Warning: Remote access allowed without authentication")
        
        if not config.get("SslEnabled"):
            print("⚠️  Security Warning: SSL not enabled (OK for development)")
        
        print()
        print("✅ Configuration validation completed successfully")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def print_config_summary(config_path="configs/orthanc.json"):
    """Print configuration summary."""
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("\n=== Configuration Summary ===")
        print(f"Name: {config.get('Name', 'N/A')}")
        print(f"DICOM AET: {config.get('DicomAet', 'N/A')}")
        print(f"DICOM Port: {config.get('DicomPort', 'N/A')}")
        print(f"HTTP Port: {config.get('HttpPort', 'N/A')}")
        print(f"Storage Directory: {config.get('StorageDirectory', 'N/A')}")
        print(f"Remote Access: {'Yes' if config.get('RemoteAccessAllowed') else 'No'}")
        print(f"Authentication: {'Yes' if config.get('AuthenticationEnabled') else 'No'}")
        print(f"SSL Enabled: {'Yes' if config.get('SslEnabled') else 'No'}")
        print(f"DicomWeb Enabled: {'Yes' if config.get('DicomWeb', {}).get('Enable') else 'No'}")
        print(f"Webhook Scripts: {len(config.get('Lua', []))} configured")
        
    except Exception as e:
        print(f"Error reading configuration: {e}")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "configs/orthanc.json"
    
    if validate_orthanc_config(config_file):
        print_config_summary(config_file)
        sys.exit(0)
    else:
        print("\n❌ Configuration validation failed")
        sys.exit(1)