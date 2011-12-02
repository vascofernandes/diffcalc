'''Angles in radians'''
from copy import copy
from diffcalc.utils import Position as P
from math import pi

SMALL = 1e-10

class Transform(object):
    
    def transform(self, pos):
        raise RuntimeError('Not implemented')

### Transforms, currently for definition and testing the theory only

class TransformC(Transform):
    '''Flip omega, invert chi and flip phi
    '''
    def transform(self, pos):
        pos = pos.clone()
        pos.omega -= 180
        pos.chi *= -1
        pos.phi -= 180
        return pos


class TransformB(Transform):
    '''Flip chi, and invert and flip omega
    '''
    def transform(self, pos):
        pos = pos.clone()
        pos.chi -= 180
        pos.omega = 180 - pos.omega
        return pos


class TransformA(Transform):
    '''Invert scattering plane: invert delta and omega and flip chi'''
    def transform(self, pos):
        pos = pos.clone()
        pos.delta *= -1
        pos.omega *= -1
        pos.chi -= 180
        return pos

class TransformCInRadians(Transform):
    '''Flip omega, invert chi and flip phi. Using radians and keeping  -pi<omega<=pi and 0<=phi<=360
    '''
    def transform(self, pos):
        pos = pos.clone()
        if pos.omega > 0:
            pos.omega -= pi
        else:
            pos.omega += pi
        pos.chi *= -1
        pos.phi += pi
        return pos


###

transformsFromSector = {
                    0 : (),
                    1 : ('c',),
                    2 : ('a',),
                    3 : ('a', 'c'),
                    4 : ('b', 'c'),
                    5 : ('b',),
                    6 : ('a', 'b', 'c'),
                    7 : ('a', 'b')
                    }

sectorFromTransforms = {}
for k, v in transformsFromSector.iteritems():
    sectorFromTransforms[v] = k
    

class SectorSelector(object):
    '''All returned angles are between -180. and 180. -180.<=angle<180.
    '''
