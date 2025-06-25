#!/usr/bin/env python
"""
Setup script for the Loan Repayment Backend
"""
import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("⚠️  Please update .env with your Paynow credentials")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")

def main():
    print("🚀 Setting up Loan Repayment Backend...")
    
    if install_requirements():
        create_env_file()
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Update .env file with your Paynow credentials")
        print("2. Run: python app.py")
        print("3. Backend will be available at: http://localhost:5000")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
