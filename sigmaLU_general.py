from sigmaLU_jsonScan import sigmaLU_Scan
import sys
import os
import csv
import io
import numpy
platform = sys.platform
if platform.startswith('win'):
    slash = '\\'
elif platform.startswith('linux'):
    slash = '/'

sys.path.append(os.path.abspath(os.path.dirname(__file__) + slash + '.' + slash + 'common_Utils' + slash))
from sklearn import metrics
from os import listdir
from draw import Draw
import pandas as pd
pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_General(object):
    '''
    This is the General parent class of malign and detect, stores all the shared functions of malign and detect
    Author: Siqi Qin
    '''
    def __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords):
        '''
        This is the Constructor of General class
        :param filename: the name you want to give to all the output files
        :param detect_path: the path to the results of sigmaLU exe
        :param gt_path: the path to the ground truth labeled by doctors
        :param result_path: the path to the output of the evaluation
        :param detect_postfix: postfix of the the results of sigmaLU, eg: 100012_T0.json, postfix = '.json'
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param keywords: the keywords for statistical analysis interval
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        '''
        self._filename = filename
        self._detect_path = detect_path
        self._gt_path = gt_path
        self._result_path = result_path
        if os.path.isdir(self._result_path) == False:
            os.mkdir(self._result_path)
        # log_dir stores the match log of gt and detection
        # curve_dir is for malign cumsum curves
        # roc_dir is for detect roc curves
        self._log_dir = result_path + 'Matchlog' + slash
        self._curve_dir = result_path + 'Curves' + slash
        self._wrong_dir = result_path + 'FalseCases' + slash
        self._roc_dir = result_path + 'ROC' + slash
        self._matrix_dir = result_path + 'Matrix' + slash
        self._detect_files = listdir(detect_path)
        self._gt_files = listdir(gt_path)
        self._gt_lists = list(filter(lambda a : gt_postfix in a and 'config' not in a, self._gt_files))
        self._target_lists = list(filter(lambda a: detect_postfix in a and 'config' not in a and a.replace(detect_postfix,
                                                                    gt_postfix) in self._gt_lists, self._detect_files))
        self._keywords = keywords
        self._detect_postfix = detect_postfix
        self._gt_postfix = gt_postfix

        # maligList stores the final results of malig evalution
        # detectList stores the final results of detect evaluation
        # statResult stores the statistics of each group divided with given keywords
        # classList stores the final results of typeclassification evaluation
        # groups stores the nodules belong to each group
        # typekeys and diameterkey stores the true keywords of group adapted from given keywords
        self._maligList = []
        self._detectList = []
        self._classList = []
        self._mismatch = []
        self._statResult = {}
        self._groups = {}
        self._typekeys = []
        self._diameterkey = []

    def compareGT(self, gt, de, name, log_dir):
        '''
        This is the compareGT function for malign and detect nodule matching
        :param gt: gt Scan
        :param de: detect Scan
        :param name: current pid
        :param log_dir: path to store the match log files
        '''
        de.parseAllNodules()
        gt.parseAllNodules()
        # nodule matching, condition: ground truth center is inside the detection box
        for dd in de._noduleDiameter:
            idx = int(dd)
            de_Center = de.getNoduleCenter(idx)
            de_box = de.getBoxShape(idx)
            for dg in gt._verifiedMaligFlagDict:
                if gt.getVerifiedNoduleFlag(dg) == 'true':
                    gt_Center = gt.getNoduleCenter(int(dg))
                    if all(numpy.abs(numpy.array(gt_Center) - numpy.array(de_Center)) <= numpy.array(de_box) / 2):
                        gt.addMatch(int(dg), int(dd))
                        de.addMatch(int(dd), int(dg))

        # record the match result
        f = open(log_dir + name + '.txt', 'w')
        f.write("Ground Truth" + "\n")
        for x in gt._MatchPairs:
            f.write("Index: " + str(x) + " Match: " + str(gt._MatchPairs[x]) + "\n")
        f.write("Detection" + "\n")
        for x in de._MatchPairs:
            f.write("Index: " + str(x) + " Match: " + str(de._MatchPairs[x]) + "\n")

    def Grouping(self, type):
        '''
        This is the Grouping function used for splitting data into different groups referring to given keywords
        :param type: malign or detect or classify
        '''
        if type == "malign":
            assert len(self._keywords) == 2
            myLists = self._maligList
        elif type == "detect":
            assert len(self._keywords) == 2
            myLists = self._detectList
        elif type == "classify":
            assert len(self._keywords) == 1
            myLists = self._classList
        else:
            print("type error, please input malign, detect or classify")
            return
        # keywords initialization
        rth = sorted(self._keywords[0])
        if type != "classify":
            self._typekeys = self._keywords[1]
        # extract true keywords for diameter : [8, 20] to [less_8, 8-20, greater_20]
        self._diameterkey = []
        for i in range(len(rth)):
            if i == 0:
                self._diameterkey.append("less_" + str(rth[i]))
            if i > 0 and i < len(rth):
                self._diameterkey.append(str(rth[i - 1]) + '_' + str(rth[i]))
            if i == len(rth) - 1:
                self._diameterkey.append(("greater_" + str(rth[i])))
        self._groups['all'] = []
        if type != "classify":
            # if not evaluating typeClassification, the keywords has length 2
            # initialize groups
            if type == 'detect':
                self._groups['malig'] = []
                self._groups['benign'] = []
            for k in self._typekeys:
                self._groups[k] = []
            for k in self._diameterkey:
                self._groups[k] = {}
                self._groups[k]['all'] = []
                for t in self._typekeys:
                    self._groups[k][t] = []
            # grouping
            for r in myLists:
                self._groups["all"].append(r)
                for i in range(len(rth)):
                    if i == 0:
                        if float(r['Diameter']) <= rth[i]:
                            self._groups[self._diameterkey[0]]['all'].append(r)
                    if i == len(rth) - 1:
                        if float(r['Diameter']) > rth[i]:
                            self._groups[self._diameterkey[-1]]['all'].append(r)
                    if i > 0 and i < len(rth):
                        if float(r['Diameter']) <= rth[i] and float(r['Diameter']) > rth[i - 1]:
                            self._groups[self._diameterkey[i]]['all'].append(r)

                for t in self._typekeys:
                    if r[t] == 'true':
                        self._groups[t].append(r)

                if type == 'detect':
                    if r['Malig'] == 'true':
                        self._groups['malig'].append(r)
                    elif r['Malig'] == 'false':
                        self._groups['benign'].append(r)

            for r in self._diameterkey:
                for item in self._groups[r]['all']:
                    for t in self._typekeys:
                        if item[t] == 'true':
                            self._groups[r][t].append(item)
        else:
            # if evaluating typeClassification, keywords has length 1
            for k in self._diameterkey:
                self._groups[k] = []
            # grouping
            for r in myLists:
                self._groups["all"].append(r)
                for i in range(len(rth)):
                    if i == 0:
                        if float(r['Diameter']) <= rth[i]:
                            self._groups[self._diameterkey[0]].append(r)
                    if i == len(rth) - 1:
                        if float(r['Diameter']) > rth[i]:
                            self._groups[self._diameterkey[-1]].append(r)
                    if i > 0 and i < len(rth):
                        if float(r['Diameter']) <= rth[i] and float(r['Diameter']) > rth[i - 1]:
                            self._groups[self._diameterkey[i]].append(r)

    def statResult(self, type):
        '''
        This is the statResult function for getting TP,FP, etc of each group
        :param type: malign or detect or classify
        '''
        # initialize output path of given evaluation type
        if type == "malign":
            getStats = self.getStatsMalign
            if os.path.isdir(self._curve_dir) == False:
                os.mkdir(self._curve_dir)
        elif type == "detect":
            getStats = self.getStatsDetect
            if os.path.isdir(self._roc_dir) == False:
                os.mkdir(self._roc_dir)
        elif type == "classify":
            if os.path.isdir(self._matrix_dir) == False:
                os.mkdir(self._matrix_dir)
            getStats = self.getStatsClassify
        else:
            print("type error, please input malign, detect or classify")
            return
        # gather statistics for the output csv files
        if type != "classify":
            if os.path.isdir(self._wrong_dir) == False:
                os.mkdir(self._wrong_dir)
            # loop through all possible combination of diameter and type keywords, get the statistics
            pdInput = []
            if type == "malign":
                keyList = ["Total", "Malig", "Benign", "TP", "FP", "TN", "FN", "TPR", "FNR", "TNR", "FPR", "Precision", "Accuracy"]
            elif type == "detect":
                keyList = ["Scan", "# Nodule", "TP", "FP", "FN", "Sensitivity", "FP/Scan"]
            pdInput.append((' ', keyList))
            pdInput.append(getStats(self._groups['all'], 'all'))
            if type == 'detect':
                pdInput.append(getStats(self._groups['malig'], 'malig'))
                pdInput.append(getStats(self._groups['benign'], 'benign'))
            for t in self._typekeys:
                pdInput.append(getStats(self._groups[t], t))
            for r in self._diameterkey:
                pdInput.append(getStats(self._groups[r]['all'], r))
            for r in self._diameterkey:
                for k in self._groups[r]:
                    if k != 'all':
                        pdInput.append(getStats(self._groups[r][k], r + '_' + k))
            pdClass = pd.DataFrame.from_items(pdInput)
            pdClass.fillna('N/A')
            pdClass.T.to_csv(self._result_path + self._filename + "_" + type + "_StatSummary.csv")

        else:
            getStats(self._groups['all'], "all")
            for k in self._diameterkey:
                getStats(self._groups[k], k)

    def getStatsMalign(self, data, d):
        '''
        This is the function to get statistic of Malign
        :param data: original data
        :param d: key of this group, might be 8_10_GGO
        :param file: record the statistic information in a txt file
        '''
        # initialization
        TP = []
        FP = []
        FN = []
        TN = []
        Doctor0 = []
        Doctor1 = []
        Doctor0Scores = []
        Doctor1Scores = []
        # gather TP, FP, FN, TN etc
        for r in data:
            if r['MaligDoct'] == 1:
                Doctor1.append(r)
                Doctor1Scores.append(float(r['Sigma MaligScore']))
                if r['SigmaResult'] == 1:
                    TP.append(r)
                else:
                    FN.append(r)
            else:
                Doctor0.append(r)
                Doctor0Scores.append(float(r['Sigma MaligScore']))
                if r['SigmaResult'] == 1:
                    FP.append(r)
                else:
                    TN.append(r)

        # calculate statistics
        Infos= []
        Infos.append(len(TP) + len(FN) + len(FP) + len(TN))
        Infos.append(len(TP) + len(FN))
        Infos.append(str(len(FP) + len(TN)))
        Infos.append(len(TP))
        Infos.append(len(FP))
        Infos.append(len(TN))
        Infos.append(len(FN))
        if len(TP) + len(FN) == 0:
            Infos.append("N/A")
            Infos.append("N/A")
        else:
            Infos.append(round(len(TP) * 1.0 / (len(TP) + len(FN)),3))
            Infos.append(round(len(FN) * 1.0 / (len(TP) + len(FN)),3))
        if len(FP) + len(TN) == 0:
            Infos.append("N/A")
            Infos.append("N/A")
        else:
            Infos.append(round(len(TN) * 1.0 / (len(FP) + len(TN)),3))
            Infos.append(round(len(FP) * 1.0 / (len(FP) + len(TN)),3))
        if len(TP) + len(FP) == 0:
            Infos.append("N/A")
        else:
            Infos.append(round(len(TP) * 1.0 / (len(TP) + len(FP)),3))
        if len(TP) + len(TN) + len(FP) + len(FN) == 0:
            Infos.append("N/A")
        else:
            Infos.append(round((len(TP) + len(TN)) * 1.0 / (len(TP) + len(TN) + len(FP) + len(FN)),3))


        # record error case
        FP_list = []
        for fp in FP:
            FP_list.append({'PID': fp['PID'], 'Index': fp['Index']})
        FN_list = []
        for fn in FN:
            FN_list.append({'PID': fn['PID'], 'Index': fn['Index']})

        if len(FP_list) != 0:
            if pyVersion == 3:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FP.csv', 'w', newline='')
            elif pyVersion == 2:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FP.csv', 'w')
            writer = csv.DictWriter(csvfile, fieldnames=['PID', 'Index'])
            writer.writeheader()
            for fp in FP_list:
                writer.writerow(fp)

        if len(FN_list) != 0:
            if pyVersion == 3:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FN.csv', 'w', newline='')
            elif pyVersion == 2:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FN.csv', 'w')
            writer = csv.DictWriter(csvfile, fieldnames=['PID', 'Index'])
            writer.writeheader()
            for fn in FN_list:
                writer.writerow(fn)

        # calculate cumsum
        x = [i for i in range(0, 100)]
        y0 = [0 for i in range(0, 100)]
        y1 = [0 for i in range(0, 100)]

        for s in Doctor0Scores:
            y0[int(s * 100)] += 1
        for s in Doctor1Scores:
            y1[int(s * 100)] += 1
        if len(Doctor0Scores) != 0:
            y0 = [y * 1.0 / len(Doctor0Scores) for y in y0]
        if len(Doctor1Scores) != 0:
            y1 = [y * 1.0 / len(Doctor1Scores) for y in y1]

        myDraw = Draw([x, x], [1 - numpy.cumsum(y0), numpy.cumsum(y1)], "Malign Score", "Probability", d + " Group Cumsum",
                      ['benign', 'malign'], self._curve_dir + "Group_" + d + ".png")
        myDraw.show()

        return (d, Infos)

    def getStatsDetect(self, data, d):
        '''
        This is the function to get statistic of Detect
        :param data: original data
        :param d: key of this group, might be 8_10_GGO
        :param file: record the statistic information in a txt file
        '''
        # extract TP, FP, FN
        TP = list(filter(lambda datum : datum['Flag'] == 'TP', data))
        FP = list(filter(lambda datum : datum['Flag'] == 'FP', data))
        FN = list(filter(lambda datum: datum['Flag'] == 'FN', data))

        # record error cases
        FP_list = []
        for fp in FP:
            FP_list.append({'PID': fp['PID'], 'Index': fp['Index']})
        FN_list = []
        for fn in FN:
            FN_list.append({'PID': fn['PID'], 'Index': fn['Index']})

        if len(FP_list) != 0:
            if pyVersion == 3:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FP.csv', 'w', newline='')
            elif pyVersion == 2:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FP.csv', 'w')
            writer = csv.DictWriter(csvfile, fieldnames=['PID', 'Index'])
            writer.writeheader()
            for fp in FP_list:
                writer.writerow(fp)

        if len(FN_list) != 0:
            if pyVersion == 3:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FN.csv', 'w', newline='')
            elif pyVersion == 2:
                csvfile = open(self._wrong_dir + self._filename + '_' + d + '_FN.csv', 'w')
            writer = csv.DictWriter(csvfile, fieldnames=['PID', 'Index'])
            writer.writeheader()
            for fn in FN_list:
                writer.writerow(fn)


        # calculate statistics
        Infos = []
        Detect_Amount = len(TP) + len(FN)
        TruePositive = len(TP)
        FalsePositive = len(FP)
        FalseNegative = len(FN)
        if TruePositive + FalseNegative != 0:
            Sensitivity = TruePositive * 1.0 / (TruePositive + FalseNegative)
        else:
            Sensitivity = "N/A"
        Scans = set(list(map(lambda datum : datum['PID'].replace("_gt", ""), data)))
        if len(Scans) != 0:
            FP_Scan = FalsePositive * 1.0 / len(Scans)
        else:
            FP_Scan = "N/A"
        Infos.append(len(Scans))
        Infos.append(Detect_Amount)
        Infos.append(TruePositive)
        Infos.append(FalsePositive)
        Infos.append(FalseNegative)
        if isinstance(Sensitivity, str):
            Infos.append(Sensitivity)
        else:
            Infos.append(round(Sensitivity,3))
        if isinstance(FP_Scan, str):
            Infos.append(FP_Scan)
        else:
            Infos.append(round(FP_Scan,3))
        # calculate froc
        if TruePositive + FalsePositive != 0:
            unlisted_FPs = list(map(lambda datum: float(datum['Sigma DetectScore']), FP))
            unlisted_TPs = list(map(lambda datum: float(datum['Sigma DetectScore']), TP))
            all_probs = sorted(set(unlisted_FPs + unlisted_TPs))
            total_FPs, total_TPs = [], []
            for Thresh in all_probs[1 : ]:
                total_FPs.append((numpy.asarray(unlisted_FPs) >= Thresh).sum())
                total_TPs.append((numpy.asarray(unlisted_TPs) >= Thresh).sum())
            total_FPs.append(0)
            total_TPs.append(0)
            total_Sens = numpy.asarray(total_TPs) / float(TruePositive + FalseNegative)
            total_FPs = numpy.asarray(total_FPs) / float(len(Scans))
            myDraw = Draw([total_FPs], [total_Sens], "FP/Scan", "TPR", d + " Group_FROC",
                          [], self._roc_dir + "Group_" + d + ".png")
            myDraw.show()

        return (d, Infos)

    def getStatsClassify(self, data, post):
        '''
        This is the function to get statistic of type classification
        :param data: original data
        :param post : keywords know you are evaluating for
        '''
        # initialization
        classKeys = ["Solid", "p_GGO", "m_GGO", "Calc", "Solid_Calc", "m_GGO_Calc"]
        classBox = {}
        for k in classKeys:
            classBox[k] = {}
            for l in classKeys:
                classBox[k]["all"] = 0
                classBox[k][l] = 0

        # count result distribution in confusion matrix
        for d in data:
            for k in classKeys:
                if d[k + "_GT"] == 'true':
                    classBox[k]["all"] += 1
                    for t in classKeys:
                        if d[t + "_DE"] == 'true':
                            classBox[k][t] += 1

        # calculate confustion matrix
        pdList = []
        for k in classKeys:
            temp = []
            if classBox[k]["all"] != 0:
                for t in classKeys:
                    temp.append(round(classBox[k][t] * 1.0 / classBox[k]["all"], 3))
                temp.append(1)
            else:
                temp = ["N/A"] * len(classKeys)
                temp.append(0)
            pdList.append(temp)

        # output result
        indexs = [t + "_GT" for t in classKeys]
        cols = [t + "_DE" for t in classKeys]
        cols.append("total")
        pdInput = []
        pdInput.append((' ', cols))
        for i in range(len(classKeys)):
            pdInput.append((indexs[i], pdList[i]))

        pdClass = pd.DataFrame.from_items(pdInput)
        pdClass.fillna('N/A')
        pdClass.T.to_csv(self._matrix_dir + self._filename + "_" + post + "_classifyStat.csv")

