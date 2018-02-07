from sigmaLU_jsonScan import sigmaLU_Scan
import csv
import os
import io
import sys
import pandas as pd
from sigmaLU_general import sigmaLU_General
pyVersion = 2
if sys.version_info[0] == 3:
    pyVersion = 3

class sigmaLU_Malign(sigmaLU_General):
    def __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, malignThre, diameterScale, typeSource):
        '''
        This is the sigmaLU_Malign class for malignancy evaluation between CAD detection and gt Doc
        Author: Siqi Qin
        :param filename: output file name
        :param detect_path: path to sigmaLU results
        :param gt_path: path to ground truth files
        :param result_path: path to all output files
        :param detect_postfix: postfix of the the results of sigmaLU, eg: 100012_T0.json, postfix = '.json'
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param keywords: keywords for malignancy
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        :param malignThre: threshold for malign
        :param diameterScale: in Scan, diameter = max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * iameterScale
        :param typeSource: control the source of nodule type in malign evaluation
                                0 : gt Doc, 1 : gt Detect, 2: CAD Detect
        '''
        sigmaLU_General. __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords)
        self._malignThre = malignThre
        self._typeSource = typeSource
        self._diameterScale = diameterScale
        self.readMe()

    def readMe(self):
        # manually add readMe files
        f = open(self._result_path + "readMe.txt", "w")
        f.write("This is the readMe file for malign evaluation \n")
        f.write("\n")
        f.write(self._filename + "_malign.csv stores the raw data of the malign model results \n")
        f.write(self._filename + "_mismatch.txt stores the nodules has no match in ground truth \n")
        f.write(self._filename + "_malign_StatSummary.csv stores the malign statistical results \n")
        f.write(self._filename + "_malign_Sheets.xlsx stores the malign statistical results in sheets format \n")
        f.write("//Curves folder stores the cumsum curves of different size interval and different type \n")
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
            # perform nodule matching
            self.compareGT(gt, de, name, self._log_dir)

            # add results of all matched nodules
            for dg in gt._verifiedMaligFlagDict:
                MaligDoct = gt.getVerifiedMaligFlag(int(dg))
                if MaligDoct == 'true':
                    MaligDoct = 1
                elif MaligDoct == 'false':
                    MaligDoct = 0
                gt_D = gt.getDiameter(int(dg))
                if len(gt._MatchPairs[dg]) != 0:
                    for m in gt._MatchPairs[dg]:
                        SigmaScore = de.getMalignScore(int(m))
                        if self._typeSource == 0:
                            TT = gt.getTypefromVerify(int(dg))
                        elif self._typeSource == 1:
                            TT = gt.getTypefromNodule(int(dg))
                        else:
                            print('Type source only from 0 = gt verify, 1 = gt CAD')
                            exit(1)
                        if gt.getVerifiedNoduleFlag(dg) == 'true':
                            self._maligList.append(
                                {'PID': name, 'Index': int(dg), 'MaligDoct': MaligDoct, 'Sigma MaligScore': SigmaScore,
                                 'SigmaResult': int(SigmaScore > self._malignThre), 'Diameter': gt_D,
                                 'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                            'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']})
                # record mismatched ones
                else:
                    self._mismatch.append(name + ' ' + str(dg))

            print(name + ' Done')

    def writeCSV(self):
        print("Number of Mismatch: ", len(self._mismatch))
        fieldnames = ['PID', 'Index', 'MaligDoct', 'Sigma MaligScore', 'SigmaResult', 'Diameter', 'Solid', 'p_GGO', \
                      'm_GGO', 'Calc', 'Solid_Calc', 'm_GGO_Calc']
        if pyVersion == 3:
            csvfile = open(self._result_path + self._filename + '_malign.csv', 'w', newline='')
        elif pyVersion == 2:
            csvfile = open(self._result_path + self._filename + '_malign.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in self._maligList:
            writer.writerow(d)

        f = open(self._result_path + self._filename + '_mismatch.txt', 'w')
        for i in self._mismatch:
            f.write(i + "\n")
        f.close()

    def getPlots(self):
        self.Grouping("malign")
        self.statResult("malign")

    def getSheetResults(self):
        '''
        read the raw stats info and reformat to store in excel
        '''
        pd_file = pd.read_csv(self._result_path + self._filename + '_malign_StatSummary.csv').fillna('N/A')
        precisionDict = {}
        accuracyDict = {}
        sensitivityDict = {}
        specificityDict = {}
        keywordsList = pd_file[['Unnamed: 0']].values
        precisionList = pd_file[['11']].values
        accuracyList = pd_file[['12']].values
        sensitivityList = pd_file[['7']].values
        specificityList = pd_file[['9']].values
        for idx in range(len(keywordsList)):
            precisionDict[keywordsList[idx][0]] = precisionList[idx][0]
            accuracyDict[keywordsList[idx][0]] = accuracyList[idx][0]
            sensitivityDict[keywordsList[idx][0]] = sensitivityList[idx][0]
            specificityDict[keywordsList[idx][0]] = specificityList[idx][0]

        sensPandaList = []
        s1List = ['Total', '%1.1f' % (float(sensitivityDict['all']) * 100.0) + '%']
        for tt in self._typekeys:
            if sensitivityDict[tt] == 'N/A':
                s1List.append('N/A')
            else:
                s1List.append('%1.1f' % (float(sensitivityDict[tt]) * 100.0) + '%')
        sensPandaList.append(s1List)
        for rr in self._diameterkey:
            sList = [rr]
            if sensitivityDict[rr] == 'N/A':
                sList.append('N/A')
            else:
                sList.append('%1.1f' % (float(sensitivityDict[rr]) * 100.0) + '%')
            for tt in self._typekeys:
                if sensitivityDict[rr + '_' + tt] == 'N/A':
                    sList.append('N/A')
                else:
                    sList.append('%1.1f' % (float(sensitivityDict[rr + '_' + tt]) * 100.0) + '%')
            sensPandaList.append(sList)

        specPandaList = []
        sp1List = ['Total', '%1.1f' % (float(specificityDict['all']) * 100.0) + '%']
        for tt in self._typekeys:
            if specificityDict[tt] == 'N/A':
                sp1List.append('N/A')
            else:
                sp1List.append('%1.1f' % (float(specificityDict[tt]) * 100.0) + '%')
        specPandaList.append(sp1List)
        for rr in self._diameterkey:
            spList = [rr]
            if specificityDict[rr] == 'N/A':
                spList.append('N/A')
            else:
                spList.append('%1.1f' % (float(specificityDict[rr]) * 100.0) + '%')
            for tt in self._typekeys:
                if specificityDict[rr + '_' + tt] == 'N/A':
                    spList.append('N/A')
                else:
                    spList.append('%1.1f' % (float(specificityDict[rr + '_' + tt]) * 100.0) + '%')
            specPandaList.append(spList)

        precPandaList = []
        p1List = ['Total', '%1.1f' %(float(precisionDict['all']) * 100.0) + '%']
        for tt in self._typekeys:
            if precisionDict[tt] == 'N/A':
                p1List.append('N/A')
            else:
                p1List.append('%1.1f' %(float(precisionDict[tt]) * 100.0) + '%')
        precPandaList.append(p1List)
        for rr in self._diameterkey:
            pList = [rr]
            if precisionDict[rr] == 'N/A':
                pList.append('N/A')
            else:
                pList.append('%1.1f' %(float(precisionDict[rr]) * 100.0) + '%')
            for tt in self._typekeys:
                if precisionDict[rr + '_' + tt] == 'N/A':
                    pList.append('N/A')
                else:
                    pList.append('%1.1f' %(float(precisionDict[rr + '_' + tt]) * 100.0) + '%')
            precPandaList.append(pList)

        accPandaList = []
        a1List = ['Total', '%1.1f' %(float(accuracyDict['all']) * 100.0) + '%']
        for tt in self._typekeys:
            if accuracyDict[tt] == 'N/A':
                a1List.append('N/A')
            else:
                a1List.append('%1.1f' %(float(accuracyDict[tt]) * 100.0) + '%')
        accPandaList.append(a1List)
        for rr in self._diameterkey:
            aList = [rr]
            if accuracyDict[rr] == 'N/A':
                aList.append('N/A')
            else:
                aList.append('%1.1f' %(float(accuracyDict[rr]) * 100.0) + '%')
            for tt in self._typekeys:
                if accuracyDict[rr + '_' + tt] == 'N/A':
                    aList.append('N/A')
                else:
                    aList.append('%1.1f' %(float(accuracyDict[rr + '_' + tt]) * 100.0) + '%')
            accPandaList.append(aList)

        writer = pd.ExcelWriter(self._result_path + self._filename + '_malign_Sheets.xlsx', engine='xlsxwriter')
        df1 = pd.DataFrame({'Precision': []})
        df1.to_excel(writer, sheet_name='Sheet1', index=False, header=['Precision'])

        keys = ['Nodule Diameter', 'Total']
        keys.extend(self._typekeys)
        df2 = pd.DataFrame(precPandaList)
        df2.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=1)

        df3 = pd.DataFrame({'Accuracy': []})
        df3.to_excel(writer, sheet_name='Sheet1', index=False, header=['Accuracy'], startrow=8)

        df4 = pd.DataFrame(accPandaList)
        df4.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=9)

        df5 = pd.DataFrame({'Sensitivity': []})
        df5.to_excel(writer, sheet_name='Sheet1', index=False, header=['Sensitivity'], startrow=16)

        df6 = pd.DataFrame(sensPandaList)
        df6.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=17)

        df7 = pd.DataFrame({'Specificity': []})
        df7.to_excel(writer, sheet_name='Sheet1', index=False, header=['Specificity'], startrow=24)

        df8 = pd.DataFrame(specPandaList)
        df8.to_excel(writer, sheet_name='Sheet1', index=False, header=keys, startrow=25)

        writer.save()




# TEST SECTION
if __name__ == '__main__':
    filename = 'test'
    detect_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\malign\\result\\'
    gt_path = '\\\\192.168.0.12\\Data\\Datasets\\Lung_Cancer\\JSPH\\nii\\'
    result_path = 'C:\\Work\\github\\SigmaCAD\\automation_tools\\evaluationTools\\test\\malign\\'
    detect_postfix = '.json'
    gt_postfix = '_gt_ym_1.2.json'
    keywords = [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
    diameterScale = 0.7
    malignThre = 0.5
    maligtypeSource = 0

    myMalign = sigmaLU_Malign(filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, malignThre, diameterScale, maligtypeSource)
    myMalign.compare()
    myMalign.writeCSV()
    myMalign.getPlots()