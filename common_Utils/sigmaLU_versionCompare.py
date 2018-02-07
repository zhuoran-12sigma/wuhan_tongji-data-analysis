import os
import csv
import sys
from sigmaLU_jsonScan import sigmaLU_Scan
pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_VersionCompare(object):
    def __init__(self, v1_path, v2_path, output_path, v1_postfix, v2_postfix):
        '''
        This is the sigmaLU_VersionCompare class for comparing the detection results of two version SigmaLU
        :param v1_path: the detection path of version 1
        :param v2_path: the detection path of version 2
        :param output_path: the comparison results path
        :param v1_postfix: the postfix of version 1 results
        :param v2_postfix: the postfix of version 2 results
        '''
        self._v1_path = v1_path
        self._v2_path = v2_path
        self._v1_postfix = v1_postfix
        self._v2_postfix = v2_postfix
        self._output_path = output_path
        self._v1 = ''
        self._v2 = ''
        self._v1_files = os.listdir(self._v1_path)
        self._v2_files = os.listdir(self._v2_path)
        self._compareResult = []
        self._totaldiff = 0
        self._totalv1 = 0
        self._totalv2 = 0

    def compare(self):
        # loop through all v1 files to find matched v2 files, then extract count # to calculate the difference
        for v1 in self._v1_files:
            if self._v1_postfix in v1 and 'config' not in v1:
                name = v1.split(self._v1_postfix)[0]
                if name + self._v2_postfix in self._v2_files:
                    v1Scan = sigmaLU_Scan(self._v1_path + name + self._v1_postfix, 0)
                    v2Scan = sigmaLU_Scan(self._v2_path + name + self._v2_postfix, 0)
                    self._v1 = v1Scan.getVersion()
                    self._v2 = v2Scan.getVersion()
                    count1 = v1Scan.getCount()
                    count2 = v2Scan.getCount()
                    diff = abs(count1 - count2)
                    self._totalv1 += count1
                    self._totalv2 += count2
                    self._totaldiff += diff
                    self._compareResult.append({'PID': name, self._v1: count1, self._v2: count2, 'diff': diff})
                    print(name + ' done')
        self._compareResult.append({'PID': 'all', self._v1: self._totalv1, self._v2: self._totalv2, 'diff': self._totaldiff})

    def writeCSV(self):
        # save results to csv file
        fieldnames = ['PID', self._v1, self._v2, 'diff']
        if pyVersion == 3:
            csvfile = open(self._output_path + 'versionDiff_' + self._v1 + '_' + self._v2 + '.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._output_path + 'versionDiff_' + self._v1 + '_' + self._v2 + '.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._compareResult:
            writer.writerow(d)


if __name__ == '__main__':
    v1_path = 'Z:\\Data02\\Results\\Lung_Cancer\\NLST\\nlst_nii_test_20171112_v0.5.2\\'
    v2_path = 'Z:\\Data02\\Release\\sigmaLU_release_test_results\\SigmaLU_Results\\Windows_0.5.4\\NLST\\nlst_nii_test_20180115_v0.5.4\\'
    v1_postfix = '.json'
    v2_postfix = '.json'
    output_path = 'C:\\Users\\siqi\\Desktop\\evaluationSiqi\\SigmaPy\\shared\\evaluation_tools\\sigmaLU\\'

    test = sigmaLU_VersionCompare(v1_path, v2_path, output_path, v1_postfix, v2_postfix)
    test.compare()
    test.writeCSV()