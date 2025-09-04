import difflib
import json


#Search for suspicious leafs in the total character tree

def flatten(lst):
    """Simple flatten: list of lists -> flat list"""
    return [x for sub in lst for x in sub]


def format_typed(typed):
    if typed.startswith("p."):
        typed = typed.replace("p.","particle:")
    if typed == "drop" or typed == "particle:drop":
        typed = "particle:a drop of"
    return typed


def check_missing_decompositions(database):
    """
    Interactive check for suspicious leaves.
    """
    for key, entry in database.items():
        comps = entry.get("primary_components", [])
        if not comps:
            continue

        flat = flatten(comps)

        # suspicious case: single component that is not itself
        if len(flat) == 1 and flat[0] != key:
            hanzi = entry.get("hanzi", key)
            print(f"\n⚠ Suspicious leaf found: {hanzi} ({key})")
            print(f"   Current components: {comps}")

            while True:
                choice = input("Options: [L]eaf / [M]anual / [A]dd /[S]kip ? / [Q]uit or add the keyword if only one needs to be added ").strip().lower()
                typed = choice.strip()
                typed = format_typed(typed)
                if typed in database:
                    new_comps = [flat[0],typed]
                    entry["primary_components"] = [new_comps]
                    print(f"✅ Updated {key}: {entry['primary_components']}")
                    break

                elif choice == "l":
                    # Make it a true leaf
                    entry["primary_components"] = [[key]]
                    print(f"✅ Set {key} as a leaf: [[{key}]]")
                    break

                elif choice == "m":
                    new_comps = []
                    while True:
                        typed = input("Enter a component (blank to finish): ").strip()
                        typed = format_typed(typed)
                        if not typed:
                            break
                        if typed in database:
                            new_comps.append(typed)
                        else:
                            # Suggest closest matches
                            suggestions = difflib.get_close_matches(typed, database.keys(), n=3, cutoff=0.6)
                            print(f"❌ '{typed}' not found in database.")
                            if suggestions:
                                print("Did you mean:", ", ".join(suggestions))
                            continue
                    if new_comps:
                        entry["primary_components"] = [new_comps]
                        print(f"✅ Updated {key}: {entry['primary_components']}")
                    else:
                        print("⚠ No components entered, skipping.")
                    break

                elif choice == "s":
                    print("⏭ Skipped.")
                    break
                elif choice == "a":
                    print("add additional components")
                    new_comps = [flat[0]]
                    while True:
                        typed = input("Enter a component (blank to finish): ").strip()
                        typed = format_typed(typed)
                        if not typed:
                            break
                        if typed in database:
                            new_comps.append(typed)
                        else:
                            # Suggest closest matches
                            suggestions = difflib.get_close_matches(typed, database.keys(), n=3, cutoff=0.6)
                            print(f"❌ '{typed}' not found in database.")
                            if suggestions:
                                print("Did you mean:", ", ".join(suggestions))
                            continue
                    if new_comps:
                        entry["primary_components"] = [new_comps]
                        print(f"✅ Updated {key}: {entry['primary_components']}")
                    else:
                        print("⚠ No components entered, skipping.")
                    break
                elif choice == "q":
                    print("⏹ Quitting early. All previous changes have been saved.")
                    return  # exit the function immediately
                else:
                    print("❌ Invalid choice, try again.")


with open("database.json", "r", encoding="utf-8") as f:
    database = json.load(f)

check_missing_decompositions(database)

with open("database.json", "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

print("✅ Finished checking.")