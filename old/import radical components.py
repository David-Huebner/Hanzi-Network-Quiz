# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24 13:15:51 2023

@author: David
"""
import re
import pandas as pd
from itertools import product
import json

# File paths
filename = "database.json"

with open(filename, "r", encoding="utf-8") as f:
    database = json.load(f)

column_names = ["Simplified","Components",  "Traditional", "Number", "Sequenz", "Keyword","notes", "ComponentsSearch",
                "Story", "Stroke Count", "Pinyin","InMyVocab", "Words", "audio", "common_rank"]

path = "particles.txt"

# Read CSV
df = pd.read_csv(path, sep="\t",index_col=False, dtype=str, keep_default_na=False,skiprows=2,names=column_names)

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
    database[keyword]["components"] = split_comp

# Write entire database to JSON
with open(filename, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)


