import sys
import os
import io
from sigmaLU_profiling import sigmaLU_Profile
from sigmaLU_malign import sigmaLU_Malign
from sigmaLU_detect import sigmaLU_Detect
from sigmaLU_dataDistribution import sigmaLU_DataDistribution
from sigmaLU_typeClassify import sigmaLU_TypeClassify
from sigmaLU_malignGT import sigmaLU_MalignGT

import pandas as pd
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


platform = sys.platform
if platform.startswith('win'):
    slash = '\\'
elif platform.startswith('linux'):
    slash = '/'

class EvaluateSigmaLU(object):
    def __init__(self, filename, gt_path, detect_path, eval_file_path, eval_choices, det_keywords, malig_keywords, \
                classify_keywords, profile_keywords, distribution_keywords, det_postfix, gt_postfix, maligThre, diameterScale, GTtypeSource):
        '''
        This is the evaluateSigmaLU class for Lung results evaluation
        Author : Siqi Qin
        :param filename: output file name
        :param gt_path: path to ground truth files
        :param detect_path: path to sigmaLU results
        :param eval_file_path: path to all output files
        :param eval_choices: modules to evaluation (set to 1 if evaluate): [DataDistribution, detect, malign, type classify, profiling, malignGT]
        :param det_keywords: keywords for detection
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        :param malig_keywords: keywords for malignancy
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        :param classify_keywords: keywords for type classification
                         eg: [[8, 20]]
                         format: keywords[0] is the keywords for diameter
        :param profile_keywords: profiling keywords to extract time
        :param distribution_keywords: keywords for data distribution
                         eg: [[8, 20], ["Solid", "GGO", "Mixed", "Cal"]]
                         format: keywords[0] is the keywords for diameter
                                 keywords[1] is the keywords for nodule type
        :param det_postfix: postfix of the the results of sigmaLU, eg: 100012_T0.json, postfix = '.json'
        :param gt_postfix: postfix of the gt, eg: 100012_T0_gt_ym_1.2.json, postfix = '_gt_ym_1.2.json'
        :param maligThre: threshold for malign
        :param diameterScale: in Scan, diameter = max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * iameterScale
        :param GTtypeSource: control the source of nodule type in malign evaluation
                                0 : gt Doc, 1 : gt Detect
        '''
        self._filename = filename
        self._gt_path = gt_path
        self._detect_path = detect_path
        self._eval_file_path = eval_file_path
        self._eval_choices = eval_choices
        self._det_keywords = det_keywords
        self._malig_keywords = malig_keywords
        self._classify_keywords = classify_keywords
        self._profile_keywords = profile_keywords
        self._distribution_keywords = distribution_keywords
        self._det_postfix = det_postfix
        self._gt_postfix = gt_postfix
        self._maligThre = maligThre
        self._diameterScale = diameterScale
        self._GTtypeSource = GTtypeSource

    def evaluate(self):
        if os.path.isdir(self._eval_file_path) == False:
            os.mkdir(self._eval_file_path)

        # data Distribution
        if self._eval_choices[0] == 1:
            print("\n")
            print("***************Run Data Distribution***************")
            print("\n")
            eval_dd_path = self._eval_file_path + 'dataDistribution' + slash
            myGT = sigmaLU_DataDistribution(self._gt_path, eval_dd_path , filename, gt_postfix,  \
                   self._distribution_keywords, self._diameterScale, self._GTtypeSource)
            myGT.extractInfo()
            myGT.getStat()

        # detect
        if self._eval_choices[1] == 1:
            print("\n")
            print("***************Run Detection***************")
            print("\n")
            eval_detect_path = self._eval_file_path + 'detect' + slash
            myDetect = sigmaLU_Detect(self._filename, self._detect_path, self._gt_path, eval_detect_path, self._det_postfix, \
                              self._gt_postfix, self._det_keywords, self._diameterScale, self._maligThre, self._GTtypeSource)
            myDetect.compare()
            myDetect.writeCSV()
            myDetect.getPlots()

        # malign
        if self._eval_choices[2] == 1:
            print("\n")
            print("***************Run Malignancy***************")
            print("\n")
            eval_malig_path = self._eval_file_path + 'malign' + slash
            myMalign = sigmaLU_Malign(self._filename, self._detect_path, self._gt_path, eval_malig_path, self._det_postfix, \
                              self._gt_postfix, self._malig_keywords, self._maligThre, self._diameterScale, self._GTtypeSource)
            myMalign.compare()
            myMalign.writeCSV()
            myMalign.getPlots()
            myMalign.getSheetResults()

        # type classify
        if self._eval_choices[3] == 1:
            print("\n")
            print("***************Run Type Classification***************")
            print("\n")
            eval_classify_path = self._eval_file_path + 'classify' + slash
            myTypeClassify = sigmaLU_TypeClassify(self._filename, self._detect_path, self._gt_path, eval_classify_path, \
                                          self._det_postfix, self._gt_postfix, self._classify_keywords, self._diameterScale, self._GTtypeSource)
            myTypeClassify.extractInfo()
            myTypeClassify.writeCSV()
            myTypeClassify.getMatrix()

        # profiling
        if self._eval_choices[4] == 1:
            print("\n")
            print("***************Run Profiling***************")
            print("\n")
            eval_profile_path = self._eval_file_path + 'profile' + slash
            myProfile = sigmaLU_Profile(self._filename, self._detect_path, eval_profile_path, \
                                self._profile_keywords, self._det_postfix)
            myProfile.extractInfo()
            myProfile.writeCSV()

        # malign GT
        if self._eval_choices[5] == 1:
            print("\n")
            print("***************Run Malignancy GT***************")
            print("\n")
            eval_maligGT_path = self._eval_file_path + 'malignGT' + slash
            myMalignGT = sigmaLU_MalignGT(self._filename, self._detect_path, self._gt_path, eval_maligGT_path, self._det_postfix, \
                              self._gt_postfix, self._malig_keywords, self._maligThre, self._diameterScale, self._GTtypeSource)
            myMalignGT.extractInfo()
            myMalignGT.writeCSV()
            myMalignGT.getPlots()
            myMalignGT.getSheetResults()

    def getReport(self):
        doc = SimpleDocTemplate(self._eval_file_path + self._filename + "_Report.pdf", pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        Story = []
        logo = "logo.jpg"

        Story.append(Spacer(1, 150))
        im = Image(logo, 5 * inch, 2 * inch)
        Story.append(im)
        Story.append(Spacer(1, 150))
        ptext = '<font size=20>12 Sigma Auto-Evaluation Report</font>'
        Story.append(Paragraph(ptext, styles["Title"]))
        Story.append(Spacer(1, 210))
        ptext = '<font size=20> Summary </font>'
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 20))
        ptext = '<font size=12> Welcome to 12 Sigma Auto Evalution System ! </font>'
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12> You are using the detection results at: </font>'
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12> %s </font>' % self._detect_path
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12> And the ground truth files are at: </font>'
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12> %s </font>' % self._gt_path
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 30))

        if self._eval_choices[0] == 1:
            ptext = '<font size=20> Data Distribution </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))

            # write ground truth
            dd_Stat_File = self._eval_file_path + 'dataDistribution' + slash + self._filename + '_Sheets.xlsx'
            pd_Dist = pd.read_excel(dd_Stat_File).fillna('         ')
            widths = [100]
            widths.extend([50] * (pd_Dist.shape[1] - 1))

            for i in range(pd_Dist.shape[0]):
                Story.append(Table([pd_Dist.take([i], axis=0).values.tolist()[0][:9]], colWidths=widths))
            for i in range(pd_Dist.shape[0]):
                Story.append(Table([pd_Dist.take([i], axis=0).values.tolist()[0][9:]], colWidths=widths))

            Story.append(Spacer(1, 30))

        if self._eval_choices[1] == 1:
            ptext = '<font size=20> Detection </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))
            det_Stat_File = self._eval_file_path + 'detect' + slash + self._filename + '_detect_StatSummary.csv'
            pd_Det = pd.read_csv(det_Stat_File).fillna('N/A')
            widths = [100]
            widths.extend([50] * (pd_Det.shape[1] - 1))
            for i in range(pd_Det.shape[0]):
                Story.append(Table(pd_Det.take([i], axis=0).values.tolist(), colWidths = widths))
            det_roc_all = self._eval_file_path + 'detect' + slash + 'ROC' + slash + 'Group_all.png'
            Story.append(Spacer(1, 20))
            im = Image(det_roc_all, 5 * inch, 3 * inch)
            Story.append(im)

            # write malign
            Story.append(Spacer(1, 30))

        if self._eval_choices[2] == 1:
            ptext = '<font size=20> Malign </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))
            mal_Stat_File = self._eval_file_path + 'malign' + slash + self._filename + '_malign_StatSummary.csv'
            pd_Mal = pd.read_csv(mal_Stat_File).fillna('N/A')
            widths = [90]
            widths.extend([30] * 11)
            widths.extend([45] * 2)
            for i in range(pd_Mal.shape[0]):
                Story.append(Table(pd_Mal.take([i], axis=0).values.tolist(), colWidths = widths))
            mal_curve_all = self._eval_file_path + 'malign' + slash + 'Curves' + slash + 'Group_all.png'
            Story.append(Spacer(1, 20))
            im = Image(mal_curve_all, 5 * inch, 3 * inch)
            Story.append(im)

            # write type class
            Story.append(Spacer(1, 30))

        if self._eval_choices[3] == 1:
            ptext = '<font size=20> Type Classification </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))
            ptext = '<font size=15> Overall Confusion Matrix </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))
            type_Stat_File = self._eval_file_path + 'classify' + slash + 'Matrix' + slash + self._filename + '_all_classifyStat.csv'
            pd_type = pd.read_csv(type_Stat_File).fillna('N/A')
            widths = [75] * 8
            for i in range(pd_type.shape[0]):
                Story.append(Table(pd_type.take([i], axis=0).values.tolist(), colWidths = widths))

            # write runtime profile
            Story.append(Spacer(1, 30))

        if self._eval_choices[4] == 1:
            ptext = '<font size=20> Profiling </font>'
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 20))
            run_Stat_File = self._eval_file_path + 'profile' + slash + self._filename + '_profile_summary.csv'
            with open(run_Stat_File, 'r') as f:
                for m in f.readlines():
                    ptext = '<font size=12> %s </font>' % m
                    Story.append(Paragraph(ptext, styles["Normal"]))
                    Story.append(Spacer(1, 12))

        doc.build(Story)




