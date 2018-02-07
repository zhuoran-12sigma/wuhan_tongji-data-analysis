# Author Siqi Qin
# Basic Parser for json file get from SigmaLU V0.4.5 +
# This parser covers all the contents in json files

import json
import sys
import numpy as np
import os

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
    def __init__(self, object, diameterScale):
        self._node = object
        self._diameterScale = diameterScale
        self._label = object['Label']
        self._maligScore = object['OrigDetMaligScore']
        self._detScore = object['OrigDetScore']
        self._Radius = object['Radius']
        self._Center = [float(object['OrigDetCenter0']), float(object['OrigDetCenter1']), float(object['OrigDetCenter2'])]
        self._SegmentationDimX = float(object['SegmentationDimX'])
        self._SegmentationDimY = float(object['SegmentationDimY'])
        self._OrigDetScaleInVoxel0 = float(object['OrigDetScaleInVoxel0'])
        self._OrigDetScaleInVoxel1 = float(object['OrigDetScaleInVoxel1'])
        self._OrigDetScaleInVoxel2 = float(object['OrigDetScaleInVoxel2'])
        self._NoduleType = int(object['NoduleType'])
        self._Cal = object['IsCalcNodule']
        self._Verified = 'VerifiedNodule' in object
        if self._Verified:
            self._VerifiedNodule = VerifiedNodule(object['VerifiedNodule'])
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

# VerifiedNodule class is used for storing the info of each verified nodules
class VerifiedNodule(object):
    def __init__(self, object):
        self._node = object
        self._label = object['lablelIndex']
        self._Center = [object['Center0'], object['Center1'], object['Center2']]
        self._MaligFlag = object['Malign']
        self._NoduleFlag = object['True']
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
    def __init__(self, filename, diameterScale):
        self._filename = filename
        # scale for radius calculation
        self._diameterScale = diameterScale
        # info from detection
        self._maligDict = {}
        self._noduleDiameter = {}
        self._obj = json.loads(open(filename).read(), object_pairs_hook = join_duplicate_keys)
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
                    curNode = Nodule(child, self._diameterScale)
                    label = curNode.getLabel()
                    malig = curNode.getMaligScore()
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
                        else:
                            self._MissedCenterDict[label] = verifiedNode.getCenter()
                            self._MissedMaligFlagDict[label] = verifiedNode.getMaligFlag()
                            self._MissedNoduleFlagDict[label] = verifiedNode.getNoduleFlag()
                            self._MissedTypeDict[label] = verifiedNode.getTypeDic()


    def getCount(self):
        return self._count

    def getVersion(self):
        return self._version

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

# TEST SECTION
if __name__ == '__main__':
    # example for json file with verified section, missed labeled as negative
    test = sigmaLU_Scan('ZSBenignCT01001.json', 0.7)
    print("Number of Nodules: ", test.getCount())
    for i in range(test.getCount()):
        print("\n")
        print("Lable", i)
        print("Radius: ", test.getDiameter(i))
        print("Malign: ", test.getMalignScore(i))
        print("Det: ", test.getDetScore(i))
        print("Center: ", test.getNoduleCenter(i))
        # use getVerifiedStatus to check is the verified Nodule exists for this label
        if test.getVerifiedStatus(i):
            if test.getMatchPair(i) >= 0:
                print("VerifiedCenter: ", test.getVerifiedNoduleCenter(i))
                print("VerifiedMalignFlag: ", test.getVerifiedMaligFlag(i))
                print("VerifiedNoduleFlag: ", test.getVerifiedNoduleFlag(i))
                print("VerifiedNoduleType: ", test.getVerifiedNoduleType(i))
            else:
                print("MissededCenter: ", test.getMissedNoduleCenter(i))
                print("MissedMalignFlag: ", test.getMissedMaligFlag(i))
                print("MissedNoduleFlag: ", test.getMissedNoduleFlag(i))
                print("MissedNoduleType: ", test.getMissedNoduleType(i))

    # example for json file without verified section
    print("\n\n")
    test = sigmaLU_Scan('ZSBenignCT01001_gt.json', 0.7)
    print("Number of Nodules: ", test.getCount())
    for i in range(test.getCount()):
        print("\n")
        print("Lable", i)
        print("Radius: ", test.getDiameter(i))
        print("Malign: ", test.getMalignScore(i))
        print("Det: ", test.getDetScore(i))
        print("Center: ", test.getNoduleCenter(i))
        # use getVerifiedStatus to check is the verified Nodule exists for this label
        if test.getVerifiedStatus(i):
            # verified nodules
            if test.getMatchPair(i) >= 0:
                print("VerifiedCenter: ", test.getVerifiedNoduleCenter(i))
                print("VerifiedMalignFlag: ", test.getVerifiedMaligFlag(i))
                print("VerifiedNoduleFlag: ", test.getVerifiedNoduleFlag(i))
                print("VerifiedNoduleType: ", test.getVerifiedNoduleType(i))
            # missing nodules
            else:
                print("MissededCenter: ", test.getMissedNoduleCenter(i))
                print("MissedMalignFlag: ", test.getMissedMaligFlag(i))
                print("MissedNoduleFlag: ", test.getMissedNoduleFlag(i))
                print("MissedNoduleType: ", test.getMissedNoduleType(i))