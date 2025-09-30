"""
Executor Module - Handles execution of planned actions
"""
import os
import json
import subprocess
import platform
import webbrowser
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of action execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    files_created: List[str] = None


class ActionExecutor:
    """Executes planned actions from the decision planner"""
    
    def __init__(self, storage_path: str = "data"):
        self.storage_path = storage_path
        self.bookings_file = os.path.join(storage_path, "bookings.json")
        self.slots_file = os.path.join(storage_path, "slots.json")
        
        # Ensure data directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize storage files
        self._ensure_storage_files()
        
        # Action handlers
        self.action_handlers = {
            "book_slot": self._execute_book_slot,
            "cancel_slot": self._execute_cancel_slot,
            "query_available_slots": self._execute_query_available,
            "query_user_bookings": self._execute_query_bookings,
            "system_open": self._execute_system_open,
            "system_control": self._execute_system_control,
            "create_ics": self._execute_create_ics,
            "send_notification": self._execute_send_notification
        }
    
    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute an action with given parameters"""
        if action_name in self.action_handlers:
            return self.action_handlers[action_name](parameters)
        else:
            return ExecutionResult(
                success=False,
                message=f"Unknown action: {action_name}"
            )
    
    def _execute_book_slot(self, params: Dict[str, Any]) -> ExecutionResult:
        """Execute booking a time slot"""
        time = params.get("time")
        date = params.get("date")
        
        if not time:
            return ExecutionResult(
                success=False,
                message="Time is required for booking"
            )
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Check availability
        available_slots = self._get_available_slots(date)
        if time not in available_slots:
            return ExecutionResult(
                success=False,
                message=f"Slot {time} is not available on {date}"
            )
        
        # Book the slot
        booking_data = {
            "time": time,
            "date": date,
            "booked_at": datetime.now().isoformat(),
            "booking_id": f"{date}_{time.replace(':', '')}"
        }
        
        success = self._save_booking(booking_data)
        
        if success:
            # Generate ICS file
            ics_file = self._generate_ics_file(booking_data)
            
            return ExecutionResult(
                success=True,
                message=f"Successfully booked {time} on {date}",
                data=booking_data,
                files_created=[ics_file] if ics_file else []
            )
        else:
            return ExecutionResult(
                success=False,
                message="Failed to save booking"
            )
    
    def _execute_cancel_slot(self, params: Dict[str, Any]) -> ExecutionResult:
        """Execute cancelling a booking"""
        time = params.get("time")
        date = params.get("date")
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Load bookings
        bookings = self._load_bookings()
        date_bookings = bookings.get("calendar", {}).get(date, [])
        
        # Find and remove booking
        original_count = len(date_bookings)
        if time:
            date_bookings = [b for b in date_bookings if b.get("time") != time]
        else:
            # Cancel all bookings for the date
            date_bookings = []
        
        if len(date_bookings) == original_count:
            return ExecutionResult(
                success=False,
                message=f"No booking found for {time or 'any time'} on {date}"
            )
        
        # Save updated bookings
        bookings["calendar"][date] = date_bookings
        self._save_bookings(bookings)
        
        return ExecutionResult(
            success=True,
            message=f"Cancelled booking for {time or 'all slots'} on {date}"
        )
    
    def _execute_query_available(self, params: Dict[str, Any]) -> ExecutionResult:
        """Query available slots"""
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        available_slots = self._get_available_slots(date)
        
        if available_slots:
            message = f"Available slots for {date}: {', '.join(available_slots)}"
        else:
            message = f"No available slots for {date}"
        
        return ExecutionResult(
            success=True,
            message=message,
            data={"available_slots": available_slots, "date": date}
        )
    
    def _execute_query_bookings(self, params: Dict[str, Any]) -> ExecutionResult:
        """Query user bookings"""
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        bookings = self._load_bookings()
        user_bookings = bookings.get("calendar", {}).get(date, [])
        
        if user_bookings:
            times = [b.get("time", "Unknown") for b in user_bookings]
            message = f"Your bookings for {date}: {', '.join(times)}"
        else:
            message = f"No bookings found for {date}"
        
        return ExecutionResult(
            success=True,
            message=message,
            data={"bookings": user_bookings, "date": date}
        )
    
    def _execute_system_open(self, params: Dict[str, Any]) -> ExecutionResult:
        """Execute system open command"""
        command = params.get("command", "").lower()
        target = params.get("target", "")
        
        system = platform.system().lower()
        
        try:
            if "browser" in command or "web" in command:
                if target:
                    webbrowser.open(target)
                    message = f"Opened {target} in browser"
                else:
                    webbrowser.open("https://www.google.com")
                    message = "Opened browser"
            
            elif "calculator" in command:
                if system == "windows":
                    subprocess.run(["calc.exe"], check=True)
                elif system == "darwin":  # macOS
                    subprocess.run(["open", "-a", "Calculator"], check=True)
                else:  # Linux
                    subprocess.run(["gnome-calculator"], check=True)
                message = "Opened calculator"
            
            elif "notepad" in command or "text" in command:
                if system == "windows":
                    subprocess.run(["notepad.exe"], check=True)
                elif system == "darwin":
                    subprocess.run(["open", "-a", "TextEdit"], check=True)
                else:
                    subprocess.run(["gedit"], check=True)
                message = "Opened text editor"
            
            elif "file" in command and target:
                if os.path.exists(target):
                    if system == "windows":
                        subprocess.run(["explorer", target], check=True)
                    elif system == "darwin":
                        subprocess.run(["open", target], check=True)
                    else:
                        subprocess.run(["xdg-open", target], check=True)
                    message = f"Opened {target}"
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"File or folder not found: {target}"
                    )
            
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Unknown open command: {command}"
                )
            
            return ExecutionResult(success=True, message=message)
            
        except subprocess.CalledProcessError as e:
            return ExecutionResult(
                success=False,
                message=f"Failed to open {command}: {str(e)}"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error executing system command: {str(e)}"
            )
    
    def _execute_system_control(self, params: Dict[str, Any]) -> ExecutionResult:
        """Execute system control commands"""
        command = params.get("command", "").lower()
        
        # For safety, we'll only provide information about system commands
        # rather than actually executing them
        system_commands = {
            "shutdown": "To shutdown the system",
            "restart": "To restart the system", 
            "sleep": "To put system to sleep",
            "hibernate": "To hibernate the system"
        }
        
        if command in system_commands:
            return ExecutionResult(
                success=True,
                message=f"For safety, I can't execute {command}. {system_commands[command]}"
            )
        else:
            return ExecutionResult(
                success=False,
                message=f"Unknown system command: {command}"
            )
    
    def _execute_create_ics(self, params: Dict[str, Any]) -> ExecutionResult:
        """Create ICS calendar file"""
        booking_data = params.get("booking_data", {})
        
        if not booking_data:
            return ExecutionResult(
                success=False,
                message="No booking data provided for ICS creation"
            )
        
        ics_file = self._generate_ics_file(booking_data)
        
        if ics_file:
            return ExecutionResult(
                success=True,
                message=f"Created ICS file: {ics_file}",
                files_created=[ics_file]
            )
        else:
            return ExecutionResult(
                success=False,
                message="Failed to create ICS file"
            )
    
    def _execute_send_notification(self, params: Dict[str, Any]) -> ExecutionResult:
        """Send system notification"""
        title = params.get("title", "AI Assistant")
        message = params.get("message", "")
        
        if not message:
            return ExecutionResult(
                success=False,
                message="No message provided for notification"
            )
        
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows toast notification
                subprocess.run([
                    "powershell", "-Command",
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.MessageBox]::Show('{message}', '{title}')"
                ], check=True)
            
            elif system == "darwin":  # macOS
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ], check=True)
            
            else:  # Linux
                subprocess.run([
                    "notify-send", title, message
                ], check=True)
            
            return ExecutionResult(
                success=True,
                message=f"Notification sent: {message}"
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Failed to send notification: {str(e)}"
            )
    
    def _ensure_storage_files(self):
        """Ensure storage files exist with default structure"""
        if not os.path.exists(self.slots_file):
            default_slots = {
                "start_time": "09:00",
                "end_time": "17:00",
                "slot_duration": 30,
                "break_duration": 0,
                "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            }
            with open(self.slots_file, "w", encoding="utf-8") as f:
                json.dump(default_slots, f, indent=2)
        
        if not os.path.exists(self.bookings_file):
            default_bookings = {"calendar": {}}
            with open(self.bookings_file, "w", encoding="utf-8") as f:
                json.dump(default_bookings, f, indent=2)
    
    def _load_bookings(self) -> Dict[str, Any]:
        """Load bookings from file"""
        try:
            with open(self.bookings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"calendar": {}}
    
    def _save_bookings(self, bookings: Dict[str, Any]):
        """Save bookings to file"""
        with open(self.bookings_file, "w", encoding="utf-8") as f:
            json.dump(bookings, f, indent=2)
    
    def _save_booking(self, booking_data: Dict[str, Any]) -> bool:
        """Save a single booking"""
        try:
            bookings = self._load_bookings()
            date = booking_data["date"]
            
            if "calendar" not in bookings:
                bookings["calendar"] = {}
            
            if date not in bookings["calendar"]:
                bookings["calendar"][date] = []
            
            bookings["calendar"][date].append(booking_data)
            self._save_bookings(bookings)
            return True
            
        except Exception as e:
            print(f"Error saving booking: {e}")
            return False
    
    def _get_available_slots(self, date: str) -> List[str]:
        """Get available slots for a date"""
        # Load slot configuration
        try:
            with open(self.slots_file, "r", encoding="utf-8") as f:
                slots_config = json.load(f)
        except Exception:
            # Default configuration
            slots_config = {
                "start_time": "09:00",
                "end_time": "17:00",
                "slot_duration": 30
            }
        
        # Generate all possible slots
        all_slots = self._generate_time_slots(slots_config)
        
        # Get booked slots
        bookings = self._load_bookings()
        booked_slots = set()
        
        for booking in bookings.get("calendar", {}).get(date, []):
            booked_slots.add(booking.get("time"))
        
        # Return available slots
        return [slot for slot in all_slots if slot not in booked_slots]
    
    def _generate_time_slots(self, config: Dict[str, Any]) -> List[str]:
        """Generate time slots based on configuration"""
        start_time = config.get("start_time", "09:00")
        end_time = config.get("end_time", "17:00")
        slot_duration = config.get("slot_duration", 30)
        
        slots = []
        start_hour, start_min = map(int, start_time.split(":"))
        end_hour, end_min = map(int, end_time.split(":"))
        
        current_hour = start_hour
        current_min = start_min
        
        while (current_hour < end_hour) or (current_hour == end_hour and current_min < end_min):
            slots.append(f"{current_hour:02d}:{current_min:02d}")
            
            current_min += slot_duration
            if current_min >= 60:
                current_min = 0
                current_hour += 1
        
        return slots
    
    def _generate_ics_file(self, booking_data: Dict[str, Any]) -> Optional[str]:
        """Generate ICS calendar file"""
        try:
            date = booking_data["date"]
            time = booking_data["time"]
            booking_id = booking_data.get("booking_id", f"{date}_{time.replace(':', '')}")
            
            # Parse date and time
            year, month, day = map(int, date.split("-"))
            hour, minute = map(int, time.split(":"))
            
            # Create datetime objects
            start_dt = datetime(year, month, day, hour, minute)
            end_dt = start_dt.replace(minute=minute + 30)  # 30-minute slot
            
            # Generate ICS content
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Assistant//Booking System//EN
BEGIN:VEVENT
UID:{booking_id}@aiassistant.local
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:Booked Slot - {time}
DESCRIPTION:AI Assistant booking for {date} at {time}
LOCATION:AI Assistant System
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
            
            # Save to file
            filename = f"booking_{booking_id}.ics"
            filepath = os.path.join(self.storage_path, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(ics_content)
            
            return filepath
            
        except Exception as e:
            print(f"Error generating ICS file: {e}")
            return None