### basic sector selection

    def __init__(self, limitCheckerFunction):
        self.transforms = []
        self.autotransforms = []
        self.autosectors = []
        self.limitCheckerFunction = limitCheckerFunction
        self.sector = None
        self.setSector(0)
        
    def setSector(self, sector):
        if not 0 <= sector <= 7:
            raise ValueError('%i must between 0 and 7.' % sector)
        self.sector = sector
        self.transforms = list(transformsFromSector[sector])

    def setTransforms(self, transformList):
        transformList = list(transformList)
        transformList.sort()
        self.sector = sectorFromTransforms[tuple(transformList)]
        self.transforms = transformList

    def addTransorm(self, transformName):
        if transformName not in ('a', 'b', 'c'):
            raise ValueError('%s is not a recognised transform. Try a, b or c' % transformName)
        if transformName in self.transforms:
            print "WARNING, transform %s is already selected"
        else:
            self.setTransforms(self.transforms + [transformName])

    def removeTransorm(self, transformName):
        if transformName not in ('a', 'b', 'c'):
            raise ValueError('%s is not a recognised transform. Try a, b or c' % transformName)
        if transformName in self.transforms:
            new = copy(self.transforms)
            new.remove(transformName)
            self.setTransforms(new)
        else:
            print "WARNING, transform %s was not selected" % transformName
    
    def addAutoTransorm(self, transformOrSector):
        '''If input is a string (letter), tags one of the transofrms as being a candidate for auto
        application. If a number, tags a sector as being a candidate for auto application, and
        removes similar tags for any transforms (as the two are incompatable).'''
        if type(transformOrSector) == str:
            transform = transformOrSector
            if transform not in ('a', 'b', 'c'):
                raise ValueError('%s is not a recognised transform. Try a, b or c' % transform)
            if transform not in self.autotransforms:
                self.autosectors = []
                self.autotransforms.append(transform)
            else:
                print "WARNING: %s is already set to auto apply" % transform
        elif type(transformOrSector) == int:
            sector = transformOrSector
            if not 0 <= sector <= 7:
                raise ValueError('%i must between 0 and 7.' % sector)
            if sector not in self.autosectors:
                self.autotransforms = []
                self.autosectors.append(sector)
            else:
                print "WARNING: %i is already set to auto apply" % sector
        else:
            raise ValueError, "Input must be 'a', 'b' or 'c', or 1,2,3,4,5,6 or 7."

    def removeAutoTransform(self, transformOrSector):
        if type(transformOrSector) == str:
            transform = transformOrSector
            if transform not in ('a', 'b', 'c'):
                raise ValueError('%s is not a recognised transform. Try a, b or c' % transform)
            if transform in self.autotransforms:
                self.autotransforms.remove(transform)
            else:
                print "WARNING: %s is not set to auto apply" % transform
        elif type(transformOrSector) == int:
            sector = transformOrSector
            if not 0 <= sector <= 7:
                raise ValueError('%i must between 0 and 7.' % sector)
            if sector in self.autosectors:
                self.autosectors.remove(sector)
            else:
                print "WARNING: %s is not set to auto apply" % sector
        else:
            raise ValueError, "Input must be 'a', 'b' or 'c', or 1,2,3,4,5,6 or 7."
    
    def setAutoSectors(self, sectorList):
        for sector in sectorList:
            if not 0 <= sector <= 7:
                raise ValueError('%i must between 0 and 7.' % sector)
        self.autosectors = list(sectorList)

    def transformPosition(self, pos):
        pos = self.transformNWithoutCut(self.sector, pos)
        cutpos = self.cutPosition(pos) # -180<=cutpos<180, NOT the externally applied cuts
        if len(self.autosectors) > 0:
            if self.isPositionWithinLimits(cutpos):
                return cutpos
            else:
                return self.autoTransformPositionBySector(cutpos)
        if len(self.autotransforms) > 0:
            if self.isPositionWithinLimits(cutpos):
                return cutpos
            else:
                return self.autoTransformPositionByTransforms(pos)
        #else
        return cutpos

    def transformNWithoutCut(self, n, pos):
#        if not self.inSectorZero(delta, omega, chi, phi):
#            print "WARNING: SectorSelector, input position delta=%s, omega=%s, chi=%s, phi=%s was not in default sector" % (delta, omega, chi, phi)
        if n == 0:
            return P(pos.alpha, pos.delta, pos.gamma, pos.omega, pos.chi, pos.phi)
        if n == 1:
            return P(pos.alpha, pos.delta, pos.gamma, pos.omega - 180., -pos.chi, pos.phi - 180.)
        if n == 2:
            return P(pos.alpha, -pos.delta, pos.gamma, -pos.omega, pos.chi - 180., pos.phi)
        if n == 3:
            return P(pos.alpha, -pos.delta, pos.gamma, 180. - pos.omega, 180. - pos.chi, pos.phi - 180.)
        if n == 4:
            return P(pos.alpha, pos.delta, pos.gamma, -pos.omega, 180. - pos.chi, pos.phi - 180.)
        if n == 5:
            return P(pos.alpha, pos.delta, pos.gamma, 180. - pos.omega, pos.chi - 180., pos.phi)
        if n == 6:
            return P(pos.alpha, -pos.delta, pos.gamma, pos.omega, -pos.chi, pos.phi - 180.)
        if n == 7:
            return P(pos.alpha, -pos.delta, pos.gamma, pos.omega - 180., pos.chi, pos.phi)
        else:
            raise Exception("sector must be between 0 and 7")

