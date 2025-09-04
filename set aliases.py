
import json
import shutil
import os
i = 0

# Load your JSON file
filename = "database.json"
backup_filename = filename + ".bak"
progress_file = "progress.json"

# Make a backup before overwriting
shutil.copy(filename, backup_filename)
print(f"📂 Backup created: {backup_filename}")

with open(filename, "r", encoding="utf-8") as f:
    data = json.load(f)


Sequenz_limit = 1347 # Limit up to which i aliases are added


# Load progress
start_index = 0
if os.path.exists(progress_file):
    with open(progress_file, "r", encoding="utf-8") as pf:
        progress = json.load(pf)
        start_index = progress.get("last_index", 0)
        print(f"▶️ Resuming from index {start_index}")

# Step 1: Collect all component references
used_components = set()
for entry in data.values():
    for comp_group in entry.get("primary_components", []):
        for comp in comp_group:
            used_components.add(comp)

# Step 2: Only check elements that appear in components elsewhere
keys = list(data.keys())
i = start_index
while i < len(keys) and i<Sequenz_limit:
    key = keys[i]
    entry = data[key]

    if key not in used_components:
        print(f"⏩ Skipping {key} (not used as a component)")
        i += 1
        continue

    print(f"Word: {key}")
    print(f"Hanzi: {entry['hanzi']}")
    print(f"Current Aliases: {entry.get('Aliases', [])}")
    
    user_input = input("Enter aliases (comma-separated), 'redo' to repeat, or Enter to skip: ").strip()

    if user_input.lower() == "redo":
        print("🔄 Redo requested. Will repeat this entry next time.")
        # Move progress back one step (but not below 0)
        i = max(i - 2, 0)
        with open(progress_file, "w", encoding="utf-8") as pf:
            json.dump({"last_index": i}, pf)
        break  # Exit so next run starts at this element again

    elif user_input.lower().startswith("new: "):
        new_value = user_input[5:].strip()
        if new_value:
            entry["Aliases"] = [new_value]
            print(f"🆕 Aliases overwritten: {entry['Aliases']}")
        else:
            print("⚠️ No value provided after 'new:', skipping.")

    elif user_input:
        aliases_list = [alias.strip() for alias in user_input.split(",") if alias.strip()]
        entry["Aliases"].extend(aliases_list)
        print(f"✅ Updated Aliases: {entry['Aliases']}")
    else:
        print("Skipped.")

    print("-" * 40)

    # Save progress and data after each step
    i += 1
    with open(progress_file, "w", encoding="utf-8") as pf:
        json.dump({"last_index": i}, pf)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Progress saved in {progress_file}, file updated: {filename}")
