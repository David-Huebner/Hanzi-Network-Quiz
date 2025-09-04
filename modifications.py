import json
import pandas as pd

#All purpose script for manipulating the database


filename = "database.json"

def clean_water(database):
    modified = []

    for key, entry in database.items():
        components = entry.get("components", [])
        # Flatten components for checking
        flat_comps = [c for group in components for c in group]

        if "particle:ice" in flat_comps and "water" in flat_comps:
            # Remove all "water" from each component group
            entry["components"] = [[c for c in group if c != "water"] for group in components]
            modified.append(key)

    return modified

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

def normalize_components2(database):
    modified = []

    for key, entry in database.items():
        comps = entry.get("components", [])
        if comps == []:
            entry["components"] = entry.get("primary_components",[])
        elif type(entry["components"]) == str:
            entry["components"] = [entry["components"]]
        else:
            # Check if it's a flat list of strings (not a list of lists)
            if comps and all(isinstance(c, str) for c in comps):
                entry["components"] = [comps]  # wrap into another list
                modified.append(key)

    return modified

def normalize_components3(database):
    modified = []

    for key, entry in database.items():
        comps = entry.get("primary_components", [])
        # Check if it's a flat list of strings (not a list of lists)
        if comps and all(isinstance(c, str) for c in comps):
            entry["primary_components"] = [comps]  # wrap into another list
            modified.append(key)

    return modified


def normalize_components4(database):
    modified = []
    for key, entry in database.items():
        if "components" in entry:
            del entry["components"]
        if "secondary_components_backup" in entry:
            del entry["secondary_components_backup"]
        if "secondary_components" in entry:
            del entry["secondary_components"]

    return modified


def normalize_components5(database):
    modified = []
    for key, entry in database.items():
        isHanzi = entry.get("isHanzi", True)
        comps = entry.get("primary_components", [])
        # Check if it's a flat list of strings (not a list of lists)
        if comps == [] and isHanzi == False:
            entry["primary_components"] = [[key]]  # wrap into another list
            modified.append(key)
    return modified

def search(database):
    found = []
    for key, entry in database.items():
        comps = entry.get("expanded_components", [])
        if not comps:
            found.append(key)
    return found


def flatten(xss):
    return [x for xs in xss for x in xs]

def check_missing_decompositions(database):
    missing_decompositions = []

    for key, entry in database.items():
        comps = entry.get("primary_components", [])
        # Check if it's a flat list of strings (not a list of lists)
        if len(flatten(comps)) == 1 and flatten(comps)[0] != key:
            missing_decompositions.append(key)

    return missing_decompositions


with open(filename, "r", encoding="utf-8") as f:
    database = json.load(f)



column_names = ["Simplified","Components",  "Traditional", "Number", "Sequenz", "Keyword","notes", "ComponentsSearch",
                "Story", "Stroke Count", "Pinyin","InMyVocab", "Words", "audio", "common_rank"]

path = "particles.txt"

# Read CSV
df = pd.read_csv(path, sep="\t",index_col=False, dtype=str, keep_default_na=False,skiprows=2,names=column_names)
"""
for i in range(len(df)):
    hanzi = df.at[i, "Simplified"]
    keyword = df.at[i, "Keyword"].lower()
    if keyword.startswith("p."):
        keyword = keyword.replace("p.", "particle:")
    if keyword == "particle:umbrella":
        continue
    components = df.at[i, "Components"].lower()
    split_comp = [s.strip() for s in components.split(',')]
    for j in range(len(split_comp)):
        if split_comp[j].startswith("p."):
            split_comp[j] = split_comp[j].replace("p.", "particle:")
    b = keyword
    for a in split_comp:
        changed = deep_clean(database,a,b)
"""

"""
for i in range(len(df)):
    hanzi = df.at[i, "Simplified"]
    keyword = df.at[i, "Keyword"].lower()
    if keyword.startswith("p."):
        keyword = keyword.replace("p.", "particle:")
    if keyword == "particle:umbrella":
        continue
    comps = database[keyword]["components"]
    if comps == []:
        continue
    b = keyword
    #print(b)
    for a in comps[0]:
        #print(a)
        changed = deep_clean(database,a,b)
        print("✅ Split primary/secondary components for:", changed)


"""


a = "half"
b = "particle:quarter"

a = "bow (n.) (weapon)"
b = "particle:snare"

a = "bow (n.) (weapon)"
b = "particle:snare"

a = "bow (n.) (weapon)"
b = "particle:slingshot"

a = "particle:a drop of"
b = "particle:maestro"

a = "particle:elbow"
b = "particle:thread"

a = "particle:cocoon"
b = "particle:floss"

a = "particle:stamp"
b = "particle:chop"

a = "particle:stamp"
b = "particle:fingerprint"

a = "particle:salad"
b = "particle:wire mesh"

a = "particle:flower"
b = "particle:hamster cage"

a = "soil"
b = "particle:grow up"

a = "particle:grow up"
b = "plentiful"

a = "particle:grow up"
b = "particle:bonsai"

a = "plentiful"
b = "particle:cornstalk"

a = "particle:a drop of"
b = "small"

a = "small"
b = "few"

a = "month"
b = "evening"

a = "evening"
b = "many"

a = "particle:arrow"
b = "halberd"

a = "particle:mending"
b = "particle:zoo"

a = "correct"
b = "particle:zoo"

a = "one"
b = "particle:zoo"

a = "stop (v.)"
b = "particle:zoo"



#changed = clean_doubles(database,a,b)
#changed = clean_obsoletes(database)
#changed = remove_duplicate_component_groups(database)

#changed = split_primary_secondary(database)

a = "one"
b = "particle:hamster cage"

#changed = deep_clean(database,a,b)

found = search(database)

print("found:", found)


#with open(filename, "w", encoding="utf-8") as f:
#    json.dump(database, f, ensure_ascii=False, indent=2)

