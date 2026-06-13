import json
import datetime

def generate_weekly_social_events():
    filepath = "data/definitions.json"
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Let's check existing timedSocialEventDefinitions
    events = data.get("timedSocialEventDefinitions", [])
    
    # We will plan weekly events for 1 year (52 weeks) starting from today
    start_date = datetime.datetime.now(datetime.timezone.utc)
    # Align start_date to nearest Monday or start immediately
    # We want weekly events
    current_time = start_date
    
    new_events = []
    
    # Typical orders: we can reuse or define template orders
    order_templates = [
        {"orderId": 1, "transaction": 16008},
        {"orderId": 2, "transaction": 16071},
        {"orderId": 3, "transaction": 16009},
        {"orderId": 4, "transaction": 16056},
        {"orderId": 5, "transaction": 16037},
        {"orderId": 6, "transaction": 16061},
        {"orderId": 7, "transaction": 16074},
        {"orderId": 8, "transaction": 16039},
        {"orderId": 9, "transaction": 16020}
    ]
    
    base_id = 45000
    for week in range(52):
        event_start = current_time + datetime.timedelta(weeks=week)
        # Event duration: e.g., 5 days (432000 seconds) or 7 days
        event_end = event_start + datetime.timedelta(days=6)
        
        start_ts = int(event_start.timestamp())
        finish_ts = int(event_end.timestamp())
        
        ev = {
            "finishTime": finish_ts,
            "id": base_id + week,
            "localizedKey": "TempTimedSocialEvent",
            "maxTeamSize": 4,
            "orders": order_templates,
            "rewardTransaction": 22,
            "startTime": start_ts
        }
        new_events.append(ev)
        
    data["timedSocialEventDefinitions"] = new_events
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {len(new_events)} weekly social events.")

if __name__ == "__main__":
    generate_weekly_social_events()
