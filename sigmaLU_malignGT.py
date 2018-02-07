from sigmaLU_malign import sigmaLU_Malign
from sigmaLU_jsonScan import sigmaLU_Scan
from os import listdir

class sigmaLU_MalignGT(sigmaLU_Malign):
    def __init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, malignThre, diameterScale, typeSource):
        '''
        This is the sigmaLU_MalignGT class for malignancy evaluation between gt detection and gt Doc
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
        :param typeSource: control the source of nodule type in malignGT evaluation
                                0 : gt Doc, 1 : gt Detect
        '''
        sigmaLU_Malign.__init__(self, filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, malignThre, diameterScale, typeSource)
        self._gt_files = list(filter(lambda x: self._gt_postfix in x and x.split('.')[-1] == 'json', listdir(self._gt_path)))

    def extractInfo(self):
        # loop through all gt files and extract the detect and doc infos
        for gt in self._gt_files:
            name = gt.split(self._gt_postfix)[0]
            gtScan = sigmaLU_Scan(self._gt_path + name + self._gt_postfix, self._diameterScale)
            gtScan.parseAllNodules()
            if gtScan.getCount() == 0:
                print('No Nodule for ' + name)
                continue
            for dg in gtScan._noduleDiameter:
                MaligDoct = gtScan.getVerifiedMaligFlag(int(dg))
                if MaligDoct == 'true':
                    MaligDoct = 1
                elif MaligDoct == 'false':
                    MaligDoct = 0
                gt_D = gtScan.getDiameter(int(dg))
                SigmaScore = gtScan.getMalignScore(dg)
                if self._typeSource == 0:
                    TT = gtScan.getTypefromVerify(int(dg))
                elif self._typeSource == 1:
                    TT = gtScan.getTypefromNodule(int(dg))
                else:
                    print('Type source only from 0 = gt verify, 1 = gt CAD')
                    exit(1)
                if gtScan.getVerifiedNoduleFlag(dg) == 'true':
                    self._maligList.append(
                        {'PID': name, 'Index': int(dg), 'MaligDoct': MaligDoct, 'Sigma MaligScore': SigmaScore,
                         'SigmaResult': int(SigmaScore > self._malignThre), 'Diameter': gt_D,
                         'Solid': TT['Solid'], 'p_GGO': TT['p_GGO'], 'm_GGO': TT['m_GGO'], \
                         'Calc': TT['Calc'], 'Solid_Calc': TT['Solid_Calc'], 'm_GGO_Calc': TT['m_GGO_Calc']})
            print(name + ' done')

# TEST SECTION
if __name__ == '__main__':
    filename = 'test'
    detect_path = '\\\\192.168.0.12\\Data02\\Data\\Results\\Lung_Cancer\\SHFK\\result_20180105_json\\'
    gt_path = '\\\\192.168.0.12\\Data02\\Data\\Results\\Lung_Cancer\\SHFK\\gt_20180122_updatedMaligStatusSameAsPM\\'
    result_path = 'C:\\Users\\siqi\\Desktop\\evaluationSiqi\\SigmaPy\\shared\\evaluation_tools\\sigmaLU\\malignGT\\'
    detect_postfix = '.json'
    gt_postfix = '_gt.json'
    keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    diameterScale = 1
    sourceType = 0
    malignThre = 0.5

    myMalign = sigmaLU_MalignGT(filename, detect_path, gt_path, result_path, detect_postfix, gt_postfix, keywords, malignThre, diameterScale, sourceType)
    myMalign.extractInfo()
    myMalign.writeCSV()
    myMalign.getPlots()
    myMalign.getSheetResults()