### autosector
    
    def hasAutoSectorsOrTransformsToApply(self):
        return len(self.autosectors) > 0 or len(self.autotransforms) > 0

    def autoTransformPositionBySector(self, pos):
        okaysectors = []
        okaypositions = []
        for sector in self.autosectors:
            newpos = self.transformNWithoutCut(sector, pos)
            if self.isPositionWithinLimits(newpos):
                okaysectors.append(sector)
                okaypositions.append(newpos)
        if len(okaysectors) == 0:
            raise Exception("Autosector could not find a sector (from %s) to move %s into limits." % (self.autosectors, str(pos)))
        if len(okaysectors) > 1:
            print "WARNING: Autosector found multiple sectors that would move %s to move into limits: %s" % (str(pos), okaysectors) 
        
        print "INFO: Autosector changed sector from %i to %i" % (self.sector, okaysectors[0])
        self.sector = okaysectors[0]
        return okaypositions[0]
        
    def autoTransformPositionByTransforms(self, pos):
        possibleTransforms = self.createListOfPossibleTransforms()
        okaytransforms = []
        okaypositions = []
        for transforms in possibleTransforms:
            sector = sectorFromTransforms[tuple(transforms)]
            newpos = self.cutPosition(self.transformNWithoutCut(sector, pos))
            if self.isPositionWithinLimits(newpos):
                okaytransforms.append(transforms)
                okaypositions.append(newpos)
        if len(okaytransforms) == 0:
            raise Exception("Autosector could not find a sector (from %s) to move %s into limits." % (`self.autosectors`, `pos`))
        if len(okaytransforms) > 1:
            print "WARNING: Autosector found multiple sectors that would move %s to move into limits: %s" % (`pos`, `okaytransforms`) 
        
        print "INFO: Autosector changed selected transforms from %s to %s" % (`self.transforms`, `okaytransforms[0]`)
        self.setTransforms(okaytransforms[0])
        return okaypositions[0]

    def createListOfPossibleTransforms(self):    
        def vary(possibleTransforms, name):
            result = []
            for transforms in possibleTransforms:
                # add the original.
                result.append(transforms) 
                # add a modified one
                toadd = list(copy(transforms))
                if name in transforms:
                    toadd.remove(name)
                else:
                    toadd.append(name)
                toadd.sort()
                result.append(toadd)
            return result
        # start with the currently selected list of transforms
        if len(self.transforms) == 0:
            possibleTransforms = [()]
        else:
            possibleTransforms = copy(self.transforms)
        
        for name in self.autotransforms:
            possibleTransforms = vary(possibleTransforms, name)
            
        return possibleTransforms
    
    def isPositionWithinLimits(self, pos):
        '''where pos os a poistion object in degrees'''
        return self.limitCheckerFunction(pos)

    def __repr__(self):
        def createPrefix(transform):
            if transform in self.transforms:
                s = '*on* '
            else:
                s = 'off  '
            if len(self.autotransforms) > 0:
                if transform in self.autotransforms:
                    s += '*auto*'
                else:
                    s += '      '
            return s
        s = 'Transforms/sector:\n'
        s += '  %s (a transform) Invert scattering plane: invert delta and omega and flip chi\n' % createPrefix('a')
        s += '  %s (b transform) Flip chi, and invert and flip omega\n' % createPrefix('b')
        s += '  %s (c transform) Flip omega, invert chi and flip phi\n' % createPrefix('c')
        s += '  Current sector: %i (Spec fourc equivalent)\n' % self.sector
        if len(self.autosectors) > 0:
            s += '  Auto sectors: %s\n' % self.autosectors
        return s

#    def inSectorZero(self, delta, omega, chi, phi):
#        return (0 <= delta < 180.) & (-180./2 <= omega < 180./2) & (0 <= chi < 180.)

    def cutPosition(self, position):
        '''Cuts angles at -180.; moves each argument between -180. and 180.
        '''
        def cut(a):
            if a is None:
                return None
            else:
                if a < (-180. - SMALL):
                    return a + 360.
                if a > (180. + SMALL):
                    return a - 360.
            return a
        return P(cut(position.alpha), cut(position.delta), cut(position.gamma), cut(position.omega), cut(position.chi), cut(position.phi))

