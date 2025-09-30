import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from typing import List, Dict, Any

from storage import BookingStorage
from nlp import EnhancedNLU
from planner import DecisionPlanner
from executor import ActionExecutor
from utils import generate_ics_content


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize AI components
    nlu = EnhancedNLU(use_spacy=True)
    planner = DecisionPlanner(storage_path=data_dir)
    executor = ActionExecutor(storage_path=data_dir)
    
    # Legacy storage for backward compatibility
    storage = BookingStorage(
        bookings_file=os.path.join(data_dir, "bookings.json"),
        slots_file=os.path.join(data_dir, "slots.json"),
    )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/process", methods=["POST"])
    def process():
        payload = request.get_json(silent=True) or {}
        user_text: str = (payload.get("text") or "").strip()
        lang: str = (payload.get("lang") or "en-US").strip()
        user_id: str = (payload.get("user_id") or "web_user").strip()
        
        if not user_text:
            return jsonify({"reply": "Please say something.", "intent": "unknown"})

        try:
            # Step 1: Parse intent and extract entities using enhanced NLU
            intent = nlu.parse_intent(user_text, lang=lang)
            
            # Step 2: Plan actions based on intent
            actions, response_text = planner.process_intent(
                user_id, intent.name, intent.entities, intent.confidence, user_text
            )
            
            # Step 3: Execute planned actions
            execution_results = []
            for action in actions:
                if not action.requires_confirmation:
                    result = executor.execute_action(action.name, action.parameters)
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
            
            # Check for ICS files in execution results
            ics_content = None
            for result in execution_results:
                if result.get("data", {}).get("files_created"):
                    for file_path in result["data"]["files_created"]:
                        if file_path.endswith(".ics"):
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    ics_content = f.read()
                                break
                            except:
                                pass
            
            response = {
                "reply": final_response,
                "intent": intent.name,
                "confidence": intent.confidence,
                "entities": intent.entities,
                "actions": [{"name": a.name, "parameters": a.parameters, "requires_confirmation": a.requires_confirmation} for a in actions],
                "execution_results": execution_results
            }
            
            if ics_content:
                response["ics"] = ics_content
            
            return jsonify(response)
            
        except Exception as e:
            print(f"Error processing request: {e}")
            return jsonify({
                "reply": "Sorry, I encountered an error processing your request.",
                "intent": "error",
                "error": str(e)
            })

    @app.route("/slots", methods=["GET"])
    def get_slots():
        date_str = (request.args.get("date") or "").strip()
        if not date_str:
            date_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        return jsonify({"date": date_str, "available_slots": storage.get_available_slots(date_str)})

    @app.route("/bookings", methods=["GET"])
    def get_bookings():
        date_str = (request.args.get("date") or "").strip()
        if not date_str:
            date_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        return jsonify({"date": date_str, "bookings": storage.get_bookings(date_str)})

    @app.route("/book", methods=["POST"])
    def book_specific():
        payload = request.get_json(silent=True) or {}
        desired_time: str = (payload.get("time") or "").strip()
        date_str: str = (payload.get("date") or "").strip()
        if not date_str:
            date_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        if not desired_time:
            return jsonify({"success": False, "message": "Please provide a time like 11:00"}), 400
        success, message, booking = storage.book_specific_slot(date_str, desired_time)
        response: Dict[str, Any] = {"success": success, "message": message}
        if success and booking:
            response["booking"] = booking
            response["ics"] = generate_ics_content(booking["time"], title="Booked Slot", date_str=date_str)
        return jsonify(response)

    # Serve robots.txt or favicon if present
    @app.route('/robots.txt')
    def robots():
        return send_from_directory(app.static_folder, 'robots.txt')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico')

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)



