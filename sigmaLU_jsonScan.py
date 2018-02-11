# Author Siqi Qin
# Basic Parser for json file get from SigmaLU V0.4.5 +
# This parser covers all the contents in json files

import json
import sys

if sys.version_info[0] == 2:
    from io import open

platform = sys.platform
if platform.startswith('win'):
    slash = '\\'
elif platform.startswith('linux'):
    slash = '/'

# function to solve the problem of duplicated key ("item") in json files
def join_duplicate_keys(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           if type(d[k]) == list:
               d[k].append(v)
           else:
               newlist = []
               newlist.append(d[k])
               newlist.append(v)
               d[k] = newlist
        else:
           d[k] = v
    return d

# Nodule class is used for storing the info of each nodules
# _Verified indicates whether a verifiedNodule section exists for the nodule
class Nodule(object):
    def __init__(self, object, diameterScale, otherkeysNodule, otherkeysVerify):
        self._node = object
        self._diameterScale = diameterScale
        self._label = object['Label']
        self._maligScore = object['OrigDetMaligScore']
        self._detScore = object['OrigDetScore']
        self._AveDiameter = round(float(object['Radius'])*2,3)
        self._Center = [float(object['OrigDetCenter0']), float(object['OrigDetCenter1']), float(object['OrigDetCenter2'])]
        self._SegmentationDimX = float(object['SegmentationDimX'])
        self._SegmentationDimY = float(object['SegmentationDimY'])
        self._OrigDetScaleInVoxel0 = float(object['OrigDetScaleInVoxel0'])
        self._OrigDetScaleInVoxel1 = float(object['OrigDetScaleInVoxel1'])
        self._OrigDetScaleInVoxel2 = float(object['OrigDetScaleInVoxel2'])
        self._NoduleType = int(object['NoduleType'])
        self._Cal = object['IsCalcNodule']
        self._MaxDiameter = round(float(object["EllipsoidRadius2"])*2,3)
        self._Volume = round(float(object["Volume"]),3)
        self._AveHU = round(float(object["HUAve"]),3)
        self._otherKeysNodule = otherkeysNodule
        self._otherKeysVerify = otherkeysVerify
        self._otherDict = {}
        for k in self._otherKeysNodule:
            self._otherDict[k] = object[k]

        self._Verified = 'VerifiedNodule' in object
        if self._Verified:
            self._VerifiedNodule = VerifiedNodule(object['VerifiedNodule'], self._otherKeysVerify)
        self._MatchPair = []
    def getTypefromNodule(self):
        Solid, p_GGO, m_GGO, Calc, Solid_Calc, m_GGO_Calc= 'false', 'false', 'false', 'false', 'false', 'false'
        if self._Cal == 'false':
            if self._NoduleType == 0:
                Solid = 'true'
            elif self._NoduleType == 1:
                m_GGO = 'true'
            elif self._NoduleType == 2:
                p_GGO = 'true'
        else:
            if self._NoduleType == 0:
                Solid_Calc = 'true'
            elif self._NoduleType == 1:
                m_GGO_Calc = 'true'
            elif self._NoduleType != 2:
                Calc = 'true'

        return {'Solid':Solid, 'p_GGO':p_GGO, 'm_GGO':m_GGO, 'Calc':Calc, \
                'Solid_Calc':Solid_Calc, 'm_GGO_Calc':m_GGO_Calc}

    def getOtherKeys(self):
        return self._otherDict

    def getMaligScore(self):
        return float(self._maligScore)
    def getDetScore(self):
        return float(self._detScore)
    def getBoxShape(self):
        return [self._OrigDetScaleInVoxel0, self._OrigDetScaleInVoxel1, self._OrigDetScaleInVoxel2]
    def getDiameter(self):
        return max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * self._diameterScale
    def getLabel(self):
        return int(self._label)
    def getCenter(self):
        return self._Center
    def getVerifiedFlag(self):
        return self._Verified
    def getMatch(self):
        return self._MatchPair
    def getAveHU(self):
        return self._AveHU
    def getMaxDiameter(self):
        return self._MaxDiameter
    def getAveDiameter(self):
        return self._AveDiameter
    def getVolume(self):
        return self._Volume
# VerifiedNodule class is used for storing the info of each verified nodules
class VerifiedNodule(object):
    def __init__(self, object, otherskeys):
        self._node = object
        if 'labelIndex' in object:
            self._label = object['labelIndex']
        elif 'lablelIndex' in object:
            self._label = object['lablelIndex']
        else:
            print('Index key Error')

        if 'Center0' in object:
            self._Center = [object['Center0'], object['Center1'], object['Center2']]
        elif 'CenterX' in object:
            self._Center = [object['CenterX'], object['CenterY'], object['CenterZ']]
        else:
            print('No Center for VerifiedNodule', self._label)
        self._MaligFlag = object['Malign']
        self._NoduleFlag = object['True']

        self._otherKeys = otherskeys
        self._otherDict = {}
        for k in self._otherKeys:
            self._otherDict[k] = object[k]

        self._TypeDic = {'Solid':object['Solid'], 'p_GGO':object['GGO'],'m_GGO':object['Mixed'],'Calc':object['Calc']}
        Solid, p_GGO, m_GGO, Calc, Solid_Calc, m_GGO_Calc = 'false', 'false', 'false', 'false', 'false', 'false'
        if self._TypeDic['Calc'] == 'false':
            if self._TypeDic['Solid'] == 'true':
                Solid = 'true'
            elif self._TypeDic['m_GGO'] == 'true':
                m_GGO = 'true'
            elif self._TypeDic['p_GGO'] == 'true':
                p_GGO = 'true'
        else:
            if self._TypeDic['Solid'] == 'true':
                Solid_Calc = 'true'
            elif self._TypeDic['m_GGO'] == 'true':
                m_GGO_Calc = 'true'
            elif self._TypeDic['p_GGO'] == 'false':
                Calc = 'true'

        self._FinalTypeDic = {'Solid':Solid, 'p_GGO':p_GGO, 'm_GGO':m_GGO, 'Calc':Calc, \
                'Solid_Calc':Solid_Calc, 'm_GGO_Calc':m_GGO_Calc}

    def getOtherKeys(self):
        return self._otherDict

    def getLabel(self):
        return int(self._label)
    def getCenter(self):
        return self._Center
    def getMaligFlag(self):
        return self._MaligFlag
    def getNoduleFlag(self):
        return self._NoduleFlag
    def getTypeDic(self):
        return self._FinalTypeDic

# Scan is the basic parser for json files
class sigmaLU_Scan(object): # takes sigmaLU json result file as input
    def __init__(self, filename, diameterScale, othersKeysNodule = None, othersKeysVerify = None):
        self._filename = filename
        self._othersKeysNodule = []
        self._othersKeysNVerify = []
        if othersKeysNodule != None:
            self._othersKeysNodule = othersKeysNodule
        if othersKeysVerify != None:
            self._othersKeysNVerify = othersKeysVerify
        # scale for radius calculation
        self._diameterScale = diameterScale

        self._otherKeysNoduleDict = {}
        self._otherKeysVerifyDict = {}

        # info from detection
        self._maligDict = {}
        self._noduleDiameter = {}
        self._obj = json.loads(open(filename, 'r', encoding='utf8').read(), object_pairs_hook = join_duplicate_keys)
        self._count = int(self._obj['Nodules']['count'])
        self._version = self._obj['Nodules']['version']
        self._centerDict = {}
        self._detDict = {}
        # info from verified (gt)
        self._verifiedCenterDict = {}
        self._verifiedMaligFlagDict = {}
        self._verifiedNoduleFlagDict = {}
        self._verifiedTypeDict = {}
        self._NoduleTypeDict = {}
        self._VerifiedDict = {}
        self._MissedCenterDict = {}
        self._MissedMaligFlagDict = {}
        self._MissedNoduleFlagDict = {}
        self._MissedTypeDict = {}
        self._MatchPairs = {}
        self._boxShape = {}

        self._MaxDiameterDict = {}
        self._AveDiameterDict = {}
        self._VolumeDict = {}
        self._AveHUDict = {}

        # _LabelMatchPair solves the potential problems of label mismatching in nodule and verified nodule
        # in early version, the labels for missing nodules are negative
        self._LabelMatchPair = {}
        #print("nodule count = ", self._count)

    def parseAllNodules(self):
        if 'item' in self._obj['Nodules']:
            noduleNode = self._obj['Nodules']['item']
            # parse nodules
            if noduleNode != None:
                #print ("Start process nodules")
                if type(noduleNode) == dict:
                    noduleNode = [noduleNode]
                for child in noduleNode:
                    curNode = Nodule(child, self._diameterScale, self._othersKeysNodule, self._othersKeysNVerify)
                    label = curNode.getLabel()
                    malig = curNode.getMaligScore()

                    self._otherKeysNoduleDict[label] = curNode.getOtherKeys()
                    self._AveDiameterDict[label] = curNode.getAveDiameter()
                    self._MaxDiameterDict[label] = curNode.getMaxDiameter()
                    self._AveHUDict[label] = curNode.getAveHU()
                    self._VolumeDict[label] = curNode.getVolume()
                    self._maligDict[label] = malig
                    self._noduleDiameter[label] = curNode.getDiameter()
                    self._centerDict[label] = curNode.getCenter()
                    self._detDict[label] = curNode.getDetScore()
                    self._VerifiedDict[label] = curNode.getVerifiedFlag()
                    self._MatchPairs[label] = curNode.getMatch()
                    self._NoduleTypeDict[label] = curNode.getTypefromNodule()
                    self._boxShape[label] = curNode.getBoxShape()
                    # in early version, all verified and missing nodules are labeled as verified
                    # in early version, all truly verified nodules are labeled positive and missed nodules are negative
                    # in later version, if all verified and missing nodules are labeled positive, they will all be stored in verifiedNodule section
                    if curNode.getVerifiedFlag():
                        verifiedNode = curNode._VerifiedNodule
                        self._LabelMatchPair[label] = verifiedNode.getLabel()
                        if verifiedNode.getLabel() >= 0:
                            self._verifiedCenterDict[label] = verifiedNode.getCenter()
                            self._verifiedMaligFlagDict[label] = verifiedNode.getMaligFlag()
                            self._verifiedNoduleFlagDict[label] = verifiedNode.getNoduleFlag()
                            self._verifiedTypeDict[label] = verifiedNode.getTypeDic()
                            self._otherKeysVerifyDict[label] = verifiedNode.getOtherKeys()
                        else:
                            self._MissedCenterDict[label] = verifiedNode.getCenter()
                            self._MissedMaligFlagDict[label] = verifiedNode.getMaligFlag()
                            self._MissedNoduleFlagDict[label] = verifiedNode.getNoduleFlag()
                            self._MissedTypeDict[label] = verifiedNode.getTypeDic()


    def getCount(self):
        return self._count

    def getVersion(self):
        return self._version

    def getOtherKeysNodule(self, index, key):
        return self._otherKeysNoduleDict[index][key]

    def getBoxShape(self, index):
        return self._boxShape[index]

    def getVerifiedStatus(self, index):
        return index in self._LabelMatchPair

    def getLabelMatchPair(self, index):
        return self._LabelMatchPair[index]

    def getTypefromVerify(self, index):
        return self._verifiedTypeDict[index]

    def getTypefromNodule(self, index):
        return self._NoduleTypeDict[index]

    def addMatch(self, index, match):
        self._MatchPairs[index].append(match)

    def getDiameter(self, index):
        return self._noduleDiameter[index]

    def getMalignScore(self, index):
        return self._maligDict[index]

    def getDetScore(self, index):
        return self._detDict[index]

    def getNoduleCenter(self, index):
        return self._centerDict[index]

    def getOtherKeysVerified(self, index, key):
        if self._LabelMatchPair[index] >= 0:
            return self._otherKeysVerifyDict[index][key]
        else:
            print("No Verfied Nodule for Label ", index)

    def getVerifiedNoduleCenter(self, index):
        if self._LabelMatchPair[index] >= 0:
            return self._verifiedCenterDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getVerifiedMaligFlag(self, index):
        if self._LabelMatchPair[index] >= 0:
            return self._verifiedMaligFlagDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getVerifiedNoduleFlag(self, index):
        if self._LabelMatchPair[index] >= 0:
            return self._verifiedNoduleFlagDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getVerifiedNoduleType(self, index):
        if self._LabelMatchPair[index] >= 0:
            return self._verifiedTypeDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getMissedNoduleCenter(self, index):
        if self._LabelMatchPair[index] < 0:
            return self._MissedCenterDict[index]
        else:
            print("No Missed Nodule Pair for Label ", index)

    def getMissedMaligFlag(self, index):
        if self._LabelMatchPair[index] < 0:
            return self._MissedMaligFlagDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getMissedNoduleFlag(self, index):
        if self._LabelMatchPair[index] < 0:
            return self._MissedNoduleFlagDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getMissedNoduleType(self, index):
        if self._LabelMatchPair[index] < 0:
            return self._MissedTypeDict[index]
        else:
            print("No Verfied Nodule for Label ", index)

    def getMaxDiameter(self, index):
        return self._MaxDiameterDict[index]
    def getAveDiameter(self, index):
        return self._AveDiameterDict[index]
    def getVolume(self, index):
        return self._VolumeDict[index]
    def getAveHU(self, index):
        return self._AveHUDict[index]

# TEST SECTION
if __name__ == '__main__':
    # example for json file with verified section, missed labeled as negative
    othersNodule = ['PatientCoordBases', 'Volume']
    otherVerify = ['P_M', 'P_B']
    test = sigmaLU_Scan('PA12.json', 1, othersNodule)
    #test = sigmaLU_Scan('SHFK_339881_CAD_SYL.json', 1, othersNodule, otherVerify)
    test.parseAllNodules()
    print("Number of Nodules: ", test.getCount())
    for i in test._noduleDiameter:
        print("\n")
        print("Lable", i)
        print("Diameter: ", test.getDiameter(i))
        print("Malign: ", test.getMalignScore(i))
        print("Det: ", test.getDetScore(i))
        print("Center: ", test.getNoduleCenter(i))
        for o in othersNodule:
            print(o + ': ', test.getOtherKeysNodule(i, o))
        # use getVerifiedStatus to check is the verified Nodule exists for this label
        if test.getVerifiedStatus(i):
            print("VerifiedCenter: ", test.getVerifiedNoduleCenter(i))
            print("VerifiedMalignFlag: ", test.getVerifiedMaligFlag(i))
            print("VerifiedNoduleFlag: ", test.getVerifiedNoduleFlag(i))
            print("VerifiedNoduleType: ", test.getVerifiedNoduleType(i))
            for o in otherVerify:
                print(o + ': ', test.getOtherKeysVerified(i, o))
