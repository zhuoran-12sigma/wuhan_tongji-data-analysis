# -*- coding: utf-8 -*-
from gt_converter import AddVerifiedNodule
import sys
from sigmaLU_jsonScan import sigmaLU_Scan
import numpy
import csv
import os

v = sys.version_info.major
# if v == 2:
#     from io import open
    # from io import BytesIO
platform = sys.platform
if platform.startswith('win'):
    slash = '\\'
elif platform.startswith('linux') or platform.startswith("darwin"):
    slash = '/'

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def del_dir_tree(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            del_dir_tree(itempath)
        os.rmdir(path)
class AutoMatch:
    def __init__(self, gt_path, detect_path, log_path, result_path, gt_postfix, detect_postfix):
        self._gt_path = gt_path
        self._detect_path = detect_path
        self._log_path = log_path
        self._result_path = result_path
        self._gt_postfix = gt_postfix
        self._detect_postfix = detect_postfix
        if os.path.isdir(self._log_path):
            del_dir_tree(self._log_path)
        os.mkdir(self._log_path)
        if os.path.isdir(self._result_path):
            del_dir_tree(self._result_path)
        os.mkdir(self._result_path)
        self._sensitivity = dict()

    def compareGT(self):
        scans = listdir_nohidden(self._detect_path)
        sensitivity = dict()


        for scan in scans:
            curr_detect_path = self._detect_path + scan + slash

            # open the log files
            curr_log_name = self._log_path + scan + ".txt"
            # print("current log " + curr_log_name)

            # record the TP, FP, recall of current scan
            TP_num = 0
            FP_num = 0

            gt_files = listdir_nohidden(gt_path)
            for gt_file in gt_files:
                name = gt_file.split(self._gt_postfix)[0]
                # write the consistency.csv file
                gt = sigmaLU_Scan(self._gt_path + name + self._gt_postfix, 1.0)
                de = sigmaLU_Scan(curr_detect_path + name + "_" + scan + self._detect_postfix, 1.0)

                if de.getCount() == 0 and gt.getCount() == 0:
                    print("No Nodule for" + name)
                    continue
                # compare one gt_file to one detect_file
                de.parseAllNodules()
                gt.parseAllNodules()
                for dd in de._noduleDiameter:
                    idx = int(dd)
                    de_Center = de.getNoduleCenter(idx)
                    de_box = de.getBoxShape(idx)
                    for dg in gt._verifiedMaligFlagDict:
                        if gt.getVerifiedNoduleFlag(dg) == 'true':
                            gt_Center = gt.getNoduleCenter(int(dg))
                            if all(numpy.abs(numpy.array(gt_Center) - numpy.array(de_Center)) <= numpy.array(
                                    de_box) / 2):
                                gt.addMatch(int(dg), int(dd))
                                de.addMatch(int(dd), int(dg))
                            # write in to the log
                                if not os.path.isfile(curr_log_name):
                                    with open(curr_log_name, 'w') as f:
                                        if v == 2:
                                            f.write(unicode("pid" + "\t" + "gt" + "\t" + "detection" + "\n"))
                                            f.write(unicode(name + "\t" + str(int(dg)) + "\t" + str(int(dd)) + "\n"))
                                        else:
                                            f.write("pid" + "\t" + "gt" + "\t" + "detection" + "\n")
                                            f.write(name + "\t" + str(int(dg)) + "\t" + str(int(dd)) + "\n")
                                else:
                                    with open(curr_log_name, 'a') as f:
                                        if v == 2:
                                            f.write(unicode(name + "\t" + str(int(dg)) + "\t" + str(int(dd)) + "\n"))
                                        else:
                                            f.write(name + "\t" + str(int(dg)) + "\t" + str(int(dd)) + "\n")
                                f.close()
                # calculate TP and FP, write to the CSV file
                # print ("GT match pair")
                # print (gt._MatchPairs)
                csv_filename = self._result_path + name + ".csv"
                # write the header
                if not os.path.isfile(csv_filename):
                    headers = [u"序列号"]
                    for i in range(gt.getCount()):
                        headers.append(u"真结节#" + str(i))
                        headers.extend([u"最大直径", u"平均直径", u"体积", u"平均密度"])
                    headers.extend([u"找到真性结节个数", u"假阳性结节个数"])
                    true_row = (u"金标准",)

                    for x in gt._MatchPairs:
                        true_row += ("",gt.getMaxDiameter(x), gt.getAveDiameter(x), gt.getVolume(x), gt.getAveHU(x))
                    true_row += ("", "")
                    if v == 2:
                        mode = "wb"
                    else:
                        mode = "w"
                    with open(csv_filename, mode) as f:
                        if v == 2:
                            f.write(u'\ufeff'.encode('utf8'))
                        f_csv = csv.writer(f)
                        if v == 2:
                            # headers = unicode(headers).encode('utf-8')
                            # true_row = unicode(true_row).encode('utf-8')
                            for a in [headers, true_row]:
                                f_csv.writerow([unicode(aa).encode('utf8') for aa in a])
                        else:
                            f_csv.writerow(headers)
                            f_csv.writerow(true_row)
                        f.close()
                row = (scan,)
                # true_row = ("金标准",)
                for x in gt._MatchPairs:
                    if gt._MatchPairs[x] != []:
                        index = gt._MatchPairs[x][0]
                        TP_num += 1
                        row += (1, de.getMaxDiameter(index), de.getAveDiameter(index), de.getVolume(index), de.getAveHU(index))
                    else:
                        row += (0, " ", " ", " ", " ")
                    # true_row += (gt.getMaxDiameter(x), gt.getAveDiameter(x), gt.getVolume(x), gt.getAveHU(x))
                FP_num += de.getCount() - TP_num
                sensitivity[scan]= [TP_num, FP_num]
                row += (TP_num, FP_num)
                if v == 2:
                    mode = "ab"
                else:
                    mode = "a"
                with open(csv_filename, mode) as f:
                    if v == 2:
                        f.write(u'\ufeff'.encode('utf8'))
                    f_csv = csv.writer(f)
                    if v == 2:
                        f_csv.writerow([unicode(aa).encode('utf8') for aa in row])
                    else:
                        f_csv.writerow(row)
                    f.close()

        self._sensitivity = sensitivity
        return self._sensitivity

    def write_sen(self):
        TP_ave = 0
        FP_ave = 0
        row_TP = (u"找到真结节个数",)
        row_FP = (u"假阳性结节个数",)
        headers = [" "]
        for item in self._sensitivity:
            TP_ave += self._sensitivity[item][0]
            FP_ave += self._sensitivity[item][1]
            row_TP +=(self._sensitivity[item][0],)
            row_FP += (self._sensitivity[item][1],)
            headers.append(item)
        TP_ave /= round(len(self._sensitivity) * 1.0, 3)
        FP_ave /= round(len(self._sensitivity) * 1.0, 3)
        row_TP += (TP_ave,)
        row_FP += (FP_ave,)
        headers.append("Average")

        if v == 2:
            mode = "wb"
        else:
            mode = "w"
        with open(self._result_path + "sensitivity.csv", mode) as f:
            if v == 2:
                f.write(u'\ufeff'.encode('utf8'))
            f_csv = csv.writer(f)
            if v == 2:
                # headers = unicode(headers).encode('utf-8')
                # row_TP = unicode(row_TP).encode('utf-8')
                # row_FP = unicode(row_FP).encode('utf-8')
                for a in [headers, row_TP, row_FP]:
                    f_csv.writerow([unicode(aa).encode('utf8') for aa in a])
            else:
                f_csv.writerow(headers)
                f_csv.writerow(row_TP)
                f_csv.writerow(row_FP)
            f.close()

    # def write_con(self, name):

if __name__ == "__main__":


    # add verified nodule to ground truth and delete non_GT
    # gt_path_old = "/Users/zhuoran/wuhan_tongji-data-analysis/data/label/"
    # if platform.startswith('win'):


    if v == 2:
        str_input = raw_input("请输入金标准路径：".decode("utf-8").encode("gb2312"))
        gt_path_old = str_input
        str_input = raw_input("请输入转化后金标准路径：".decode("utf-8").encode("gb2312"))
        # gt_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/label_new/"
        gt_path = str_input

        gt_postfix_old = ".json"
        gt_postfix = "_gt.json"
        myGT = AddVerifiedNodule(gt_path_old, gt_path, gt_postfix_old, gt_postfix)
        myGT.addVerified()

        # match ground truth and detect file
        str_input = raw_input("请输入CAD结果路径：".decode("utf-8").encode("gb2312"))
        detect_path = str_input
        # detect_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/detection/"
        str_input = raw_input("请输入日志路径：".decode("utf-8").encode("gb2312"))
        log_path= str_input
        # log_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/log/"
        str_input = raw_input("请输入结果分析路径：".decode("utf-8").encode("gb2312"))
        result_path = str_input
    else:
        str_input = input("请输入金标准路径：".decode("utf-8").encode("gb2312"))
        gt_path_old = str_input
        str_input = input("请输入转化后金标准路径：".decode("utf-8").encode("gb2312"))
        # gt_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/label_new/"
        gt_path = str_input

        gt_postfix_old = ".json"
        gt_postfix = "_gt.json"
        myGT = AddVerifiedNodule(gt_path_old, gt_path, gt_postfix_old, gt_postfix)
        myGT.addVerified()

        # match ground truth and detect file
        str_input = input("请输入CAD结果路径：".decode("utf-8").encode("gb2312"))
        detect_path = str_input
        # detect_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/detection/"
        str_input = input("请输入日志路径：".decode("utf-8").encode("gb2312"))
        log_path= str_input
        # log_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/log/"
        str_input = input("请输入结果分析路径：".decode("utf-8").encode("gb2312"))
        result_path = str_input
    # result_path = "/Users/zhuoran/wuhan_tongji-data-analysis/data/result/"
    detect_postfix = ".json"
    myMatch = AutoMatch(gt_path, detect_path, log_path, result_path, gt_postfix, detect_postfix)
    sen = myMatch.compareGT()
    # print sen
    myMatch.write_sen()
