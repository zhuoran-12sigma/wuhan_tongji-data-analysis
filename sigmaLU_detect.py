from sigmaLU_jsonScan import sigmaLU_Scan
from os import listdir
import os
import csv
import io
import sys
from sigmaLU_general import sigmaLU_General
pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_Detect(sigmaLU_General):
    def __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, diameterScale, malignThre, GTtypeSource):
        '''
        This is the sigmaLU_Detect class for detection evaluation
        Author: Siqi Qin
        :param filename: output file name
        :param detect_path: path to sigmaLU results
        :param gt_path: path to ground truth files
        :param result_path: path to all output evaluation files
        :param detect_postfix: postfix of the the results of sigmaLU, eg: 100012_T0.json, postfix = '.json'
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param keywords: keywords for detection
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        :param diameterScale: in Scan, diameter = max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * iameterScale
        :param malignThre: threshold for malign
        '''
        sigmaLU_General.__init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords)
        self._diameterScale = diameterScale
        self._malignThre = malignThre
        self._GTtypeSource = GTtypeSource
        self.readMe()

    def readMe(self):
        f = open(self._result_path + "readMe.txt", "w")
        f.write("This is the readMe file for detection evaluation \n")
        f.write("\n")
        f.write(self._filename + "_detect.csv stores the raw data of the detection model results \n")
        f.write(self._filename + "_detect_StatSummary.csv stores the detection statistical results \n")
        f.write("//ROC folder stores the roc curves of different size interval and different type \n")
        f.write("//Matchlog folder stores the match log of detection and groundTruth\n")
        f.write("//FalseCases folder stores the false detections for later model improvement\n")
        f.close()

    def compare(self):
        '''
        This is the compare function to extract the info from gt and detect
        '''
        if os.path.isdir(self._log_dir) == False:
            os.mkdir(self._log_dir)
        # loop through all results
        for f in self._target_lists:
            name = f.split('.')[0]
            de = sigmaLU_Scan(self._detect_path + name + self._detect_postfix, self._diameterScale)
            gt = sigmaLU_Scan(self._gt_path + name + self._gt_postfix, self._diameterScale)
            if de.getCount() == 0 and gt.getCount() == 0:
                print('No Nodule for ' + name)
                continue
            # nodule matching
            self.compareGT(gt, de, name, self._log_dir)

            # deal with FN cases
            for x in gt._MatchPairs:
                if len(gt._MatchPairs[x]) == 0:
                    idx = int(x)
                    Flag = 'FN'
                    D = gt.getDiameter(idx)
                    if self._GTtypeSource == 0:
                        TT = gt.getTypefromVerify(idx)
                    elif self._GTtypeSource == 1:
                        TT = gt.getTypefromNodule(idx)
                    else:
                        print('Type source only from 0 = gt verify, 1 = gt CAD')
                        exit(1)
                    Score = gt.getDetScore(idx)
                    Malig = gt.getVerifiedMaligFlag(idx)
                    if gt.getVerifiedNoduleFlag(idx) == 'true':
                        self._detectList.append(
                            {'PID': name + '_gt', 'Index': idx, 'Flag': Flag, 'Sigma DetectScore': Score, 'Malig': Malig,
                             'Diameter': D, 'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                            'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']})

            for x in de._MatchPairs:
                idx = int(x)
                D = de.getDiameter(idx)
                Score = de.getDetScore(idx)
                if len(de._MatchPairs[idx]) == 0:
                    # deal with FP cases
                    TT = de.getTypefromNodule(idx)
                    Flag = 'FP'
                    Malig = de.getMalignScore(idx) > self._malignThre
                    if Malig:
                        Malig = 'true'
                    else:
                        Malig = 'false'
                    self._detectList.append(
                        {'PID': name, 'Index': idx, 'Flag': Flag, 'Sigma DetectScore': Score, 'Malig': Malig,
                        'Diameter': D, 'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                            'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']})
                else:
                    # deal with TP cases
                    for m in de._MatchPairs[idx]:
                        if self._GTtypeSource == 0:
                            TT = gt.getTypefromVerify(int(m))
                        elif self._GTtypeSource == 1:
                            TT = gt.getTypefromNodule(int(m))
                        else:
                            print('Type source only from 0 = gt verify, 1 = gt CAD')
                            exit(1)
                        Flag = 'TP'
                        Malig = gt.getVerifiedMaligFlag(int(m))
                        if gt.getVerifiedNoduleFlag(int(m)) == 'true':
                            self._detectList.append(
                                {'PID': name, 'Index': idx, 'Flag': Flag, 'Sigma DetectScore': Score, 'Malig':Malig,
                                'Diameter': D, 'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                            'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']})

            print(name + ' Done')

    def writeCSV(self):
        fieldnames = ['PID', 'Index', 'Flag', 'Sigma DetectScore', 'Malig', 'Diameter', 'Solid', 'p_GGO', \
                      'm_GGO', 'Calc', 'Solid_Calc', 'm_GGO_Calc']

        if pyVersion == 3:
            csvfile = open(self._result_path + self._filename + '_detect.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._result_path + self._filename + '_detect.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._detectList:
            writer.writerow(d)

    def getPlots(self):
        self.Grouping("detect")
        self.statResult("detect")


# TEST SECTION
if __name__ == '__main__':
    filename = 'test'
    detect_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\malign\\result\\'
    gt_path = '\\\\192.168.0.12\\Data\\Datasets\\Lung_Cancer\\JSPH\\nii\\'
    result_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\detect\\'
    detect_postfix = '.json'
    gt_postfix = '_gt_ym_1.2.json'
    keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    diameterScale = 0.7
    MaligThre = 0.5

    myDetect = sigmaLU_Detect(filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, diameterScale, MaligThre)
    myDetect.compare()
    myDetect.writeCSV()
    myDetect.getPlots()