# 🤖 AI Voice Assistant - Offline Jarvis

A comprehensive offline AI voice assistant that can handle natural language interactions, booking management, and system tasks without requiring internet connectivity.

## ✨ Features

### 🎤 **Voice Interaction**
- **Offline Speech-to-Text**: Uses Vosk for completely offline speech recognition
- **Text-to-Speech**: Local TTS with pyttsx3 for natural voice responses
- **Web Speech API**: Browser-based speech recognition for web interface
- **Multi-language Support**: English and Hindi support

### 🧠 **Advanced AI Processing**
- **Enhanced NLU**: spaCy-powered natural language understanding
- **Intent Recognition**: Sophisticated intent detection with confidence scoring
- **Entity Extraction**: Time, date, and context extraction from natural language
- **Decision Planning**: Smart action planning and execution orchestration

### 📅 **Booking Management**
- **Smart Scheduling**: Natural language booking ("book tomorrow at 10 AM")
- **Calendar Integration**: Automatic .ics file generation for calendar apps
- **Availability Checking**: Real-time slot availability
- **Booking History**: Track and manage your appointments

### 🎯 **System Integration**
- **System Commands**: Open applications, files, and perform system tasks
- **File Management**: Create, organize, and manage files
- **Notifications**: System notifications for important events
- **Offline Operation**: Works completely without internet

### 🌐 **Modern Web Interface**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Interaction**: Live conversation with visual feedback
- **Quick Actions**: One-click access to common tasks
- **Conversation History**: Persistent chat history
- **Dark/Light Themes**: Beautiful, modern UI

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd ai-voice-assistant

# Run the setup script
python setup.py
```

### 2. **Start the Assistant**
```bash
# Web interface (recommended)
python main.py --mode web

# Interactive text mode
python main.py --mode interactive

# Voice-only mode
python main.py --mode voice
```

### 3. **Access Web Interface**
Open your browser and go to: `http://localhost:5000`

## 📋 System Requirements

### **Minimum Requirements**
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for models and dependencies
- **Audio**: Microphone and speakers/headphones

### **Recommended Setup**
- **Python**: 3.9+
- **RAM**: 8GB+
- **Storage**: 2GB+ SSD
- **Browser**: Chrome/Edge (for Web Speech API)

### **Supported Platforms**
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 18.04+, Debian, CentOS)

## 🛠️ Installation Options

### **Option 1: Automated Setup (Recommended)**
```bash
python setup.py
```
This will automatically:
- Install all Python dependencies
- Download spaCy English model
- Download Vosk speech recognition model
- Create necessary directories
- Generate configuration files

### **Option 2: Manual Installation**
```bash
# Install Python packages
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download Vosk model manually from:
# https://alphacephei.com/vosk/models
# Place in models/ directory
```

### **Option 3: Virtual Environment (Recommended for Development)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## 🎯 Usage Examples

### **Voice Commands**
```
"Hello" → Greet the assistant
"Book a slot" → Book next available slot
"Book tomorrow at 10 AM" → Book specific time
"Show available slots" → Check availability
"Cancel my 2 PM booking" → Cancel appointment
"Open calculator" → Launch calculator app
"What's my schedule?" → Show bookings
```

### **Text Commands**
```
book slot 14:00 → Book 2 PM slot
schedule meeting tomorrow → Book tomorrow
check availability → Show free slots
show bookings → Display your appointments
```

## 🔧 Configuration

### **Main Configuration**
Edit `config.ini` to customize:
- Storage paths
- TTS settings (rate, volume)
- Web server settings
- Model paths

### **Command Line Options**
```bash
python main.py --help

Options:
  --mode {web,interactive,voice}  Run mode (default: web)
  --host HOST                     Web server host (default: 0.0.0.0)
  --port PORT                     Web server port (default: 5000)
  --debug                         Enable debug mode
  --storage PATH                  Storage directory
  --model PATH                    Vosk model path
  --no-tts                        Disable text-to-speech
  --tts-rate RATE                 TTS speech rate
  --tts-volume VOLUME             TTS volume (0.0-1.0)
```

## 📁 Project Structure

```
ai-voice-assistant/
├── main.py                 # Main launcher and server
├── setup.py               # Automated setup script
├── config.ini             # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── nlp.py                # Natural Language Understanding
├── planner.py            # Decision planning and orchestration
├── executor.py           # Action execution
├── tts_local.py          # Text-to-Speech engine
├── stt_vosk.py           # Speech-to-Text engine
├── storage.py            # Data storage management
├── utils.py              # Utility functions
│
├── app.py                # Flask web application
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── style.css         # Styling
│   └── script.js         # JavaScript functionality
│
├── data/                 # Data storage
│   ├── bookings.json     # Booking data
│   ├── slots.json        # Slot configuration
│   └── context_*.json    # User contexts
│
├── models/               # AI models
│   └── vosk-model-*/     # Vosk speech models
│
└── logs/                 # Log files
```

