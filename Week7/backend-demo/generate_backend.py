"""
Script to generate backend code from OpenAPI specification
Uses OpenAPI Generator (Swagger Codegen successor)
"""
import subprocess
import os
import sys

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    # Check Node.js
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        print("✅ Node.js installed")
    except:
        print("❌ Node.js not found. Install from: https://nodejs.org/")
        return False
    
    # Check npm
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
        print("✅ npm installed")
    except:
        print("❌ npm not found")
        return False
    
    return True


def install_openapi_generator():
    """Install OpenAPI Generator CLI"""
    print("\n📦 Installing OpenAPI Generator CLI...")
    
    try:
        subprocess.run([
            'npm', 'install', '@openapitools/openapi-generator-cli', '-g'
        ], check=True)
        print("✅ OpenAPI Generator installed")
        return True
    except Exception as e:
        print(f"❌ Failed to install: {e}")
        return False


def generate_server():
    """Generate Flask server from OpenAPI spec"""
    print("\n🚀 Generating backend code from openapi.yaml...")
    
    if not os.path.exists('openapi.yaml'):
        print("❌ openapi.yaml not found!")
        return False
    
    # Generate Python Flask server
    try:
        cmd = [
            'npx', '@openapitools/openapi-generator-cli', 'generate',
            '-i', 'openapi.yaml',
            '-g', 'python-flask',
            '-o', './generated-backend',
            '--additional-properties',
            'packageName=swagger_server,serverPort=5000'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Backend code generated successfully!")
            print("\n📁 Generated files in: ./generated-backend/")
            return True
        else:
            print(f"❌ Generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_next_steps():
    """Show next steps to user"""
    print("\n" + "="*60)
    print("🎉 Code Generation Complete!")
    print("="*60)
    print("\n📋 Next steps:")
    print("\n1. Install generated backend dependencies:")
    print("   cd generated-backend")
    print("   pip install -r requirements.txt")
    print("\n2. Run the generated server:")
    print("   python -m swagger_server")
    print("\n3. Test the API:")
    print("   http://localhost:5000/ui/")
    print("\n4. Integrate with MongoDB:")
    print("   - Edit swagger_server/controllers/")
    print("   - Add MongoDB connection")
    print("   - Implement CRUD operations")
    print("\n" + "="*60)


def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     OpenAPI Backend Code Generator (Swagger Codegen)     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install required tools first")
        sys.exit(1)
    
    # Install OpenAPI Generator
    if not install_openapi_generator():
        print("\n❌ Failed to install OpenAPI Generator")
        sys.exit(1)
    
    # Generate server code
    if not generate_server():
        print("\n❌ Failed to generate backend code")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()


if __name__ == '__main__':
    main()
