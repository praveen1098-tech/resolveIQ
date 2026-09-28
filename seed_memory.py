import json
from memory_store import retain_incident

def load_seeds():
    try:
        with open("data/seed_incidents.json", "r") as f:
            incidents = json.load(f)
        for inc in incidents:
            retain_incident(
                service=inc["service"],
                symptom=inc["symptom"],
                root_cause=inc["root_cause"],
                resolution=inc["resolution"],
                incident_id=inc["incident_id"]
            )
        print("✅ Seed incidents successfully loaded into Hindsight.")
    except Exception as e:
        print(f"Error loading seeds: {e}")

if __name__ == "__main__":
    load_seeds()
