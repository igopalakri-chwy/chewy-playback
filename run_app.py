#!/usr/bin/env python3
import subprocess
import sys
import os

def install_flask():
    """Install Flask if not already installed"""
    try:
        import flask
        print(f"✅ Flask {flask.__version__} is already installed")
        return True
    except ImportError:
        print("📦 Installing Flask...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "Flask"])
            print("✅ Flask installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Flask: {e}")
            return False

def run_app():
    """Run the Flask app"""
    try:
        print("🚀 Starting Flask app...")
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running app: {e}")

if __name__ == "__main__":
    if install_flask():
        run_app()
    else:
        print("❌ Cannot run app without Flask")
        sys.exit(1) 