import json
import pandas as pd
filename = "database.json"

#All purpose script for manipulating the database


def clean_doubles(database,a,b):
    modified = []

    for key, entry in database.items():
        components = entry.get("components", [])
        # Flatten components for checking
        flat_comps = [c for group in components for c in group]

        if a in flat_comps and b in flat_comps:
            # Remove all "water" from each component group
            entry["components"] = [[c for c in group if c != a] for group in components]
            modified.append(key)

    return modified

def clean_obsoletes(database):
    modified = []

    for key, entry in database.items():
        groups = entry.get("components", [])
        new_groups = []

        # Convert each group to a set for easy subset checking
        group_sets = [set(group) for group in groups]

        for i, g in enumerate(group_sets):
            # Check if there exists another group that strictly contains g
            redundant = any(g < other for j, other in enumerate(group_sets) if i != j)
            if not redundant:
                new_groups.append(groups[i])

        if len(new_groups) != len(groups):
            entry["components"] = new_groups
            modified.append(key)

    return modified


def remove_duplicate_component_groups(database):
    modified = []

    for key, entry in database.items():
        groups = entry.get("components", [])
        seen = set()
        new_groups = []

        for group in groups:
            # Use frozenset to ignore order (so ["a","b"] == ["b","a"])
            group_key = frozenset(group)
            if group_key not in seen:
                seen.add(group_key)
                new_groups.append(group)

        if len(new_groups) != len(groups):
            entry["components"] = new_groups
            modified.append(key)

    return modified

def split_primary_secondary(database):
    modified = []

    for key, entry in database.items():
        if entry.get("primary_components", []) != []:
            continue
        groups = entry.get("components", [])
        if not groups:
            continue

        # If only one sublist → make it primary
        if len(groups) == 1:
            entry["primary_components"] = groups[0]
            entry["secondary_components"] = []
            modified.append(key)
            continue

        # Find the shortest length
        min_len = min(len(g) for g in groups)
        shortest_groups = [g for g in groups if len(g) == min_len]

        if len(shortest_groups) == 1:
            # Exactly one shortest
            chosen = shortest_groups[0]
        else:
            # Multiple shortest: let user pick
            print(f"Hanzi: {entry['hanzi']} ({key})")
            for i, g in enumerate(shortest_groups, 1):
                print(f"  {i}: {g}")
            choice = None
            while choice is None:
                try:
                    inp = input(f"Choose primary [1-{len(shortest_groups)}]: ").strip()
                    idx = int(inp) - 1
                    if idx == 99:
                        return modified #quit early if 100 is entered
                    if 0 <= idx < len(shortest_groups):
                        choice = idx
                    else:
                        print("❌ Invalid choice, try again.")
                except ValueError:
                    print("❌ Please enter a number.")
            chosen = shortest_groups[choice]

        # Assign new properties
        entry["primary_components"] = chosen
        entry["secondary_components"] = [g for g in groups if g != chosen]
        modified.append(key)

    return modified

def deep_clean(database,a,b):
    changed = clean_doubles(database,a,b)
    changed2 = clean_obsoletes(database)
    changed3 = remove_duplicate_component_groups(database)
    return changed

def normalize_components(database):
    modified = []

    for key, entry in database.items():
        comps = entry.get("components", [])
        # Check if it's a flat list of strings (not a list of lists)
        if comps and all(isinstance(c, str) for c in comps):
            entry["components"] = [comps]  # wrap into another list
            modified.append(key)

    return modified

with open(filename, "r", encoding="utf-8") as f:
    database = json.load(f)


#changed = normalize_components(database)

#changed = clean_doubles(database,a,b)
#changed = clean_obsoletes(database)
#changed = remove_duplicate_component_groups(database)


a = "particle:horns"
b = "sheep"

#changed = deep_clean(database,a,b)

changed = split_primary_secondary(database)

print("✅ Split primary/secondary components for:", changed)


with open(filename, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

