import re
import dateparser
from dataclasses import dataclass
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


@dataclass
class Intent:
    name: str
    entities: Dict[str, Any]
    confidence: float = 1.0


class EnhancedNLU:
    def __init__(self, use_spacy: bool = True):
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("spaCy model not found. Installing...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")
        
        # Intent keywords
        self.intent_keywords = {
            "book": ["book", "schedule", "reserve", "set up", "arrange", "slot", "appointment", "meeting"],
            "cancel": ["cancel", "drop", "remove", "delete", "unbook"],
            "greet": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "query": ["what", "when", "where", "how", "show", "list", "available", "free"],
            "system": ["open", "launch", "start", "run", "execute", "shutdown", "restart"]
        }
        
        # Time patterns
        self.time_patterns = [
            r'\b([01]?\d|2[0-3]):([0-5]\d)\s?(am|pm)?\b',  # 10:30, 10:30am
            r'\b([01]?\d|2[0-3])\s?(am|pm)\b',  # 10am, 2pm
            r'\b(quarter|half)\s+(past|to)\s+([01]?\d|2[0-3])\b',  # quarter past 10
            r'\b([01]?\d|2[0-3])\s+(o\'?clock)\b'  # 10 o'clock
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b(today|tomorrow|yesterday)\b',
            r'\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month)\b',
            r'\b(in|after)\s+(\d+)\s+(day|days|week|weeks|month|months)\b',
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b'  # MM/DD/YYYY
        ]

    def parse_intent(self, text: str, lang: str = "en-US") -> Intent:
        """Enhanced intent parsing with spaCy and better entity extraction"""
        text = text.lower().strip()
        
        # Use spaCy if available
        if self.nlp and self.use_spacy:
            return self._parse_with_spacy(text, lang)
        else:
            return self._parse_with_rules(text, lang)

    def _parse_with_spacy(self, text: str, lang: str) -> Intent:
        """Parse intent using spaCy NLP model"""
        doc = self.nlp(text)
        
        # Intent detection
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for token in doc if any(kw in token.text for kw in keywords))
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return Intent(name="unknown", entities={}, confidence=0.0)
        
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_name = best_intent[0]
        confidence = min(best_intent[1] / len(self.intent_keywords[intent_name]), 1.0)
        
        # Entity extraction
        entities = self._extract_entities_spacy(doc)
        
        return Intent(name=intent_name, entities=entities, confidence=confidence)

    def _parse_with_rules(self, text: str, lang: str) -> Intent:
        """Fallback rule-based parsing"""
        # Intent detection
        for intent, keywords in self.intent_keywords.items():
            if any(kw in text for kw in keywords):
                entities = self._extract_entities_rules(text)
                return Intent(name=intent, entities=entities, confidence=0.8)
        
        return Intent(name="unknown", entities={}, confidence=0.0)

    def _extract_entities_spacy(self, doc) -> Dict[str, Any]:
        """Extract entities using spaCy"""
        entities = {}
        
        # Time entities
        for ent in doc.ents:
            if ent.label_ in ["TIME", "DATE"]:
                if ent.label_ == "TIME":
                    entities["time"] = self._normalize_time(ent.text)
                elif ent.label_ == "DATE":
                    entities["date"] = self._normalize_date(ent.text)
        
        # Manual pattern matching for better coverage
        time_entity = self._extract_time_from_text(doc.text)
        if time_entity:
            entities["time"] = time_entity
            
        date_entity = self._extract_date_from_text(doc.text)
        if date_entity:
            entities["date"] = date_entity
        
        return entities

    def _extract_entities_rules(self, text: str) -> Dict[str, Any]:
        """Extract entities using regex patterns"""
        entities = {}
        
        time_entity = self._extract_time_from_text(text)
        if time_entity:
            entities["time"] = time_entity
            
        date_entity = self._extract_date_from_text(text)
        if date_entity:
            entities["date"] = date_entity
        
        return entities

    def _extract_time_from_text(self, text: str) -> Optional[str]:
        """Extract time from text using multiple patterns"""
        text = text.lower()
        
        # Pattern 1: HH:MM format
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_time(match.group())
        
        # Pattern 2: Word-based time
        word_to_time = {
            "ten": "10:00", "eleven": "11:00", "twelve": "12:00",
            "one": "13:00", "two": "14:00", "three": "15:00",
            "four": "16:00", "five": "17:00", "six": "18:00",
            "seven": "19:00", "eight": "20:00", "nine": "21:00"
        }
        
        for word, time in word_to_time.items():
            if word in text and any(am_pm in text for am_pm in ["am", "pm", "morning", "afternoon", "evening"]):
                return self._normalize_time(f"{word} {next(am_pm for am_pm in ['am', 'pm', 'morning', 'afternoon', 'evening'] if am_pm in text)}")
        
        return None

    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text"""
        # Use dateparser for natural language dates
        try:
            parsed_date = dateparser.parse(text)
            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d")
        except:
            pass
        
        # Fallback patterns
        if "today" in text:
            return datetime.now().strftime("%Y-%m-%d")
        elif "tomorrow" in text:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "yesterday" in text:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        return None

    def _normalize_time(self, time_str: str) -> str:
        """Normalize time string to HH:MM format"""
        time_str = time_str.lower().strip()
        
        # Handle AM/PM
        if "pm" in time_str and ":" not in time_str:
            hour = re.search(r'(\d+)', time_str)
            if hour:
                h = int(hour.group(1))
                if h < 12:
                    h += 12
                return f"{h:02d}:00"
        
        # Handle HH:MM format
        match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        
        # Handle HH format
        match = re.search(r'(\d{1,2})(?!:)', time_str)
        if match:
            return f"{int(match.group(1)):02d}:00"
        
        return time_str

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format"""
        try:
            parsed = dateparser.parse(date_str)
            if parsed:
                return parsed.strftime("%Y-%m-%d")
        except:
            pass
        return date_str


# Backward compatibility
def parse_intent(text: str, lang: str = "en-US") -> Intent:
    """Backward compatible function"""
    nlu = EnhancedNLU()
    return nlu.parse_intent(text, lang)



