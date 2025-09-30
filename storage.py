import json
import os
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta


class BookingStorage:
    def __init__(self, bookings_file: str, slots_file: str) -> None:
        self.bookings_file = bookings_file
        self.slots_file = slots_file
        self._ensure_files()

    def _ensure_files(self) -> None:
        # Keep a simple config for slots in slots_file (start, count, stepMinutes)
        if not os.path.exists(self.slots_file):
            with open(self.slots_file, "w", encoding="utf-8") as f:
                json.dump({
                    "start_time": "10:00",   # day start
                    "slot_count": 6,          # total slots per day
                    "slot_step_minutes": 30   # 30 minutes per slot
                }, f, indent=2)
        if not os.path.exists(self.bookings_file):
            with open(self.bookings_file, "w", encoding="utf-8") as f:
                json.dump({"calendar": {}}, f, indent=2)

    def _read_json(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_json(self, path: str, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _generate_daily_slots(self) -> List[str]:
        cfg = self._read_json(self.slots_file) or {}
        start_str = cfg.get("start_time", "10:00")
        slot_count = int(cfg.get("slot_count", 6))
        step_minutes = int(cfg.get("slot_step_minutes", 30))
        start_h, start_m = [int(x) for x in start_str.split(":")]
        today = datetime.now().date()
        cursor = datetime(today.year, today.month, today.day, start_h, start_m)
        out: List[str] = []
        for _ in range(slot_count):
            out.append(cursor.strftime("%H:%M"))
            cursor += timedelta(minutes=step_minutes)
        return out

    def get_available_slots(self, date_str: str) -> List[str]:
        all_slots = self._generate_daily_slots()
        booked = {b["time"] for b in self.get_bookings(date_str)}
        return [s for s in all_slots if s not in booked]

    def get_bookings(self, date_str: str) -> List[Dict[str, Any]]:
        data = self._read_json(self.bookings_file) or {}
        cal = data.get("calendar", {})
        return list(cal.get(date_str, []))

    def book_first_available(self, date_str: str) -> Tuple[bool, str, Dict[str, Any] | None]:
        slots = self.get_available_slots(date_str)
        if not slots:
            return False, "No available slots left.", None
        desired = slots[0]
        return self.book_specific_slot(date_str, desired)

    def book_specific_slot(self, date_str: str, time_str: str) -> Tuple[bool, str, Dict[str, Any] | None]:
        time_str = time_str.strip()
        slots = self.get_available_slots(date_str)
        if time_str not in slots:
            return False, f"Slot {time_str} is not available.", None
        data = self._read_json(self.bookings_file) or {}
        cal = data.get("calendar", {})
        day_bookings = list(cal.get(date_str, []))
        booking = {"time": time_str}
        day_bookings.append(booking)
        cal[date_str] = day_bookings
        data["calendar"] = cal
        self._write_json(self.bookings_file, data)
        return True, f"Booked {time_str} successfully.", booking



