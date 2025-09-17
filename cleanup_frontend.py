import os
import shutil

def cleanup_frontend():
    """Clean up frontend directory, keeping only essential files."""
    print("🧹 Cleaning up frontend directory...")
    
    if not os.path.exists('frontend'):
        print("  ℹ️  Frontend directory not found, skipping...")
        return
    
    # Essential files to keep in frontend root
    keep_frontend_files = {
        'package.json',
        'package-lock.json',
        'tsconfig.json',
        '.env',
        '.env.example',
        'README.md'
    }
    
    # Essential directories to keep
    keep_frontend_dirs = {
        'src',
        'public'
    }
    
    # Clean up frontend root
    removed_count = 0
    for item in os.listdir('frontend'):
        if item not in keep_frontend_files and item not in keep_frontend_dirs:
            item_path = os.path.join('frontend', item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"  ❌ Removed frontend file: {item}")
                    removed_count += 1
                elif os.path.isdir(item_path):
                    # Remove large directories that are not essential
                    if item in ['node_modules', 'build', 'dist', '.git']:
                        shutil.rmtree(item_path)
                        print(f"  ❌ Removed frontend directory: {item}")
                        removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not remove frontend/{item}: {e}")
    
    # Clean up src directory - keep only essential files
    src_path = os.path.join('frontend', 'src')
    if os.path.exists(src_path):
        keep_src_files = {
            'App.tsx',
            'index.tsx',
            'index.css',
            'theme.ts',
            'reportWebVitals.ts',
            'setupProxy.js'
        }
        
        keep_src_dirs = {
            'components',
            'services',
            'pages',
            'types',
            'utils',
            'contexts',
            'hooks',
            'theme'
        }
        
        for item in os.listdir(src_path):
            if item not in keep_src_files and item not in keep_src_dirs:
                item_path = os.path.join(src_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        print(f"  ❌ Removed src file: {item}")
                        removed_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"  ❌ Removed src directory: {item}")
                        removed_count += 1
                except Exception as e:
                    print(f"  ⚠️  Could not remove src/{item}: {e}")
    
    # Clean up public directory - keep only essential files
    public_path = os.path.join('frontend', 'public')
    if os.path.exists(public_path):
        keep_public_files = {
            'index.html',
            'manifest.json'
        }
        
        for item in os.listdir(public_path):
            if item not in keep_public_files:
                item_path = os.path.join(public_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        print(f"  ❌ Removed public file: {item}")
                        removed_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"  ❌ Removed public directory: {item}")
                        removed_count += 1
                except Exception as e:
                    print(f"  ⚠️  Could not remove public/{item}: {e}")
    
    print(f"✅ Removed {removed_count} items from frontend")

def show_frontend_structure():
    """Show the cleaned frontend structure."""
    print("\n📁 Cleaned Frontend Structure:")
    
    if not os.path.exists('frontend'):
        print("  Frontend directory not found")
        return
    
    def show_dir(path, prefix=""):
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1
            
            if os.path.isdir(item_path):
                print(f"{prefix}{'└── ' if is_last else '├── '}📁 {item}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                show_dir(item_path, new_prefix)
            else:
                print(f"{prefix}{'└── ' if is_last else '├── '}📄 {item}")
    
    print("📁 frontend/")
    show_dir('frontend', "")

def main():
    print("🏥 Frontend Cleanup")
    print("=" * 30)
    
    cleanup_frontend()
    show_frontend_structure()
    
    print("\n🎉 Frontend cleanup completed!")
    print("✅ Kept only essential files for patient management")
    print("✅ Removed node_modules, build, and other large directories")
    print("✅ Frontend is now clean and focused")

if __name__ == "__main__":
    main()