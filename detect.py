import cv2
from supabase import create_client, Client
from ultralytics import YOLO
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()
# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# YOLOv8 model
model = YOLO("yolov8n.pt")  # You can also try yolov8s.pt

# Room config
ROOM_NAME = "Room A"
CAMERA_ID = 0  # change to 1, 2, or stream URL for other rooms
DETECTION_INTERVAL = 10  # seconds between uploads

def detect_people_yolo(frame):
    results = model(frame, verbose=False)
    people = [det for det in results[0].boxes.cls if int(det) == 0]  # class 0 = person
    return len(people)

def send_to_supabase(status):
    response = supabase.table("classroom_status").insert({
        "room_name": ROOM_NAME,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()
    print("📡 Sent to Supabase:", response)

def main():
    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("❌ Camera not working")
        return

    print("✅ ClasUtil YOLOv8 AI started. Press 'q' to quit.")

    last_sent = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        people_count = detect_people_yolo(frame)
        status = "occupied" if people_count > 0 else "empty"

        # display
        cv2.putText(frame, f"{ROOM_NAME} - {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0) if status == "occupied" else (0, 0, 255), 2)
        cv2.imshow("ClasUtil Monitor", frame)

        # send to Supabase every N seconds
        if time.time() - last_sent > DETECTION_INTERVAL:
            send_to_supabase(status)
            last_sent = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
