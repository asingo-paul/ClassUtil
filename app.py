from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

def get_latest_status(filters=None):
    response = supabase.table("classroom_status")\
        .select("*")\
        .order("timestamp", desc=True)\
        .limit(500)\
        .execute()

    all_data = response.data if response.data else []

    seen = {}
    for entry in all_data:
        room = entry["room_name"]

        # Ensure only latest entry per room
        if room not in seen:
            # Filtering logic
            if filters:
                if filters.get("building") and filters["building"].lower() not in entry.get("building", "").lower():
                    continue
                if filters.get("floor") and filters["floor"].lower() not in entry.get("floor", "").lower():
                    continue
                if filters.get("class_type") and filters["class_type"].lower() not in entry.get("class_type", "").lower():
                    continue
                if filters.get("status") and filters["status"].lower() != entry.get("status", "").lower():
                    continue
            seen[room] = entry

    return list(seen.values())

@app.route('/')
def dashboard():
    filters = {
        "building": request.args.get("building"),
        "floor": request.args.get("floor"),
        "class_type": request.args.get("class_type"),
        "status": request.args.get("status"),
    }

    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}

    data = get_latest_status(filters)
    occupied_count = sum(1 for d in data if d['status'] == 'occupied')
    empty_count = sum(1 for d in data if d['status'] == 'empty')

    return render_template('dashboard.html',
                           data=data,
                           occupied_count=occupied_count,
                           empty_count=empty_count)

@app.route('/data')
def data():
    filters = {
        "building": request.args.get("building"),
        "floor": request.args.get("floor"),
        "class_type": request.args.get("class_type"),
        "status": request.args.get("status"),
    }

    filters = {k: v for k, v in filters.items() if v}
    all_data = get_latest_status(filters)

    grouped_data = {}
    for entry in all_data:
        room = entry["room_name"]
        grouped_data[room] = {
            "status": entry["status"],
            "timestamp": entry["timestamp"],
            "building": entry.get("building", ""),
            "floor": entry.get("floor", ""),
            "class_type": entry.get("class_type", "")
        }

    return jsonify(grouped_data)

if __name__ == '__main__':
    app.run(debug=True)
