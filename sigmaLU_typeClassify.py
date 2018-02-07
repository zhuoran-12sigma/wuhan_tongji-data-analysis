from sigmaLU_jsonScan import sigmaLU_Scan
from os import listdir
from sigmaLU_general import sigmaLU_General
import os
import csv
import io
import sys

pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_TypeClassify(sigmaLU_General):
    '''
    This is the sigmaLU_TypeClassify class for type classification evaluation
    Author: Siqi Qin
    '''
    def __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, diameterScale, GTtypeSource):
        '''
        :param filename: output file name
        :param detect_path: path to sigmaLU results
        :param gt_path: path to ground truth files
        :param result_path: path to all output files
        :param detect_postfix: postfix of the the results of sigmaLU, eg: 100012_T0.json, postfix = '.json'
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param keywords: keywords for type classification
                         eg: [[8, 20]]
                         format: keywords[0] is the keywords for diameter
        :param diameterScale: in Scan, diameter = max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * iameterScale
        '''
        sigmaLU_General.__init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords)
        self._GTtypeSource = GTtypeSource
        self._diameterScale = diameterScale
        self.readMe()

    def readMe(self):
        f = open(self._result_path + "readMe.txt", "w")
        f.write("This is the readMe file for typeClassify evaluation \n")
        f.write("\n")
        f.write(self._filename + "_classify.csv stores the raw data of the classification model results \n")
        f.write("//Matrix folder stores the confusion matrix of different size interval and overall evaluation \n")
        f.write("//Matchlog folder stores the match log of detection and groundTruth\n")
        f.close()

    def extractInfo(self):
        if os.path.isdir(self._log_dir) == False:
            os.mkdir(self._log_dir)
        # loop through all results
        for f in self._target_lists:
            name = f.split('.')[0]
            print(name)
            de = sigmaLU_Scan(self._detect_path + name + self._detect_postfix, self._diameterScale)
            gt = sigmaLU_Scan(self._gt_path + name + self._gt_postfix, self._diameterScale)
            if de.getCount() == 0 and gt.getCount() == 0:
                print('No Nodule for ' + name)
                continue
            # matching nodules
            self.compareGT(gt, de, name, self._log_dir)
            # extract info
            for dg in gt._verifiedMaligFlagDict:
                MaligDoct = gt.getVerifiedMaligFlag(int(dg))
                if MaligDoct == 'true':
                    MaligDoct = 1
                elif MaligDoct == 'false':
                    MaligDoct = 0
                gt_D = gt.getDiameter(int(dg))
                if len(gt._MatchPairs[dg]) != 0:
                    if self._GTtypeSource == 0:
                        TGt = gt.getTypefromVerify(int(dg))
                    elif self._GTtypeSource == 1:
                        TGt = gt.getTypefromNodule(int(dg))
                    else:
                        print('Type source only from 0 = gt verify, 1 = gt CAD')
                        exit(1)
                    for m in gt._MatchPairs[dg]:
                        TDe = de.getTypefromNodule(int(m))
                        self._classList.append(
                            {'PID': name, 'Index': int(dg), 'MaligDoct': MaligDoct, 'Diameter': gt_D,
                             'Solid_GT': TGt['Solid'], 'p_GGO_GT': TGt['p_GGO'], 'm_GGO_GT': TGt['m_GGO'], 'Calc_GT': TGt['Calc'],
                             'Solid_Calc_GT': TGt['Solid_Calc'], 'm_GGO_Calc_GT': TGt['m_GGO_Calc'],
                             'Solid_DE': TDe['Solid'], 'p_GGO_DE': TDe['p_GGO'], 'm_GGO_DE': TDe['m_GGO'], 'Calc_DE': TDe['Calc'],
                             'Solid_Calc_DE': TDe['Solid_Calc'], 'm_GGO_Calc_DE': TDe['m_GGO_Calc']})
                else:
                    self._mismatch.append(name + ' ' + str(dg))

    def writeCSV(self):
        fieldnames = ['PID', 'Index', 'MaligDoct', 'Diameter', 'Solid_GT', 'p_GGO_GT', 'm_GGO_GT', 'Calc_GT', 'Solid_Calc_GT', \
                      'm_GGO_Calc_GT', 'Solid_DE', 'p_GGO_DE', 'm_GGO_DE', 'Calc_DE', 'Solid_Calc_DE', 'm_GGO_Calc_DE']

        if pyVersion == 3:
            csvfile = open(self._result_path + self._filename + '_classify.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._result_path + self._filename + '_classify.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._classList:
            writer.writerow(d)

    def getMatrix(self):
        self.Grouping("classify")
        self.statResult("classify")


# TEST SECTION
if __name__ == '__main__':
    filename = 'test'
    detect_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\malign\\result\\'
    gt_path = '\\\\192.168.0.12\\Data\\Datasets\\Lung_Cancer\\JSPH\\nii\\'
    result_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\classify\\'
    detect_postfix = '.json'
    gt_postfix = '_gt_ym_1.2.json'
    keywords = [[8, 20]]
    diameterScale = 0.7

    myTypeClassify = sigmaLU_TypeClassify(filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, diameterScale)
    myTypeClassify.extractInfo()
    myTypeClassify.writeCSV()
    myTypeClassify.getMatrix()