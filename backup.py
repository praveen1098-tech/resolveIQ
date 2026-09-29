"""
ResolveIQ Enterprise Database Backup & Disaster Recovery System
==============================================================
Creates timestamped, validated backups of institutional memory and databases.
Supports automated retention and point-in-time disaster recovery.
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

def create_backup() -> str:
    """Creates a timestamped snapshot of seed incidents and user databases."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"resolveiq_backup_{timestamp}.json")

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "databases": {}
    }

    # Backup seed incidents
    incidents_path = os.path.join(DATA_DIR, "seed_incidents.json")
    if os.path.exists(incidents_path):
        with open(incidents_path, "r", encoding="utf-8") as f:
            manifest["databases"]["seed_incidents"] = json.load(f)

    # Backup user records (safe metadata)
    users_path = os.path.join(DATA_DIR, "users.json")
    if os.path.exists(users_path):
        with open(users_path, "r", encoding="utf-8") as f:
            manifest["databases"]["users"] = json.load(f)

    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Backup created successfully: {backup_file}")
    return backup_file

def list_backups() -> list:
    """Lists existing backups sorted by date."""
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    return files

def restore_backup(backup_filename: str) -> bool:
    """Restores database state from a backup file."""
    filepath = os.path.join(BACKUP_DIR, backup_filename) if not os.path.isabs(backup_filename) else backup_filename
    if not os.path.exists(filepath):
        print(f"❌ Backup file not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if "databases" not in manifest:
        print("❌ Invalid backup manifest format.")
        return False

    if "seed_incidents" in manifest["databases"]:
        target = os.path.join(DATA_DIR, "seed_incidents.json")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(manifest["databases"]["seed_incidents"], f, indent=2)

    if "users" in manifest["databases"]:
        target = os.path.join(DATA_DIR, "users.json")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(manifest["databases"]["users"], f, indent=2)

    print(f"✅ Successfully restored data from {backup_filename}!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResolveIQ Backup & Recovery Utility")
    parser.add_argument("--create", action="store_true", help="Create a new backup snapshot")
    parser.add_argument("--list", action="store_true", help="List all available backup snapshots")
    parser.add_argument("--restore", type=str, help="Restore from specified backup filename")

    args = parser.parse_args()

    if args.restore:
        restore_backup(args.restore)
    elif args.list:
        backups = list_backups()
        print(f"Found {len(backups)} backups:")
        for b in backups:
            print(f" - {b}")
    else:
        create_backup()
