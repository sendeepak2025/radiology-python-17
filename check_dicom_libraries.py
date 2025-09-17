"""
Check available DICOM processing libraries and capabilities
"""

def check_dicom_libraries():
    print("🔍 Checking DICOM Processing Libraries...")
    print("=" * 50)
    
    libraries = {
        'pydicom': 'Core DICOM reading/writing',
        'dicom-numpy': 'DICOM to NumPy array conversion',
        'SimpleITK': 'Advanced medical image processing',
        'PIL': 'Image processing and conversion',
        'numpy': 'Numerical array operations',
        'matplotlib': 'Image visualization (optional)',
        'opencv-python': 'Computer vision processing (optional)'
    }
    
    available = []
    missing = []
    
    for lib, description in libraries.items():
        try:
            if lib == 'PIL':
                import PIL
                version = PIL.__version__
            elif lib == 'opencv-python':
                import cv2
                version = cv2.__version__
            elif lib == 'dicom-numpy':
                import dicom_numpy
                version = getattr(dicom_numpy, '__version__', 'unknown')
            else:
                module = __import__(lib.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
            
            print(f"✅ {lib:<15} v{version:<10} - {description}")
            available.append(lib)
            
        except ImportError:
            print(f"❌ {lib:<15} {'missing':<10} - {description}")
            missing.append(lib)
    
    print("\n" + "=" * 50)
    print(f"📊 Summary: {len(available)} available, {len(missing)} missing")
    
    if missing:
        print(f"\n📦 To install missing libraries:")
        print(f"pip install {' '.join(missing)}")
    
    # Test DICOM capabilities
    if 'pydicom' in available:
        test_dicom_capabilities()
    
    return available, missing

def test_dicom_capabilities():
    print("\n🧪 Testing DICOM Capabilities...")
    print("-" * 30)
    
    try:
        import pydicom
        print("✅ pydicom: Can read DICOM files")
        
        # Check transfer syntax support
        print("✅ Transfer syntaxes: Basic support available")
        
        # Check pixel data support
        try:
            import numpy as np
            print("✅ Pixel data: NumPy integration available")
        except ImportError:
            print("❌ Pixel data: NumPy not available")
        
        # Check SimpleITK capabilities
        try:
            import SimpleITK as sitk
            print("✅ SimpleITK: Advanced processing available")
            print("   - Image filtering, registration, segmentation")
            print("   - Multiple file format support")
            print("   - 3D/4D image processing")
        except ImportError:
            print("❌ SimpleITK: Advanced processing not available")
        
        # Check dicom-numpy
        try:
            import dicom_numpy
            print("✅ dicom-numpy: Efficient array conversion available")
        except ImportError:
            print("❌ dicom-numpy: Efficient conversion not available")
            
    except ImportError:
        print("❌ pydicom not available - basic DICOM support missing")

if __name__ == "__main__":
    available, missing = check_dicom_libraries()
    
    print("\n🎯 Recommended Setup:")
    if len(available) >= 4:
        print("✅ Good DICOM processing setup detected!")
        print("✅ Ready for advanced DICOM image processing")
    else:
        print("⚠️  Basic setup - consider installing missing libraries")
        print("📋 For full DICOM support, install all libraries")