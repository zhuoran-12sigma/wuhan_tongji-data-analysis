import re
from os import listdir
import numpy as np
import csv
import os
import io
import sys

# adapt in both windows and linux platform
platform = sys.platform
if platform.startswith('win'):
    slash = '\\'
elif platform.startswith('linux'):
    slash = '/'

pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class profileTime():
    '''
    This is the profileTime class borrowed from Yuanpeng
    Extract the corresponding time of given keywords
    '''
    def __init__(self, filename):
        self._filename = filename
        self._keyDict = {}

    def process(self, keyword):
        self._keyDict[keyword] = []
        with open(self._filename) as f:
            lines = f.readlines()
            for line in lines:
                line = line.rstrip()
                # if find keyword
                mymatch = re.search(keyword, line)
                if mymatch:
                    value = line.split()[-1] # last value needs to be the time value
                    try:
                        self._keyDict[keyword].append(float(value))
                    except ValueError:
                        pass

    def getKeyDict(self, keyword):
        return self._keyDict[keyword]

class sigmaLU_Profile(object):
    '''
    This is the Profile class for auto evaluation system
    Author: Siqi Qin
    '''
    def __init__(self, filename, filepath, outpath, keywords, postfix = '.json'):
        '''
        This is the constructor of Profile class
        :param filepath: the path to the .log files generated from sigmaLU exe
        :param outpath:  the path to the output evaluation results
        :param keywords: the keywords of modules that you want to evaluate with
        :param postfix:  the postfix after pid, eg: 100012_T0.json, postfix = '.json'
        '''
        self._filepath = filepath
        self._filename = filename
        self._outpath = outpath
        if os.path.isdir(self._outpath) == False:
            os.mkdir(self._outpath)
        self._keywords = keywords
        self._postfix = postfix
        self._files = listdir(filepath)
        # idlist stores all "pid" with both .json and .log
        self._idlist = sorted([f.split(self._postfix)[0] for f in self._files if self._postfix in f])
        # original stores the raw information extracted from .log files
        # runtime stores the time interval of each focused module
        # summary stores the max, min and average of each module
        self._original = []
        self._runtime = []
        self._summary = {}
        self._fieldnames = []
        self.readMe()

    def readMe(self):
        '''
        Add README document for the folder
        :return:
        '''
        f = open(self._outpath + "readMe.txt", "w")
        f.write("This is the readMe file for profiling evaluation \n")
        f.write("\n")
        f.write(self._filename + "_profile_original.csv stores the raw data from log files \n")
        f.write(self._filename + "_profile_runtime.csv stores the runtime of each section  \n")
        f.write(self._filename + "_profile_summary.csv stores the statistics of runtime for each section  \n")
        f.write("//CornerCases folder stores all the cases with runtime greater than twice the average")
        f.close()

    def extractInfo(self):
        '''
        extractInfo from given input files
        '''
        # extract original info
        for id in self._idlist:
            print('Extracting orignal Info for ' + str(id))
            file = self._filepath + id + '.log'
            myObj = profileTime(file)
            info = {}
            info['pid'] = id
            for k in self._keywords:
                myObj.process(k)
                if len(myObj.getKeyDict(k)) > 0:
                    info[k] = myObj.getKeyDict(k)[-1]
                else:
                    info[k] = None
            self._original.append(info)

        # calculate time interval of each module
        keydiff = []
        for i in range(1, len(self._keywords)):
            keydiff.append(self._keywords[i].replace('after ', ''))
        for o in self._original:
            valid = True
            info = {}
            info['pid'] = o['pid']
            print('Extracting runtime Info for ' + o['pid'])
            info[self._keywords[0].replace('after ', '')] = o[self._keywords[0]]
            for i in range(1, len(self._keywords)):
                if o[self._keywords[i]] != None and o[self._keywords[i - 1]] != None:
                    info[self._keywords[i].replace('after ', '')] = o[self._keywords[i]] - o[self._keywords[i - 1]]
                else:
                    info[self._keywords[i].replace('after ', '')] = None
                    valid = False
                if i == len(self._keywords) - 1:
                    if o[self._keywords[i]] != None:
                        info['all'] =o[self._keywords[i]]
                    else:
                        info['all'] = None
                        valid = False
            if valid:
                self._runtime.append(info)

        # calculate min, max, average of each module
        self._fieldnames = ['pid', 'all', self._keywords[0].replace('after ', '')]
        self._fieldnames.extend(keydiff)
        if not os.path.exists(self._outpath + 'CornerCases'):
            os.mkdir(self._outpath + 'CornerCases')
        for k in self._fieldnames[1:]:
            self._summary[k] = {}
            self._summary[k]['Average'] = np.mean([float(a[k]) for a in self._runtime])
            self._summary[k]['Min'] = min([(a[k], a['pid']) for a in self._runtime])
            corner = []
            valid = []
            for a in self._runtime:
                if a[k] >= 2 * self._summary[k]['Average']:
                    corner.append((a[k], a['pid']))
                else:
                    valid.append((a[k], a['pid']))
            # save all corner cases with time >= 2 * average
            f = open(self._outpath + 'CornerCases' + slash + k + '_cornercases.csv', 'w')
            f.write('Time, PID \n')
            for c in corner:
                f.write(str(c[0]) + ',  ' + c[1] + '\n')
            f.close()
            self._summary[k]['Max'] = max(valid)

    def writeCSV(self):
        fieldnames = ['pid']
        fieldnames.extend(self._keywords)
        if pyVersion == 3:
            csvfile = open(self._outpath + self._filename + '_profile_original.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._outpath + self._filename + '_profile_original.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._original:
            writer.writerow(d)

        if pyVersion == 3:
            csvfile = open(self._outpath + self._filename + '_profile_runtime.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._outpath + self._filename + '_profile_runtime.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=self._fieldnames)
        writer.writeheader()
        for d in self._runtime:
            writer.writerow(d)

        with open(self._outpath + self._filename + '_profile_summary.csv', 'w') as f:
            f.write('Total Case Amount: ' + str(len(self._runtime)) + '\n')
            for k in self._fieldnames[1:]:
                f.write('\n')
                f.write(k + ': \n')
                f.write('Average: ' + str(self._summary[k]['Average']) + ', \n')
                f.write('Max: ' + str(self._summary[k]['Max'][0]) + '   ' + self._summary[k]['Max'][1] + '\n')
                f.write('Min: ' + str(self._summary[k]['Min'][0]) + '   ' + self._summary[k]['Min'][1] + '\n')



if __name__ == '__main__':
    result_path = 'Z:\\Data02\\Release\\sigmaLU_release_test_results\\SigmaLU_Results\\temp\\'
    result_postfix = '.json'
    output_path = 'Z:\\Data02\\Release\\sigmaLU_release_test_results\\SigmaLU_Results\\profilingEvaluation\\'
    profile_keywords = ['after read in volume', 'after normalization',
                        'after segmentation', 'after 3D 1st stage processing',
                        'after 2nd stage processing', 'after Nodule Segmentation',
                        'after nodule malignancy classification',
                        'after post processing',
                        'after compute Nodule Stats', 'after Lung-RADS']
    # profile_keywords = ['after nodule segmentation', 'after nodule malignancy classification',
    #            'after nodule stats', 'after post process']
    filename = "test"
    test = sigmaLU_Profile(filename, result_path, output_path, profile_keywords, result_postfix)
    test.extractInfo()
    test.writeCSV()

