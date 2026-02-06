import json
import random
from datetime import datetime

# File generation for user.json
def generate_user(i):
    return {
        "user_id": f"u_{i}",
        "signup_date": datetime.utcnow().isoformat(),
        "country": random.choice(["IN", "US", "EU", "AU"]),
        "device_type": random.choice(["mobile", "PC", "tablet"]),
        "marketing_source": random.choice(
            ["google_ads", "instagram_reels", "youtube"]
        )
    }

with open(r"C:\filepath\user.json", "w") as f:
    for i in range(1_000_000):
        f.write(json.dumps(generate_user(i)) + "\n")
      
# File generation for events.json      
def generate_event(i):
    return {
        "event_id": f"e_{i}",
        "user_id": f"u_{random.randint(1,200000)}",
        "event_type": random.choice(["product_view", "product_purchase"]),
        "product_id": f"p_{random.randint(1,50000)}",
        "event_timestamp": datetime.utcnow().isoformat(),
        "session_id": f"s_{random.randint(1,500000)}",
        "device_type": random.choice(["mobile", "PC", "tablet"])
    }

with open(r"C:\Users\mjahs\OneDrive\Desktop\events.json", "w") as f:
    for i in range(1_000_000):
        f.write(json.dumps(generate_event(i)) + "\n")
        

# File generation for orders.json      
def generate_order(i):
    return {
        "order_id": f"o_{i}",
        "user_id": f"u_{random.randint(1,200000)}",
        "product_id": f"p_{random.randint(1,50000)}",
        "order_amount": round(random.uniform(10, 30000), 2),
        "currency": "USD",
        "order_timestamp": datetime.utcnow().isoformat(),
        "payment_status": random.choice(["success", "failed", "in_progress"])
    }

with open(r"C:\Users\mjahs\OneDrive\Desktop\orders.json", "w") as f:
    for i in range(1_000_000):
        f.write(json.dumps(generate_order(i)) + "\n")

