# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24 13:15:51 2023

@author: David
"""
import re
import pandas as pd
from itertools import product
import json


def decompose(char, db):
    comps_list = db.get(char, [])
    
    # If no components → return leaf
    if not comps_list:
        return {char: {}}   # empty dict, not set
    
    elif len(comps_list) <= 2:
        # each component is a leaf
        return {c: {} for c in comps_list}
    else:
        minimal = []
        for c in comps_list:
            if any(c in db[other] for other in comps_list if other != c):
                continue
            else:
                minimal.append(c)
        return {a: decompose(a, db) for a in minimal}

# Pretty printing of decomposition tree
def print_tree(tree, indent=0):
    for key in tree.keys():
        print("    " * indent + key)
        if isinstance(tree[key], dict) and len(tree[key]) > 1:
            print_tree(tree[key], indent + 1)

def expand(node):
    """
    Recursively expand a node into all valid answer sets.
    Each node must either be kept as-is, or replaced entirely by expansions of its children.
    """
    results = []

    for key, children in node.items():
        if not children:  # leaf node
            return [[key]]

        # Option 1: keep this node
        keep_self = [[key]]

        # Option 2: expand all children
        child_expansions = [expand({c: g}) for c, g in children.items()]
        replace_self = []
        for prod in product(*child_expansions):
            replace_self.append([x for sublist in prod for x in sublist])

        # Combine both options
        node_expansions = keep_self + replace_self

        # If multiple keys at this level → combine their expansions
        if len(node) > 1:
            sibling_expansions = []
            for prod in product(*[expand({k: v}) for k, v in node.items()]):
                sibling_expansions.append([x for sublist in prod for x in sublist])
            return sibling_expansions
        else:
            return node_expansions
        
def unique_answers(answers):
    """Remove duplicates and return sorted unique expansions."""
    # use tuple to make them hashable
    unique = {tuple(ans) for ans in answers}
    # back to list of lists
    deduped = [list(ans) for ans in unique]
    # sort by length first, then lexicographically
    deduped.sort(key=lambda x: (len(x), x))
    return deduped


column_names = ["Simplified", "Traditional", "Number", "Sequenz", "Keyword","notes", "ComponentsSearch",
                "Story", "Stroke Count", "Pinyin","InMyVocab", "Words", "audio", "common_rank"]


path = "heisig.txt"

# Read CSV
df = pd.read_csv(path, sep="\t",index_col=False, dtype=str, keep_default_na=False,skiprows=2,names=column_names)
db = {}
all_chars_json = {}

for _, row in df.iterrows():
    keyword = row["Keyword"].lower()
    raw = row["ComponentsSearch"].lower()
    # Extract all keywords inside keyword:"..." or hanzi:...
    matches = re.findall(r'keyword:"([^"]+)"', raw)
    db[keyword] = matches

for i in range(len(df)):
    hanzi = df.at[i, "Simplified"]
    keyword = df.at[i, "Keyword"].lower()
    if keyword.startswith("p."):
        isHanzi = False
    else:
        isHanzi = True

    Sequenz = df.at[i, "Sequenz"]
    Number = df.at[i, "Number"]

    isActive = int(Sequenz)<1342 # cut off point for which characters to include

    decomp = decompose(keyword, db)

    # Generate all possible answers
    all_answers = expand(decomp)
    all_answers = unique_answers(all_answers)

    char_entry = {
        "hanzi": hanzi,
        "components": all_answers,
        "Aliases": [],
        "isHanzi": isHanzi,
        "isMarked": False,
        "dueIn": 0,
        "isDue": True,
        "wasSkipped": False,
        "isFalseNegative": False,
        "falseNegativeAnswer": [],
        "isActive": isActive,
        "Number": Number,
        "Sequenz": Sequenz,
    }

    all_chars_json[keyword] = char_entry

# Write entire database to JSON
with open("database_base.json", "w", encoding="utf-8") as f:
    json.dump(all_chars_json, f, ensure_ascii=False, indent=2)


