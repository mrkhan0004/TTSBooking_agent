"""
Main Launcher for AI Voice Assistant
Integrates all components: STT, NLU, Planner, Executor, TTS
"""
import os
import sys
import signal
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime

# Import our modules
from nlp import EnhancedNLU
from planner import DecisionPlanner
from executor import ActionExecutor
from tts_local import LocalTTS, TTSConfig
from stt_vosk import VoskSTT

# Import Flask app
from app import create_app


class AIVoiceAssistant:
    """Main AI Voice Assistant class that orchestrates all components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_running = False
        
        # Component paths
        self.storage_path = self.config.get("storage_path", "data")
        # Ensure model_path is a valid string; fall back to default if None/empty
        self.model_path = self.config.get("model_path") or "models/vosk-model-small-en-us-0.15"
        
        # Initialize components
        self.nlu: Optional[EnhancedNLU] = None
        self.planner: Optional[DecisionPlanner] = None
        self.executor: Optional[ActionExecutor] = None
        self.tts: Optional[LocalTTS] = None
        self.stt: Optional[VoskSTT] = None
        
        # Flask app
        self.flask_app = None
        
        # User sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize all components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all AI assistant components"""
        print("Initializing AI Voice Assistant...")
        
        try:
            # Initialize NLU
            print("Loading NLU module...")
            self.nlu = EnhancedNLU(use_spacy=True)
            print("✓ NLU module loaded")
            
            # Initialize Planner
            print("Loading Decision Planner...")
            self.planner = DecisionPlanner(storage_path=self.storage_path)
            print("✓ Decision Planner loaded")
            
            # Initialize Executor
            print("Loading Action Executor...")
            self.executor = ActionExecutor(storage_path=self.storage_path)
            print("✓ Action Executor loaded")
            
            # Initialize TTS
            print("Loading Text-to-Speech...")
            tts_config = TTSConfig(
                rate=self.config.get("tts_rate", 200),
                volume=self.config.get("tts_volume", 0.8),
                enabled=self.config.get("tts_enabled", True)
            )
            self.tts = LocalTTS(tts_config)
            if self.tts.is_initialized:
                print("✓ Text-to-Speech loaded")
            else:
                print("⚠ Text-to-Speech failed to load (will use text responses)")
            
            # Initialize STT (optional, only if model exists)
            if os.path.exists(self.model_path):
                print("Loading Speech-to-Text...")
                self.stt = VoskSTT(model_path=self.model_path)
                if self.stt.is_available():
                    print("✓ Speech-to-Text loaded")
                else:
                    print("⚠ Speech-to-Text failed to load (will use text input)")
                    self.stt = None
            else:
                print(f"⚠ Vosk model not found at {self.model_path}")
                print("   STT will not be available. You can:")
                print("   1. Download a model from: https://alphacephei.com/vosk/models")
                print("   2. Place it in the 'models' directory")
                print("   3. Or use text input via the web interface")
            
            # Initialize Flask app
            print("Loading Web Interface...")
            self.flask_app = create_app()
            print("✓ Web Interface loaded")
            
            print("\n🎉 AI Voice Assistant initialized successfully!")
            self._print_status()
            
        except Exception as e:
            print(f"❌ Failed to initialize AI Assistant: {e}")
            sys.exit(1)
    
    def _print_status(self):
        """Print current system status"""
        print("\n" + "="*50)
        print("AI VOICE ASSISTANT STATUS")
        print("="*50)
        print(f"NLU (Natural Language Understanding): {'✓' if self.nlu else '✗'}")
        print(f"Planner (Decision Making): {'✓' if self.planner else '✗'}")
        print(f"Executor (Action Execution): {'✓' if self.executor else '✗'}")
        print(f"TTS (Text-to-Speech): {'✓' if self.tts and self.tts.is_initialized else '✗'}")
        print(f"STT (Speech-to-Text): {'✓' if self.stt and self.stt.is_available() else '✗'}")
        print(f"Web Interface: {'✓' if self.flask_app else '✗'}")
        print("="*50)
        print(f"Storage Path: {self.storage_path}")
        print(f"Model Path: {self.model_path}")
        print("="*50)
    
    def process_text(self, text: str, user_id: str = "default", 
                    use_tts: bool = True) -> Dict[str, Any]:
        """
        Process text input and return response
        Args:
            text: Input text from user
            user_id: Unique user identifier
            use_tts: Whether to use TTS for response
        Returns:
            Dictionary with response data
        """
        if not self.nlu or not self.planner or not self.executor:
            return {"error": "AI Assistant not properly initialized"}
        
        try:
            # Step 1: Parse intent and extract entities
            intent = self.nlu.parse_intent(text)
            
            # Step 2: Plan actions based on intent
            actions, response_text = self.planner.process_intent(
                user_id, intent.name, intent.entities, intent.confidence, text
            )
            
            # Step 3: Execute planned actions
            execution_results = []
            for action in actions:
                if not action.requires_confirmation:
                    result = self.executor.execute_action(action.name, action.parameters)
                    execution_results.append({
                        "action": action.name,
                        "success": result.success,
                        "message": result.message,
                        "data": result.data
                    })
            
            # Step 4: Generate final response
            final_response = response_text
            
            # If actions were executed successfully, update response
            if execution_results:
                success_count = sum(1 for r in execution_results if r["success"])
                if success_count > 0:
                    success_messages = [r["message"] for r in execution_results if r["success"]]
                    if success_messages:
                        final_response = "; ".join(success_messages)
            
            # Step 5: Use TTS if available and requested
            if use_tts and self.tts and self.tts.is_initialized:
                self.tts.speak(final_response)
            
            return {
                "success": True,
                "response": final_response,
                "intent": intent.name,
                "confidence": intent.confidence,
                "entities": intent.entities,
                "actions": [{"name": a.name, "parameters": a.parameters, "requires_confirmation": a.requires_confirmation} for a in actions],
                "execution_results": execution_results
            }
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(f"❌ {error_msg}")
            
            if use_tts and self.tts and self.tts.is_initialized:
                self.tts.speak("Sorry, I encountered an error processing your request.")
            
            return {
                "success": False,
                "error": error_msg,
                "response": "Sorry, I encountered an error processing your request."
            }
    
    def process_voice(self, user_id: str = "default", timeout: float = 5.0) -> Dict[str, Any]:
        """
        Process voice input and return response
        Args:
            user_id: Unique user identifier
            timeout: Maximum time to listen for speech
        Returns:
            Dictionary with response data
        """
        if not self.stt or not self.stt.is_available():
            return {"error": "Speech-to-Text not available"}
        
        try:
            # Listen for speech
            recognized_text = self.stt.listen_once(timeout)
            
            if not recognized_text:
                return {
                    "success": False,
                    "response": "I didn't hear anything. Please try again.",
                    "recognized_text": None
                }
            
            # Process the recognized text
            result = self.process_text(recognized_text, user_id, use_tts=True)
            result["recognized_text"] = recognized_text
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing voice: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "response": "Sorry, I had trouble processing your voice input."
            }
    
    def start_web_server(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Start the Flask web server"""
        if not self.flask_app:
            print("❌ Flask app not initialized")
            return
        
        print(f"\n🌐 Starting web server at http://{host}:{port}")
        print("   You can access the voice interface through your web browser")
        print("   Press Ctrl+C to stop the server")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Shutting down AI Assistant...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            self.flask_app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.shutdown()
    
    def start_interactive_mode(self):
        """Start interactive text-based mode"""
        print("\n🤖 Starting Interactive Mode")
        print("Type 'quit' or 'exit' to stop")
        print("Type 'voice' to switch to voice mode")
        print("Type 'status' to see system status")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'voice':
                    if self.stt and self.stt.is_available():
                        print("🎤 Listening... (speak now)")
                        result = self.process_voice()
                        print(f"Recognized: {result.get('recognized_text', 'Nothing heard')}")
                        print(f"Assistant: {result.get('response', 'No response')}")
                    else:
                        print("❌ Voice mode not available (STT not initialized)")
                elif user_input.lower() == 'status':
                    self._print_status()
                elif user_input:
                    result = self.process_text(user_input, use_tts=False)
                    print(f"Assistant: {result.get('response', 'No response')}")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\n👋 Goodbye!")
    
    def shutdown(self):
        """Shutdown all components"""
        print("\n🛑 Shutting down AI Voice Assistant...")
        
        if self.tts:
            self.tts.shutdown()
        
        if self.stt:
            self.stt.shutdown()
        
        print("✓ Shutdown complete")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Voice Assistant")
    parser.add_argument("--mode", choices=["web", "interactive", "voice"], 
                       default="web", help="Run mode")
    parser.add_argument("--host", default="0.0.0.0", help="Web server host")
    parser.add_argument("--port", type=int, default=5000, help="Web server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--storage", default="data", help="Storage directory")
    parser.add_argument("--model", help="Path to Vosk model")
    parser.add_argument("--no-tts", action="store_true", help="Disable TTS")
    parser.add_argument("--tts-rate", type=int, default=200, help="TTS speech rate")
    parser.add_argument("--tts-volume", type=float, default=0.8, help="TTS volume")
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        "storage_path": args.storage,
        "model_path": args.model,
        "tts_enabled": not args.no_tts,
        "tts_rate": args.tts_rate,
        "tts_volume": args.tts_volume
    }
    
    # Initialize assistant
    assistant = AIVoiceAssistant(config)
    
    # Run in selected mode
    if args.mode == "web":
        assistant.start_web_server(args.host, args.port, args.debug)
    elif args.mode == "interactive":
        assistant.start_interactive_mode()
    elif args.mode == "voice":
        if assistant.stt and assistant.stt.is_available():
            print("🎤 Voice mode - Press Ctrl+C to stop")
            try:
                while True:
                    result = assistant.process_voice()
                    print(f"Recognized: {result.get('recognized_text', 'Nothing heard')}")
                    print(f"Assistant: {result.get('response', 'No response')}")
                    print("-" * 40)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Voice mode not available (STT not initialized)")
    
    assistant.shutdown()


if __name__ == "__main__":
    main()
