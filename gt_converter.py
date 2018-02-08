"""
The json file is created not from our app
Only the nodules without "verified nodule" is the ground truth
The main job of this program is to add verified info to every ground truth nodule, so that the sigmaLU_evaluation can
apply on these files
"""
import json
import re
import os
import io

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

def pretty_json(s, step_size=4, multi_line_strings=False, advanced_parse=False, tab=False):
    # borrowed from Chunbo, convert a long string into a json format string
    out = ''
    step = 0
    in_marks = False  # Are we in speech marks? What character will indicate we are leaving it?
    escape = False  # Is the next character escaped?

    if advanced_parse:
        # \x1D (group seperator) is used as a special character for the parser
        # \0x1D has the same effect as a quote ('") but will not be ouputted
        # Can be used for special formatting cases to stop text being processed by the parser
        s = re.sub(r'datetime\(([^)]*)\)', r'datetime(\x1D\g<1>\x1D)', s)
        s = s.replace('\\x1D', chr(0X1D))  # Replace the \x1D with the single 1D character

    if tab:
        step_char = '\t'
        step_size = 1  # Only 1 tab per step
    else:
        step_char = ' '
    for c in s.decode('utf-8'):

        if step < 0:
            step = 0

        if escape:
            # This character is escaped so output it without looking at it
            escape = False
            out += c
        elif c in ['\\']:
            # Escape the next character
            escape = True
            out += c
        elif in_marks:
            # We are in speech marks
            if c == in_marks or (not multi_line_strings and c in ['', '\r']):
                # but we just got to the end of them
                in_marks = False
            if c not in ["\x1D"]:
                out += c
        elif c in ['"', "'", "\x1D"]:
            # Enter speech marks
            in_marks = c
            if c not in ["\x1D"]:
                out += c
        elif c in ['{', '[']:
            # Increase step and add new line
            step += step_size
            out += c
            out += ''
            out += step_char * step
        elif c in ['}', ']']:
            # Decrease step and add new line
            step -= step_size
            out += ''
            out += step_char * step
            out += c
        elif c in [':']:
            # Follow with a space
            out += c
            out += ' '
        elif c in [',']:
            # Follow with a new line
            out += c
            out += ''
            out += step_char * step
        elif c in [' ', '', '\r', '\t', '\x1D']:
            #Ignore this character
            pass
        else:
            # Character of no special interest, so just output it as it is
            out += c
    return out

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
        self.original_files = os.listdir(original_path)

    def addVerified(self):
        for original_file in self.original_files:
            # read in the original json file
            # original_filename = self.original_path + self.filename + self.original_extension
            original_json = json.loads(open(self.original_path + original_file).read(), object_pairs_hook=join_duplicate_keys)

            # if it is a positive nodule, it won't have verified info, add verified info for the ground truth so that we
            # can apply general json parser on the ground truth
            for i in range(len(original_json["Nodules"]["item"])):
                if "VerifiedNodule" not in original_json["Nodules"]["item"][i]:
                    original_json["Nodules"]["item"][i]["VerifiedNodule"] = {"labelIndex": "0", "Center0": "0",
                                                                             "Center1": "0", "Center1": "0", "Center2":
                                                                             "0", "True": "True", "Malign": "false",
                                                                             "Solid": "True", "GGO": "false", "Mixed":
                                                                             "false" , "Calc": "false"}

            # output to new json files
            target_filename = self.target_path + original_file[:-5] + self.target_extension
            # target_json = pretty_json(json.dumps(DuplicateDict(original_json), ensure_ascii=False).encode('utf-8'))
            with io.open(target_filename, 'w', encoding='utf8') as outfile:
                str_ = json.dumps(DuplicateDict(original_json), indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
                outfile.write(to_unicode(str_))


if __name__ == "__main__":
    original_path = ".\\label\\"
    target_path = ".\\label\\"
    original_extension = ".json"
    target_extension = "_new.json"
    test = AddVerifiedNodule(original_path, target_path, original_extension, target_extension)
    test.addVerified()
# # read in the original ground truth file
# original_file = json.loads(open(filename).read(), object_pairs_hook=join_duplicate_keys)
#
# # output to new json files
# json_str = pretty_json(json.dumps(DuplicateDict(json_reproduce), ensure_ascii=False).encode('utf-8'))
# file_reproduce = self._path_reproduce + name + self._postfix_target
# with open(file_reproduce, 'w', encoding='utf-8') as f:
#     f.write(json_str)
#     f.close()
# print(name + ' Done')
#
# suffix = ".json"
# filename = "gt" + suffix
# jsonfile = json.loads(open(filename).read(), object_pairs_hook=join_duplicate_keys)
#
#
#
# with io.open("new1" + ".json", 'w', encoding='utf8') as outfile:
#     str_ = json.dumps(jsonfile, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
#     outfile.write(to_unicode(str_))

