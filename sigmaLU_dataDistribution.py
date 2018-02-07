from sigmaLU_jsonScan import sigmaLU_Scan
from os import listdir
import os
import io
import csv
import sys
import numpy as np
import pandas as pd
pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_DataDistribution(object):
    def __init__(self, gt_Path, result_Path, filename, gt_postfix, keywords, diameterScale, GTtypeSource):
        '''
        This is the sigmaLU_DataDistribution class for the auto evaluation System
        Author: Siqi Qin
        :param gt_Path: the path to the ground truth labeled by doctors
        :param result_Path: the path to the output results
        :param filename: the name for the output files
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param keywords: the keywords for statistical analysis interval
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for radius
                                 keywords[1] is the keywords for nodule type
        :param diameterScale: parameter for jsonParser, determines the calculation of diameter
        '''
        self._gt_Path = gt_Path
        self._result_Path = result_Path
        if os.path.isdir(self._result_Path) == False:
            os.mkdir(self._result_Path)
        self._filename = filename
        self._gt_postfix = gt_postfix
        self._gt_files = list(filter(lambda x : self._gt_postfix in x and x.split('.')[-1] == 'json', listdir(self._gt_Path)))
        self._gt_info = []
        self._diameterInterval = sorted(keywords[0])
        self._diameterKey = []
        self._typeKey = keywords[1]
        self._diameterScale = diameterScale
        self._GTtypeSource = GTtypeSource
        self.readMe()

    def readMe(self):
        '''
        This is teh readMe file for the output files
        '''
        f = open(self._result_Path + "readMe.txt", "w")
        f.write("This is the readMe file for groundTruth distribution evaluation \n")
        f.write("\n")
        f.write(self._filename + "_rawData.csv stores the raw data of groundTruth Distribution \n")
        f.write(self._filename + "_Sheets.xlsx stores the statistical results of the groundTruth dataset, "
                                 + "which includes the distribution of combined keywords \n")
        f.close()

    def extractInfo(self):
        '''
        Extract the raw data of detected type class and doctor labeled type class
        '''
        for f in self._gt_files:
            name = f.split(self._gt_postfix)[0]
            gt = sigmaLU_Scan(self._gt_Path + name + self._gt_postfix, self._diameterScale)
            gt.parseAllNodules()
            for g in gt._noduleDiameter:
                idx = int(g)
                diameter = gt.getDiameter(idx)
                if self._GTtypeSource == 0:
                    TT = gt.getTypefromVerify(idx)
                elif self._GTtypeSource == 1:
                    TT = gt.getTypefromNodule(idx)
                else:
                    print('Type source only from 0 = gt verify, 1 = gt CAD')
                    exit(1)
                malig = gt.getVerifiedMaligFlag(idx)
                if gt.getVerifiedNoduleFlag(idx) == 'true':
                    self._gt_info.append({'PID':name, 'NoduleID': idx, 'Diameter': diameter, 'Malig':malig, \
                                          'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                                          'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']
                                          })
            print(name + ' done')

        fieldnames = ['PID', 'NoduleID', 'Diameter', 'Malig', 'Solid', 'p_GGO', 'm_GGO', 'Calc', 'Solid_Calc', 'm_GGO_Calc']
        if pyVersion == 3:
            csvfile = open(self._result_Path + self._filename + '_rawData.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._result_Path + self._filename + '_rawData.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._gt_info:
            writer.writerow(d)

    def getSizeDist(self, input):
        '''
        Calculate the distribution based on size
        :param input: data you want evaluation
        '''
        totalSize = len(input)
        groups = {}
        for r in self._diameterKey:
            groups[r] = []

        for r in input:
            for i in range(len(self._diameterInterval)):
                if i == 0:
                    if float(r['Diameter']) <= self._diameterInterval[i]:
                        groups[self._diameterKey[0]].append(r)
                if i == len(self._diameterInterval) - 1:
                    if float(r['Diameter']) > self._diameterInterval[i]:
                        groups[self._diameterKey[-1]].append(r)
                if i > 0 and i < len(self._diameterInterval):
                    if float(r['Diameter']) <= self._diameterInterval[i] and float(r['Diameter']) > self._diameterInterval[i - 1]:
                        groups[self._diameterKey[i]].append(r)

        countSize = np.array([len(groups[r]) for r in self._diameterKey])
        return groups, countSize, totalSize

    def getTypeDist(self, input):
        '''
        Calculate the distribution based on type
        :param input: data you want evaluation
        '''
        totalType = len(input)
        groups = {}
        for r in self._typeKey:
            groups[r] = []
        for r in input:
            for t in self._typeKey:
                if r[t] == 'true':
                    groups[t].append(r)
        countType = np.array([len(groups[r]) for r in self._typeKey])
        return groups, countType, totalType

    def getMaligDist(self, input):
        '''
        Calculate the distribution based on malign
        :param input: data you want evaluation
        '''
        totalMalig = len(input)
        groups = {}
        groups['malign'] = []
        groups['benign'] = []
        for r in input:
            if r['Malig'] == 'true':
                groups['malign'].append(r)
            elif r['Malig'] == 'false':
                groups['benign'].append(r)
        countMalig = np.array([len(groups[r]) for r in ['malign', 'benign']])
        return groups, countMalig, totalMalig

    def getxlsxSheet(self, Infos, totalNodule):
        '''
        This function calculates the desired formated list for the output excel
        :param Infos: the general infos from getDist functions
        :param totalNodule: the total number of nodules of the given infos
        :return:
        '''
        keys = ['Nodule Diameter', 'Total']
        keys.extend(self._typeKey)
        counter = {}
        counter['Nodule Diameter'] = ['Total']
        counter['Nodule Diameter'].extend(self._diameterKey)
        counter['Total'] = [totalNodule]
        percents = {}
        percents['Nodule Diameter'] = ['Total']
        percents['Nodule Diameter'].extend(self._diameterKey)
        percents['Total'] = ['100.0%']
        # formating the output lists as the desired excel format
        for k in self._diameterKey:
            counter['Total'].append(Infos[k][1])
            if totalNodule != 0:
                percents['Total'].append('%1.1f ' %(Infos[k][1] * 100.0 / totalNodule) + '%')
            else:
                percents['Total'].append('N/A')
        for i in range(len(self._typeKey)):
            sub_total = 0
            counter[self._typeKey[i]] = []
            percents[self._typeKey[i]] = []
            for k in self._diameterKey:
                counter[self._typeKey[i]].append(Infos[k][0][i])
                if totalNodule != 0:
                    percents[self._typeKey[i]].append('%1.1f' %(Infos[k][0][i] * 100.0 / totalNodule) + '%')
                else:
                    percents[self._typeKey[i]].append('N/A')
                sub_total += Infos[k][0][i]
            counter[self._typeKey[i]] = [sub_total] + counter[self._typeKey[i]]
            percents[self._typeKey[i]] = ['%1.1f' %(sub_total * 100.0 / totalNodule) + '%'] + percents[self._typeKey[i]]
        cnt_list = []
        per_list = []
        for k in keys:
            cnt_list.append(counter[k])
            per_list.append(percents[k])
        return np.asarray(cnt_list).T, np.asarray(per_list).T, keys

    def getStat(self):
        '''
        Evaluation for given keywords intervals
        '''
        for i in range(len(self._diameterInterval)):
            if i == 0:
                self._diameterKey.append("less_" + str(self._diameterInterval[i]))
            if i > 0 and i < len(self._diameterInterval):
                self._diameterKey.append(str(self._diameterInterval[i - 1]) + '_' + str(self._diameterInterval[i]))
            if i == len(self._diameterInterval) - 1:
                self._diameterKey.append(("greater_" + str(self._diameterInterval[i])))

        groupSize, countSize, totalNodule = self.getSizeDist(self._gt_info)
        groupType, countType, totalNodule = self.getTypeDist(self._gt_info)
        groupMalig, countMalig, totalNodule = self.getMaligDist(self._gt_info)

        total_Infos = {}
        for k in self._diameterKey:
            total_Infos[k] = {}
            _, countT, totalT = self.getTypeDist(groupSize[k])
            total_Infos[k] = [countT, totalT]
            total_Infos[k].append([round(c * 1.0 / totalT, 3) for c in countT])

        groupSize_M, countSize_M, totalNodule_M = self.getSizeDist(groupMalig['malign'])
        malign_Infos = {}
        for k in self._diameterKey:
            malign_Infos[k] = {}
            _, countT, totalT = self.getTypeDist(groupSize_M[k])
            malign_Infos[k] = [countT, totalT]
            malign_Infos[k].append([round(c * 1.0 /totalT, 3) for c in countT])

        groupSize_B, countSize_B, totalNodule_B = self.getSizeDist(groupMalig['benign'])
        benign_Infos = {}
        for k in self._diameterKey:
            benign_Infos[k] = {}
            _, countT, totalT = self.getTypeDist(groupSize_B[k])
            benign_Infos[k] = [countT, totalT]
            benign_Infos[k].append([round(c * 1.0 / totalT, 3) for c in countT])

        # write data distribution info into excel
        writer = pd.ExcelWriter(self._result_Path + self._filename + '_Sheets.xlsx', engine='xlsxwriter')

        df0 = pd.DataFrame({'--------------': []})
        df0.to_excel(writer, sheet_name='Sheet1', index=False, header=['--------------'])

        df1 = pd.DataFrame({'Total Number of Scan': [], '      ' : [], str(len(self._gt_files)): []})
        df1.to_excel(writer, sheet_name='Sheet1', index=False, header=['Total Number of Scan', '      ', str(len(self._gt_files))], startrow= 1)

        df2 = pd.DataFrame({'Total Number of Nodule': [], '      ' : [], str(totalNodule): []})
        df2.to_excel(writer, sheet_name='Sheet1', index=False, header=['Total Number of Nodule', '      ', str(totalNodule)], startrow=2)

        df3 = pd.DataFrame({'Total Distribution': []})
        df3.to_excel(writer, sheet_name='Sheet1', index=False, header=['Total Distribution'], startrow=4)

        df4 = pd.DataFrame({'# of Nodule': [], str(totalNodule): []})
        df4.to_excel(writer, sheet_name='Sheet1', index=False, header=['# of Nodule', str(totalNodule)], startrow=5)

        cnt_total, perc_total, keys = self.getxlsxSheet(total_Infos, totalNodule)
        df5 = pd.DataFrame(cnt_total)
        df5.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow = 6)

        df6 = pd.DataFrame(perc_total)
        df6.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow = 6, startcol = 9)

        df18 = pd.DataFrame({'Total Distribution': []})
        df18.to_excel(writer, sheet_name='Sheet1', index=False, header=['Total Distribution'], startrow=4, startcol=9)

        df7 = pd.DataFrame({'Percentage': []})
        df7.to_excel(writer, sheet_name='Sheet1', index=False, header=['Percentage'], startrow=5, startcol=9)

        df8 = pd.DataFrame({'Malign Distribution': []})
        df8.to_excel(writer, sheet_name='Sheet1', index=False, header=['Malign Distribution'], startrow=13)

        df9 = pd.DataFrame({'# of Nodule': [], str(totalNodule_M): []})
        df9.to_excel(writer, sheet_name='Sheet1', index=False, header=['# of Nodule', str(totalNodule_M)], startrow=14)

        cnt_total, perc_total, keys = self.getxlsxSheet(malign_Infos, totalNodule_M)
        df10 = pd.DataFrame(cnt_total)
        df10.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=15)

        df11 = pd.DataFrame(perc_total)
        df11.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=15, startcol=9)

        df19 = pd.DataFrame({'Malign Distribution': []})
        df19.to_excel(writer, sheet_name='Sheet1', index=False, header=['Malign Distribution'], startrow=13, startcol=9)

        df12 = pd.DataFrame({'Percentage': []})
        df12.to_excel(writer, sheet_name='Sheet1', index=False, header=['Percentage'], startrow=14, startcol=9)

        df13 = pd.DataFrame({'Benign Distribution': []})
        df13.to_excel(writer, sheet_name='Sheet1', index=False, header=['Benign Distribution'], startrow=22)

        df14 = pd.DataFrame({'# of Nodule': [], str(totalNodule_B): []})
        df14.to_excel(writer, sheet_name='Sheet1', index=False, header=['# of Nodule', str(totalNodule_B)], startrow=23)

        cnt_total, perc_total, keys = self.getxlsxSheet(benign_Infos, totalNodule_B)
        df15 = pd.DataFrame(cnt_total)
        df15.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=24)

        df16 = pd.DataFrame(perc_total)
        df16.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=24, startcol=9)

        df20 = pd.DataFrame({'Benign Distribution': []})
        df20.to_excel(writer, sheet_name='Sheet1', index=False, header=['Benign Distribution'], startrow=22, startcol=9)

        df17 = pd.DataFrame({'Percentage': []})
        df17.to_excel(writer, sheet_name='Sheet1', index=False, header=['Percentage'], startrow=23, startcol=9)

        writer.save()



if __name__ == '__main__':
    filename = 'test'
    gt_Path = '\\\\192.168.0.12\\Data\\Datasets\\Lung_Cancer\\JSPH\\nii\\'
    result_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\groundTruth\\'
    gt_postfix = '_gt_ym_1.2.json'
    keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    diameterScale = 1

    myGT = sigmaLU_DataDistribution(gt_Path, result_path, filename, gt_postfix, keywords, diameterScale)
    myGT.extractInfo()
    myGT.getStat()



