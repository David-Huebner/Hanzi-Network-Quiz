import json
import shutil
import os

# File paths
filename = "database.json"
backup_filename = filename + ".bak"
progress_file = "progress.json"

# Make a backup before overwriting
if not os.path.exists(backup_filename):
    shutil.copy(filename, backup_filename)
    print(f"📂 Backup created: {backup_filename}")

# Load progress
if not os.path.exists(progress_file):
    print("❌ No progress.json found. Run the alias script first.")
    exit(1)

with open(progress_file, "r", encoding="utf-8") as pf:
    progress = json.load(pf)
    last_index = progress.get("last_index", 0)
    print(f"▶️ Last edited index: {last_index}")

# Load data
with open(filename, "r", encoding="utf-8") as f:
    data = json.load(f)

# Deactivate items beyond last_index
keys = list(data.keys())
for i, key in enumerate(keys):
    if i >= last_index:
        data[key]["isActive"] = False

# Save changes
with open(filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ All items from index {last_index} onward have isActive = false. Updated file: {filename}")