if __name__ == '__main__':
    filename = 'test'
    if platform.startswith('win'):
        gt_path = 'C:\\user\\zgu\\wuhan_tongji-data-analysis\\'
        detect_path = 'C:\\user\\zgu\\wuhan_tongji-data-analysis\\'
        #gt_path = '\\\\192.168.0.12\\Data\\Datasets\\Lung_Cancer\\JSPH\\nii\\'
        #detect_path = '\\\\192.168.0.12\\Data\\Data02\\Results\\Lung_Cancer\\JSPH\\JSPHresult_nii_test_20171009_v0.5.2\\'
        eval_file_path = 'C:\\user\\zgu\\wuhan_tongji-data-analysis\\'
    elif platform.startswith('linux'):
        gt_path = '/media/Data/Datasets/Lung_Cancer/JSPH/nii/'
        detect_path = '/media/Data/Data02/Results/Lung_Cancer/JSPH/JSPHresult_nii_test_20171009_v0.5.2_linux/'
        eval_file_path = '/home/user/Siqi/evaluationSigma/test/'

    eval_choices = [1, 1, 1, 1, 1, 1]
    det_keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    malig_keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    distribution_keywords = [[8, 20], ["Solid", "p_GGO", "m_GGO", "Calc", 'Solid_Calc', 'm_GGO_Calc']]
    classify_keywords = [[8, 20]]
    profile_keywords = ['after read in volume', 'after normalization',
            'after segmentation', 'after 3D 1st stage processing',
            'after 2nd stage processing', 'after Nodule Segmentation',
            'after nodule malignancy classification',
            'after post processing',
            'after compute Nodule Stats', 'after Lung-RADS']
    det_postfix = '.json'
    gt_postfix = '_gt.json'
    maligThre = 0.5
    diameterScale = 1
    GTtypeSource = 0

    myReport = EvaluateSigmaLU(filename, gt_path, detect_path, eval_file_path, eval_choices, det_keywords, malig_keywords, \
    classify_keywords, profile_keywords, distribution_keywords, det_postfix, gt_postfix, maligThre, diameterScale, GTtypeSource)

    myReport.evaluate()
    myReport.getReport()