## 🧠 AI Components

### **Natural Language Understanding (NLU)**
- **spaCy Integration**: Advanced NLP with entity recognition
- **Intent Classification**: Multi-intent detection with confidence scoring
- **Entity Extraction**: Time, date, and context parsing
- **Fallback Handling**: Rule-based fallback for unsupported patterns

### **Decision Planner**
- **Action Planning**: Smart action selection and sequencing
- **Context Management**: Persistent conversation context
- **Confirmation Handling**: Interactive confirmation for critical actions
- **Memory Management**: Conversation history and user preferences

### **Action Executor**
- **Booking Management**: Create, update, cancel appointments
- **File Operations**: Generate .ics files, manage documents
- **System Integration**: Launch apps, system commands
- **Notification System**: User notifications and alerts

## 🎤 Voice Features

### **Speech Recognition**
- **Offline Operation**: Vosk-based STT works without internet
- **Browser Integration**: Web Speech API for web interface
- **Multi-language**: Support for multiple languages
- **Noise Handling**: Robust recognition in various environments

### **Text-to-Speech**
- **Local Synthesis**: pyttsx3 for offline voice output
- **Voice Selection**: Multiple voice options
- **Rate Control**: Adjustable speech speed
- **Volume Control**: Configurable audio levels

## 🌐 Web Interface Features

### **Modern UI/UX**
- **Responsive Design**: Works on all device sizes
- **Real-time Feedback**: Live speech recognition status
- **Visual Indicators**: Status indicators for all components
- **Accessibility**: Keyboard navigation and screen reader support

### **Interactive Elements**
- **Voice Controls**: Start/stop recording buttons
- **Quick Actions**: One-click common tasks
- **Date Picker**: Easy date selection for bookings
- **Conversation History**: Persistent chat log

### **Advanced Features**
- **Copy/Paste**: Easy text manipulation
- **Download Links**: Direct .ics file downloads
- **Status Monitoring**: Real-time component status
- **Error Handling**: Graceful error messages

## 🔧 Troubleshooting

### **Common Issues**

#### **Speech Recognition Not Working**
- Ensure microphone permissions are granted
- Use Chrome or Edge browser for Web Speech API
- Check if Vosk model is properly downloaded
- Verify audio drivers are working

#### **Text-to-Speech Issues**
- Check system audio settings
- Ensure speakers/headphones are connected
- Try different voice options in settings
- Restart the application

#### **Installation Problems**
- Ensure Python 3.8+ is installed
- Check internet connection for package downloads
- Run setup script as administrator (Windows)
- Install audio development libraries (Linux)

#### **Performance Issues**
- Close other applications to free RAM
- Use smaller Vosk models for better performance
- Disable TTS if not needed
- Check available disk space

### **Getting Help**
1. Check the logs in `logs/` directory
2. Run with `--debug` flag for detailed output
3. Verify all dependencies are installed
4. Check system requirements

## 🔒 Privacy & Security

### **Offline Operation**
- **No Internet Required**: All processing happens locally
- **No Data Sharing**: Your conversations stay on your device
- **Local Storage**: All data stored in local files
- **No Tracking**: No analytics or user tracking

### **Data Protection**
- **Local Files**: All data stored locally in `data/` directory
- **No Cloud**: No data sent to external servers
- **User Control**: You control all your data
- **Secure**: No network vulnerabilities

## 🚀 Advanced Usage

### **Customization**
- Modify `nlp.py` for custom intent recognition
- Extend `executor.py` for new action types
- Customize UI in `templates/` and `static/`
- Add new voice commands in `planner.py`

### **Integration**
- Use as a library in other Python projects
- Extend with additional AI models
- Integrate with external calendar systems
- Add custom system commands

### **Development**
```bash
# Run in development mode
python main.py --debug --mode web

# Test individual components
python -m nlp
python -m tts_local
python -m stt_vosk
```

## 📈 Performance Tips

### **Optimization**
- Use SSD storage for better I/O performance
- Allocate sufficient RAM (8GB+ recommended)
- Close unnecessary applications
- Use smaller Vosk models for faster startup

### **Resource Usage**
- **RAM**: ~200MB base + model size
- **CPU**: Low usage during idle, moderate during processing
- **Storage**: ~500MB for full installation
- **Network**: Only for initial setup and updates

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **spaCy**: Advanced NLP library
- **Vosk**: Offline speech recognition
- **pyttsx3**: Cross-platform TTS
- **Flask**: Web framework
- **Web Speech API**: Browser speech recognition

## 📞 Support

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join GitHub Discussions
- **Documentation**: Check this README and inline comments
- **Community**: Connect with other users

---

**Made with ❤️ for the open-source community**

*Transform your computer into a powerful, private AI assistant that works offline and respects your privacy.*