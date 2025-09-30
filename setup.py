"""
Setup script for AI Voice Assistant
"""
import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"Running: {command}")
    if description:
        print(f"  {description}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e}")
        if e.stderr:
            print(f"  Error details: {e.stderr.strip()}")
        return False


def install_python_packages():
    """Install required Python packages"""
    print("\n📦 Installing Python packages...")
    
    packages = [
        "Flask==3.0.3",
        "pyttsx3==2.90", 
        "spacy==3.7.2",
        "dateparser==1.2.0",
        "vosk==0.3.45",
        "pyaudio==0.2.11",
        "python-dateutil==2.8.2",
        "numpy==1.24.3"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        if not run_command(f"{sys.executable} -m pip install {package}"):
            print(f"⚠️  Failed to install {package}")
            print("   You may need to install it manually later")
    
    print("✅ Python packages installation completed")


def download_spacy_model():
    """Download spaCy English model"""
    print("\n🧠 Downloading spaCy English model...")
    
    try:
        # Try to download the model
        run_command(f"{sys.executable} -m spacy download en_core_web_sm")
        print("✅ spaCy model downloaded successfully")
    except Exception as e:
        print(f"⚠️  Failed to download spaCy model: {e}")
        print("   The system will fall back to rule-based NLP")


def download_vosk_model():
    """Download Vosk speech recognition model"""
    print("\n🎤 Setting up Vosk speech recognition...")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / "vosk-model-small-en-us-0.15"
    
    if model_path.exists():
        print("✅ Vosk model already exists")
        return
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = models_dir / "vosk-model-small-en-us-0.15.zip"
    
    print(f"Downloading Vosk model from {model_url}...")
    print("This may take a few minutes (model is ~40MB)...")
    
    try:
        # Download the model
        urllib.request.urlretrieve(model_url, zip_path)
        print("✅ Model downloaded successfully")
        
        # Extract the model
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Clean up zip file
        zip_path.unlink()
        
        print("✅ Vosk model setup completed")
        
    except Exception as e:
        print(f"⚠️  Failed to download Vosk model: {e}")
        print("   Speech-to-text will not be available")
        print("   You can download it manually from: https://alphacephei.com/vosk/models")


def create_data_directories():
    """Create necessary data directories"""
    print("\n📁 Creating data directories...")
    
    directories = ["data", "logs", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def create_sample_config():
    """Create sample configuration file"""
    print("\n⚙️  Creating configuration file...")
    
    config_content = """# AI Voice Assistant Configuration

# Storage settings
STORAGE_PATH = "data"

# Vosk model path (for offline speech recognition)
VOSK_MODEL_PATH = "models/vosk-model-small-en-us-0.15"

# TTS settings
TTS_ENABLED = true
TTS_RATE = 200
TTS_VOLUME = 0.8

# Web server settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
WEB_DEBUG = false

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = "logs/assistant.log"
"""
    
    config_path = Path("config.ini")
    if not config_path.exists():
        with open(config_path, "w") as f:
            f.write(config_content)
        print("✅ Configuration file created: config.ini")
    else:
        print("✅ Configuration file already exists")


def check_system_requirements():
    """Check system requirements"""
    print("\n🔍 Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return False
    else:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check operating system
    system = platform.system()
    print(f"✅ Operating system: {system}")
    
    # Check for audio libraries
    print("Checking audio libraries...")
    
    if system == "Windows":
        print("✅ Windows detected - audio should work with default drivers")
    elif system == "Darwin":  # macOS
        print("✅ macOS detected - audio should work with default drivers")
    elif system == "Linux":
        print("⚠️  Linux detected - you may need to install audio development libraries:")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
    
    return True


def create_startup_scripts():
    """Create startup scripts for different platforms"""
    print("\n🚀 Creating startup scripts...")
    
    # Windows batch file
    windows_script = """@echo off
echo Starting AI Voice Assistant...
python main.py --mode web
pause
"""
    
    with open("start_assistant.bat", "w") as f:
        f.write(windows_script)
    print("✅ Created start_assistant.bat")
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting AI Voice Assistant..."
python3 main.py --mode web
"""
    
    with open("start_assistant.sh", "w") as f:
        f.write(unix_script)
    
    # Make it executable on Unix systems
    if platform.system() != "Windows":
        os.chmod("start_assistant.sh", 0o755)
    
    print("✅ Created start_assistant.sh")


def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🎉 AI VOICE ASSISTANT SETUP COMPLETED!")
    print("="*60)
    print("\n📋 USAGE INSTRUCTIONS:")
    print("\n1. Start the web interface:")
    print("   python main.py --mode web")
    print("   or")
    print("   python main.py --host 0.0.0.0 --port 5000")
    print("\n2. Start interactive text mode:")
    print("   python main.py --mode interactive")
    print("\n3. Start voice-only mode:")
    print("   python main.py --mode voice")
    print("\n4. Web interface will be available at:")
    print("   http://localhost:5000")
    print("\n🎤 VOICE FEATURES:")
    print("- Click 'Start Speaking' to use voice input")
    print("- Use 'Quick Actions' for common tasks")
    print("- Speech recognition works in Chrome/Edge browsers")
    print("\n📝 COMMON COMMANDS:")
    print("- 'Hello' - Greet the assistant")
    print("- 'Book a slot' - Book an appointment")
    print("- 'Book tomorrow at 10 AM' - Book specific time")
    print("- 'Show available slots' - Check availability")
    print("- 'Show my bookings' - View your bookings")
    print("\n🔧 TROUBLESHOOTING:")
    print("- If speech recognition doesn't work, check browser permissions")
    print("- If TTS doesn't work, check system audio settings")
    print("- For offline STT, ensure Vosk model is downloaded")
    print("\n📚 For more help, run: python main.py --help")
    print("="*60)


def main():
    """Main setup function"""
    print("🤖 AI Voice Assistant Setup")
    print("="*40)
    
    # Check system requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met. Please fix the issues above.")
        return
    
    # Install Python packages
    install_python_packages()
    
    # Download spaCy model
    download_spacy_model()
    
    # Download Vosk model
    download_vosk_model()
    
    # Create directories
    create_data_directories()
    
    # Create configuration
    create_sample_config()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Print usage instructions
    print_usage_instructions()


if __name__ == "__main__":
    main()

