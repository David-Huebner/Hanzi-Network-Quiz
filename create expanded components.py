import json
import pandas as pd
from itertools import product

def build_tree(char_key, data, visited=None):
    """
    Recursively builds a decomposition tree as a nested dictionary.
    
    char_key: The key in the JSON database
    data: The JSON database
    visited: Keeps track of visited nodes to avoid infinite loops
    """
    if visited is None:
        visited = set()

    if char_key in visited:
        return f"{char_key} (circular)"
    visited.add(char_key)
    #print(char_key)

    primary_components = data[char_key]["primary_components"]

    # Atomic character: just return its name
    if len(primary_components) == 1 and primary_components[0] == [char_key]:
        return {}#char_key
    
    # Recursive decomposition
    tree = {}
    # Take the first group of components
    for component in primary_components[0]:
        tree[component] = build_tree(component, data, visited.copy())
    
    return tree

def flatten(lst):
    """Simple flatten: list of lists -> flat list"""
    return [x for sub in lst for x in sub]

# Pretty printing of decomposition tree
def print_tree(tree, indent=0):
    for key in tree.keys():
        print("    " * indent + key)
        if isinstance(tree[key], dict) and len(tree[key]) > 1:
            print_tree(tree[key], indent + 1)

def expand(node):
    """
    Expand a forest (dict of one or more nodes) into all valid descriptions.
    A valid description is a flattened list of labels where each node is either:
      - kept as-is, or
      - replaced by the expansions of ALL its children (chosen from one group if there are multiple).
    Tree conventions:
      - Forest: {name: children, ...}
      - children:
          {} or non-dict -> leaf
          {child_name: child_children, ...} -> single component group (AND of children)
          [ { ... }, { ... }, ... ] -> multiple alternative component groups (OR of groups)
    Returns: list[list[str]]
    """

    def is_leaf(children):
        return not isinstance(children, dict) and not isinstance(children, list) or \
               (isinstance(children, dict) and len(children) == 0)

    def expand_forest(forest):
        """Expand a forest (dict of siblings) -> list of flattened lists."""
        if not forest:
            return [[]]
        per_sibling = [expand_node(name, children) for name, children in forest.items()]
        combos = []
        for combo in product(*per_sibling):
            # combo is like [[...expansion of sib1...], [...expansion of sib2...], ...]
            flat = [token for part in combo for token in part]
            combos.append(flat)
        return combos

    def expand_node(name, children):
        """Expand a single node -> list of flattened lists."""
        # Option 1: keep this node
        keep = [[name]]

        # Leaf -> only keep-self
        if is_leaf(children):
            return keep

        # Non-leaf -> Option 2: replace by children expansions
        # Children may be:
        #   - dict (single group of children; AND them)
        #   - list of dicts (multiple alternative groups; OR across them)
        replace = []

        if isinstance(children, dict):
            # Single group
            replace = expand_forest(children)
        elif isinstance(children, list):
            # Multiple groups (alternatives): union of each group's forest expansion
            for group in children:
                replace.extend(expand_forest(group))
        else:
            # Any other unexpected type -> treat as leaf
            return keep

        # keep + replace
        return keep + replace

    # node can be a single-node dict or a forest; treat uniformly as forest
    results = expand_forest(node)

    # (Optional) deduplicate results while preserving order
    seen, deduped = set(), []
    for lst in results:
        t = tuple(lst)
        if t not in seen:
            seen.add(t)
            deduped.append(lst)
    return deduped

def unique_answers(answers):
    """Remove duplicates and return sorted unique expansions."""
    # use tuple to make them hashable
    unique = {tuple(ans) for ans in answers}
    # back to list of lists
    deduped = [list(ans) for ans in unique]
    # sort by length first, then lexicographically
    deduped.sort(key=lambda x: (len(x), x))
    return deduped




filename = "database.json" #Database name

Sequenz_limit = 1347 # Heisig Sequenz up to which secondary answers are build. Above it secondary = primary = components_backup

with open(filename, "r", encoding="utf-8") as f:
    database = json.load(f)

decomposition_trees = {}

for key, entry in database.items():
    if key == "particle:walking stick":
        1 == 1
    if int(entry["Sequenz"]) >= Sequenz_limit:
        entry["primary_components"] = entry["components_backup"]
        entry["expanded_components"] = entry["components_backup"]
        continue
    primary_components = entry.get("primary_components",[])
    primary_components_flatten = flatten(primary_components)
    # Extract all keywords inside keyword:"..." or hanzi:...
    if len(primary_components) == 1 and primary_components[0] == [key]:
        print(key)
        entry["expanded_components"] = entry["primary_components"]
        continue  # Skip atomic characters

    tree = build_tree(key, database)
    decomposition_trees[key] = tree

    # Generate all possible answers
    all_answers = expand(tree)
    all_answers = unique_answers(all_answers)
    """
    print("---------------------")
    print(key)
    print("---------------------")
    print_tree(tree)
    print("list of possible answers")
    print(all_answers)
    """
    entry["expanded_components"] = all_answers


with open(filename, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

