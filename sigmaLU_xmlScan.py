import untangle
import xml.etree.ElementTree as ET
import os

class Nodule(object): # takes a xml node and index as input
    def __init__(self, object):
        self._node = object
        self._label = int(self._node.find('Label').text)
        self._maligScore = float(self._node.find('OrigDetMaligScore').text)
        self._Radius = float(self._node.find('Radius').text)
        self._SegmentationDimX = float(self._node.find('SegmentationDimX').text)
        self._SegmentationDimY = float(self._node.find('SegmentationDimY').text)
        self._Center = [float(self._node.find('CenterX').text), float(self._node.find('CenterY').text),
                        float(self._node.find('CenterZ').text)]
        self._MatchPair = []
    def getMaligScore(self):
        return float(self._maligScore)
    def getRadius(self):
        return max(0.5, (self._SegmentationDimX + self._SegmentationDimY) / 2) * 0.7
    def getLabel(self):
        return int(self._label)
    def getCenter(self):
        return self._Center
    def getMatch(self):
        return self._MatchPair

class VerifiedInfo(object): # takes a xml node and index as input
    def __init__(self, object):
        self._node = object
        self._malignFlag = int(self._node.find('Malign').text)
        self._label = int(self._node.find('LabelIndex').text)
        self._Solid = int(self._node.find('Solid').text)
        self._GGO = int(self._node.find('GGO').text)
        self._Mixed = int(self._node.find('Mixed').text)
        self._Calc = int(self._node.find('Calc').text)
    def getLabel(self):
        return int(self._label)
    def getMalignFlag(self):
        return int(self._malignFlag)
    def getNoduleType(self):
        return [self._Solid, self._GGO, self._Mixed, self._Calc]

# might be remove in the future
class MissedInfo(object):
    def __init__(self, object):
        self._node = object
        self._malignFlag = int(self._node.find('Malign').text)
        self._label = int(self._node.find('LabelIndex').text)
    def getLabel(self):
        return int(self._label)
    def getMalignFlag(self):
        return int(self._malignFlag)

class sigmaLU_Scan(object): # takes sigmaLU result file as input
    def __init__(self, filename):
        self._filename = filename
        self._maligDict = {}
        self._verifiedMaligDict = {}
        self._missedMaligDict = {}
        self._noduleRadius = {}
        self._obj = untangle.parse(self._filename)
        self._count = int(self._obj.boost_serialization.Nodules.count.cdata)
        self._missedMaligNoduleCount = 0
        self._centerDict = {}
        self._MatchPairs = {}
        self._noduleTypeDict = {}
        #print("nodule count = ", self._count)

    def parseAllNodules(self):
        root = ET.parse(self._filename).getroot()
        noduleNode = root.find('Nodules')
        verifiedNode = root.find('VerifiedNodules')
        missedNoduleNode = root.find('MissedNodules')
        # parse nodules
        if noduleNode != None:
            #print ("Start process nodules")
            for child in noduleNode.findall("item"):
                curNode = Nodule(child)
                label = curNode.getLabel()
                malig = curNode.getMaligScore()
                self._maligDict[label] = malig
                self._noduleRadius[label] = curNode.getRadius()
                self._centerDict[label] = curNode.getCenter()
                self._MatchPairs[label] = curNode.getMatch()

        # parse verified nodules
        if verifiedNode != None:
            #print("Start process verified nodules")
            for child in verifiedNode.findall("item"):
                curVerifiedInfo = VerifiedInfo(child)
                verifiedLabel = curVerifiedInfo.getLabel()
                verifiedMaligFlag = curVerifiedInfo.getMalignFlag()
                self._verifiedMaligDict[verifiedLabel] = verifiedMaligFlag
                self._noduleTypeDict[verifiedLabel] = curVerifiedInfo.getNoduleType()

        # parse missed nodules
        if missedNoduleNode != None:
            flag = -1
            #print ("Start process missed nodules")
            for child in missedNoduleNode.findall("item"):
                missedItem = MissedInfo(child)
                missedLabel = flag
                missedMaligFlag = int(missedItem.getMalignFlag())
                self._missedMaligDict[missedLabel] = missedMaligFlag
                flag = flag -1


    def getMaligScoreFromNodule(self, index): # return [maligFlag, maligScore]
        #self.parseAllNodules()
        return float(self._maligDict[index])

    def getRadiusFromNodule(self, index): # return [maligFlag, maligScore]
        #self.parseAllNodules()
        return float(self._noduleRadius[index])

    def getCenter(self, index): # return [maligFlag, maligScore]
        #self.parseAllNodules()
        return self._centerDict[index]

    def getVerifiedMaligFlag(self, index):
        #self.parseAllNodules()
        return int(self._verifiedMaligDict[index])

    def getMissedMaligNoduleNum(self):
        #self.parseAllNodules()
        self._missedMaligNoduleCount = 0
        for key, val in self._missedMaligDict.items():
            if val == 1:
                self._missedMaligNoduleCount = self._missedMaligNoduleCount + 1
        return self._missedMaligNoduleCount

    def addMatch(self, index, match):
        #self.parseAllNodules()
        self._MatchPairs[index].append(match)

    def getTypeFromNodule(self, index):  # return [maligFlag, maligScore]
        #self.parseAllNodules()
        return self._noduleTypeDict[index]