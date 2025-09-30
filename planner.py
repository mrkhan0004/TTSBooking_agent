"""
Decision Planner Module - Orchestrates actions based on NLU output
"""
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Action:
    """Represents an action to be executed"""
    name: str
    parameters: Dict[str, Any]
    priority: int = 1
    requires_confirmation: bool = False


@dataclass
class ConversationContext:
    """Maintains conversation context and memory"""
    user_id: str
    current_intent: str
    entities: Dict[str, Any]
    pending_actions: List[Action]
    conversation_history: List[Dict[str, Any]]
    last_updated: datetime


class DecisionPlanner:
    """Main decision maker and action orchestrator"""
    
    def __init__(self, storage_path: str = "data"):
        self.storage_path = storage_path
        self.contexts: Dict[str, ConversationContext] = {}
        self.action_handlers = {
            "book_slot": self._plan_booking,
            "cancel_slot": self._plan_cancellation,
            "query_slots": self._plan_query,
            "system_action": self._plan_system_action,
            "greet": self._plan_greeting,
            "unknown": self._plan_fallback
        }
        
        # Load persistent context if exists
        self._load_contexts()
    
    def process_intent(self, user_id: str, intent_name: str, entities: Dict[str, Any], 
                      confidence: float, original_text: str) -> Tuple[List[Action], str]:
        """
        Main entry point for processing intents and planning actions
        Returns: (list of actions, response message)
        """
        # Get or create user context
        context = self._get_or_create_context(user_id, intent_name, entities)
        
        # Update conversation history
        self._add_to_history(context, original_text, intent_name, entities)
        
        # Plan actions based on intent
        if intent_name in self.action_handlers:
            actions, response = self.action_handlers[intent_name](context, entities, confidence)
        else:
            actions, response = self._plan_fallback(context, entities, confidence)
        
        # Add actions to context
        context.pending_actions.extend(actions)
        context.current_intent = intent_name
        context.entities = entities
        context.last_updated = datetime.now()
        
        # Save context
        self._save_context(context)
        
        return actions, response
    
    def _get_or_create_context(self, user_id: str, intent_name: str, 
                              entities: Dict[str, Any]) -> ConversationContext:
        """Get existing context or create new one"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(
                user_id=user_id,
                current_intent=intent_name,
                entities=entities,
                pending_actions=[],
                conversation_history=[],
                last_updated=datetime.now()
            )
        return self.contexts[user_id]
    
    def _add_to_history(self, context: ConversationContext, text: str, 
                       intent: str, entities: Dict[str, Any]):
        """Add interaction to conversation history"""
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "intent": intent,
            "entities": entities
        })
        
        # Keep only last 10 interactions
        if len(context.conversation_history) > 10:
            context.conversation_history = context.conversation_history[-10:]
    
    def _plan_booking(self, context: ConversationContext, entities: Dict[str, Any], 
                     confidence: float) -> Tuple[List[Action], str]:
        """Plan booking-related actions"""
        actions = []
        
        # Check if we have required information
        time = entities.get("time")
        date = entities.get("date")
        
        if not time and not date:
            # Ask for time preference
            response = "I'd be happy to book a slot for you. What time would you prefer?"
            actions.append(Action("clarify_time", {"missing": "time"}, requires_confirmation=True))
            
        elif not time:
            # Ask specifically for time
            response = f"Great! I can book a slot for {date or 'today'}. What time would you like?"
            actions.append(Action("clarify_time", {"missing": "time", "date": date}, requires_confirmation=True))
            
        elif not date:
            # Use today as default, confirm time
            today = datetime.now().strftime("%Y-%m-%d")
            response = f"Perfect! I'll book {time} for today ({today}). Should I proceed?"
            actions.append(Action("book_slot", {
                "time": time, 
                "date": today
            }, requires_confirmation=True))
            
        else:
            # We have both time and date
            response = f"Excellent! I'll book {time} on {date}. Should I proceed?"
            actions.append(Action("book_slot", {
                "time": time,
                "date": date
            }, requires_confirmation=True))
        
        return actions, response
    
    def _plan_cancellation(self, context: ConversationContext, entities: Dict[str, Any], 
                          confidence: float) -> Tuple[List[Action], str]:
        """Plan cancellation actions"""
        actions = []
        time = entities.get("time")
        date = entities.get("date")
        
        if not time and not date:
            # Need more info
            response = "I can help you cancel a booking. Which date and time would you like to cancel?"
            actions.append(Action("clarify_cancellation", {"missing": ["time", "date"]}, requires_confirmation=True))
        else:
            response = f"I'll cancel your booking for {time or 'any time'} on {date or 'today'}. Confirm?"
            actions.append(Action("cancel_slot", {
                "time": time,
                "date": date or datetime.now().strftime("%Y-%m-%d")
            }, requires_confirmation=True))
        
        return actions, response
    
    def _plan_query(self, context: ConversationContext, entities: Dict[str, Any], 
                   confidence: float) -> Tuple[List[Action], str]:
        """Plan query actions"""
        actions = []
        
        # Determine what to query
        if "available" in str(entities) or "free" in str(entities):
            date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))
            response = f"I'll check available slots for {date}."
            actions.append(Action("query_available_slots", {"date": date}))
            
        elif "bookings" in str(entities) or "my" in str(entities):
            date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))
            response = f"I'll show your bookings for {date}."
            actions.append(Action("query_user_bookings", {"date": date}))
            
        else:
            response = "What would you like to know about your bookings or available slots?"
            actions.append(Action("clarify_query", {"missing": "query_type"}, requires_confirmation=True))
        
        return actions, response
    
    def _plan_system_action(self, context: ConversationContext, entities: Dict[str, Any], 
                           confidence: float) -> Tuple[List[Action], str]:
        """Plan system-level actions"""
        actions = []
        
        # Extract system command
        original_text = context.conversation_history[-1]["text"] if context.conversation_history else ""
        
        if any(word in original_text.lower() for word in ["open", "launch", "start"]):
            response = "I can help you open applications or files. What would you like me to open?"
            actions.append(Action("system_open", {"command": "open"}, requires_confirmation=True))
            
        elif any(word in original_text.lower() for word in ["shutdown", "restart", "sleep"]):
            response = "I can help with system commands. What system action would you like?"
            actions.append(Action("system_control", {"command": "system"}, requires_confirmation=True))
            
        else:
            response = "I can help with system tasks. What would you like me to do?"
            actions.append(Action("clarify_system", {"missing": "system_command"}, requires_confirmation=True))
        
        return actions, response
    
    def _plan_greeting(self, context: ConversationContext, entities: Dict[str, Any], 
                      confidence: float) -> Tuple[List[Action], str]:
        """Plan greeting response"""
        actions = []
        
        # Personalized greeting based on history
        if len(context.conversation_history) > 1:
            response = "Hello again! How can I assist you today?"
        else:
            response = "Hello! I'm your personal assistant. I can help you book slots, manage your schedule, or assist with system tasks. What would you like to do?"
        
        return actions, response
    
    def _plan_fallback(self, context: ConversationContext, entities: Dict[str, Any], 
                      confidence: float) -> Tuple[List[Action], str]:
        """Handle unknown intents"""
        actions = []
        
        # Check if this might be a follow-up to previous intent
        if context.current_intent == "book_slot" and context.pending_actions:
            # This might be providing missing information
            time = entities.get("time")
            date = entities.get("date")
            
            if time or date:
                # Merge with existing booking action
                existing_action = context.pending_actions[0]
                if time:
                    existing_action.parameters["time"] = time
                if date:
                    existing_action.parameters["date"] = date
                
                response = f"Got it! I'll book {existing_action.parameters.get('time', 'a slot')} on {existing_action.parameters.get('date', 'today')}. Should I proceed?"
                return [], response
        
        # Generic fallback
        response = "I didn't quite understand that. You can ask me to book a slot, check availability, or help with other tasks. What would you like to do?"
        actions.append(Action("clarify_intent", {"missing": "intent"}, requires_confirmation=True))
        
        return actions, response
    
    def confirm_action(self, user_id: str, action_name: str, confirmed: bool) -> Tuple[str, Optional[Action]]:
        """Handle user confirmation of actions"""
        if user_id not in self.contexts:
            return "I don't have any pending actions for you.", None
        
        context = self.contexts[user_id]
        
        # Find the action to confirm
        action_to_confirm = None
        for action in context.pending_actions:
            if action.name == action_name and action.requires_confirmation:
                action_to_confirm = action
                break
        
        if not action_to_confirm:
            return "I don't have that action pending for confirmation.", None
        
        if confirmed:
            # Remove from pending and return for execution
            context.pending_actions.remove(action_to_confirm)
            context.pending_actions = [a for a in context.pending_actions if a.name != action_name]
            self._save_context(context)
            
            return f"Confirmed! Executing {action_name}.", action_to_confirm
        else:
            # Remove from pending
            context.pending_actions.remove(action_to_confirm)
            self._save_context(context)
            
            return "Action cancelled. How else can I help you?", None
    
    def _save_context(self, context: ConversationContext):
        """Save context to persistent storage"""
        os.makedirs(self.storage_path, exist_ok=True)
        context_file = os.path.join(self.storage_path, f"context_{context.user_id}.json")
        
        # Convert to serializable format
        context_data = {
            "user_id": context.user_id,
            "current_intent": context.current_intent,
            "entities": context.entities,
            "conversation_history": context.conversation_history,
            "last_updated": context.last_updated.isoformat(),
            "pending_actions": [
                {
                    "name": action.name,
                    "parameters": action.parameters,
                    "priority": action.priority,
                    "requires_confirmation": action.requires_confirmation
                }
                for action in context.pending_actions
            ]
        }
        
        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(context_data, f, indent=2)
    
    def _load_contexts(self):
        """Load contexts from persistent storage"""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.startswith("context_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(self.storage_path, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Convert back to ConversationContext
                    pending_actions = [
                        Action(
                            name=action_data["name"],
                            parameters=action_data["parameters"],
                            priority=action_data.get("priority", 1),
                            requires_confirmation=action_data.get("requires_confirmation", False)
                        )
                        for action_data in data.get("pending_actions", [])
                    ]
                    
                    context = ConversationContext(
                        user_id=data["user_id"],
                        current_intent=data["current_intent"],
                        entities=data["entities"],
                        pending_actions=pending_actions,
                        conversation_history=data.get("conversation_history", []),
                        last_updated=datetime.fromisoformat(data["last_updated"])
                    )
                    
                    self.contexts[data["user_id"]] = context
                    
                except Exception as e:
                    print(f"Error loading context from {filename}: {e}")
    
    def get_user_context(self, user_id: str) -> Optional[ConversationContext]:
        """Get context for a specific user"""
        return self.contexts.get(user_id)
    
    def clear_user_context(self, user_id: str) -> bool:
        """Clear context for a specific user"""
        if user_id in self.contexts:
            del self.contexts[user_id]
            
            # Also remove persistent file
            context_file = os.path.join(self.storage_path, f"context_{user_id}.json")
            if os.path.exists(context_file):
                os.remove(context_file)
            
            return True
        return False

