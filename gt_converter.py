"""
The json file is created not from our app
Only the nodules without "verified nodule" is the ground truth
The main job of this program is to add verified info to every ground truth nodule, so that the sigmaLU_evaluation can
apply on these files
"""
import json
import os
import io
import sys
pyVersion = 3

# for the encoding issue, use io.open on python 2
if sys.version_info[0] == 2:
    pyVersion = 2
    from io import open

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f
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

class DuplicateDict(dict):
    """
    to dump duplicate key(item) json
    Borrowed from Chunbo, Modified by Siqi to be compatible on both python 2 and 3
    """
    def __init__(self, data):
        self['who'] = '12sigma'     # need to have something in the dictionary
        self._data = data
        self._items = []
    # for python 3, the internal JSON encoder calls items
    def items(self):
        for key, value in self._data.items():
            if key != 'item':
                if isinstance(value, dict):
                    self._items.append((key, DuplicateDict(value)))
                else:
                    self._items.append((key, value))
            else:
                for vv in value:
                    self._items.append((key, vv))
        return self._items

    # for python 2, the internal JSON encoder calls __iter__ and __getitem__
    def __getitem__(self, key):
        return self._value

    def __iter__(self):
        def generator():
            for key, value in self._data.items():
                if isinstance(value, list) and key == 'item':
                    for i in value:
                        if isinstance(i, dict):
                            self._value = DuplicateDict(i)
                        else:
                            self._value = i
                        yield key
                elif isinstance(value, dict):
                    self._value = DuplicateDict(value)
                    yield key
                else:
                    self._value = value
                    yield key

        return generator()


class AddVerifiedNodule:
    def __init__(self, original_path, target_path, original_extension, target_extension):
        self.original_path = original_path
        self.target_path = target_path
        self.original_extension = original_extension
        self.target_extension = target_extension

        # if the target path doesn't exit, create one
        if not os.path.isdir(self.target_path):
            os.mkdir(self.target_path)

        # a list of original json files
        self.original_files = listdir_nohidden(original_path)

    def addVerified(self):
        for original_file in self.original_files:
            # read in the original json file
            # original_filename = self.original_path + self.filename + self.original_extension
            # print self.original_path + original_file
            print (self.original_path + original_file)
            original_json = json.loads(open(self.original_path + original_file).read(), object_pairs_hook=join_duplicate_keys)

            # if it is a positive nodule, it won't have verified info, add verified info for the ground truth so that we
            # can apply general json parser on the ground truth
            i = 0
            while i < len(original_json["Nodules"]["item"]):
                # print i
                if "VerifiedNodule" not in original_json["Nodules"]["item"][i]:
                    # print i
                    original_json["Nodules"]["item"][i]["VerifiedNodule"] = {"labelIndex": "0", "Center0": "0",
                                                                             "Center1": "0", "Center1": "0", "Center2":
                                                                             "0", "True": "true", "Malign": "false",
                                                                             "Solid": "true", "GGO": "false", "Mixed":
                                                                                 "false" , "Calc": "false"}
                    i += 1
                else:
                    original_json["Nodules"]["item"].pop(i)
            count = len(original_json["Nodules"]["item"])
            original_json["Nodules"]["count"] = count
            # output to new json files
            target_filename = self.target_path + original_file[:-5] + self.target_extension
            # target_json = pretty_json(json.dumps(DuplicateDict(original_json), ensure_ascii=False).encode('utf-8'))
            with io.open(target_filename, 'w', encoding='utf8') as outfile:
                str_ = json.dumps(DuplicateDict(original_json), indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
                outfile.write(str_)
                outfile.close()
# json_str = pretty_json(json.dumps(DuplicateDict(json_reproduce), ensure_ascii=False).encode('utf-8'))
#             file_reproduce = self._path_reproduce + name + self._postfix_target
#             with open(file_reproduce, 'w', encoding='utf-8') as f:
#                 f.write(json_str)
#                 f.close()
#             print(name + ' Done')

if __name__ == "__main__":
    original_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/label/"
    target_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/label_new/"
    original_extension = ".json"
    target_extension = "_new.json"
    test = AddVerifiedNodule(original_path, target_path, original_extension, target_extension)
    test.addVerified()


