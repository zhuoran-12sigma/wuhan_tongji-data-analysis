"""
The json file is created not from our app
Only the nodules without "verified nodule" is the ground truth
The main job of this program is to add verified info to every ground truth nodule, so that the sigmaLU_evaluation can
apply on these files
"""
import json
import csv
import io
from collections import defaultdict

try:
    to_unicode = unicode
except NameError:
    to_unicode = str
PYTHONIOENCODING='utf-8'
# function to solve the problem of duplicated key ("item") in json files
def join_duplicate_keys(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            if type(d[k]) == list:
                d[k].append(v)
            else:
                newlist = []
                newlist.append(d[k])
                newlist.append(v)
                d[k] = newlist
        else:
            d[k] = v
    return d


suffix = ".json"
filename = "gt" + suffix
jsonfile = json.loads(open(filename).read(), object_pairs_hook=join_duplicate_keys)

for item in jsonfile["Nodules"]["item"]:
    if "VerifiedNodule" not in item:
        item["VerifiedNodule"] = {"labelIndex": "0", "Center0": "0", "Center1": "0", "Center1": "0", "Center2": "0",
                                  "True": "True", "Malign": "false", "Solid": "false", "GGO": "false", "Mixed": "false"
            , "Calc": "false"}

with io.open("new1" + ".json", 'w', encoding='utf8') as outfile:
    str_ = json.dumps(jsonfile, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
    outfile.write(to_unicode(str_))

