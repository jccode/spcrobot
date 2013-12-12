#!/usr/bin/python

import os.path
import spec_parser as sp
import settings as S

class EvidenceGen(object):
    """
    """
    SQL_SELECT="select plotts,spcid,paramid,modelid,datacount,ratio,storets"
    SQL_ORDERBY=" order by modelid,paramid,plotts"
    
    def __init__(self, specFile, sqlretDir, spcidsFile):
        """
        
        Arguments:
        - `spcidsFile`:
        - `sqlretDir`:
        """
        self._sqlretDir = os.path.normpath(sqlretDir)
        self.specParser = sp.SpecificationParser(specFile)
        self.typesNeedShowView = ['Error-Ratio', 'Combined-Error-Ratio', 'Defective', 'Total-Defective']
        self._spcidsFile = spcidsFile
        self.spcids = [line.strip() for line in open(spcidsFile)]
        self.outputFile = S.EVIDENCE_OUT
        

    def getEvidence(self, spcid):
        """
        Arguments:
        - `self`:
        - `spcid`:
        """
        spcItem = self.specParser.getSpcid(spcid)
        chartType = spcItem["CHART_TYPE"]
        extraField = self.specParser.getExtraField(spcid)[1]
        table = spcid[:11] + spcid[12:]
        sqlForTable = self.SQL_SELECT + extraField + " from PLOT." + table + self.SQL_ORDERBY
        sqlForView = self.SQL_SELECT + extraField + " from SPC." + table + self.SQL_ORDERBY
        ret = "SPCID:\t\t {0} \nPlot Table Name:\t\t PLOT.{1} \n\n\n\n\n\n\n\n\n\n\n\n\n"\
              "Sample Records from SPCDB: \n\n\n"\
              "db2 \"{2}\"".format(spcid, table, sqlForTable)
        ret += ("\n" + self.getSQLRet(spcid, 'table'))
        
        if chartType in self.typesNeedShowView:
            ret += "\n\n\ndb2 \"%s\"" % sqlForView
            ret += ('\n' + self.getSQLRet(spcid, 'view'))
        return ret


    def getEvidences(self, spcids):
        """
        """
        return map(self.getEvidence, spcids)


    def getSQLRet(self, spcid, type):
        """
        
        Arguments:
        - `self`:
        - `type`: should be 'table' or 'view'
        - `spcid`:
        """
        sqlretfile = "sqlret_{0}_{1}.txt".format(type, spcid)

        with open(self._sqlretDir + "/" + sqlretfile, 'r') as retfile:
            return retfile.read()

        
    def out(self):
        """
        """
        SEPERATOR = '=================================\n'
        with open(self.outputFile, 'w') as f:
            f.write("Evidence\n")
            f.write(SEPERATOR + "\n")
            f.write(("\n"+SEPERATOR+"\n").join(self.getEvidences(self.spcids)))
            f.write("\n\n")
            

if __name__ == '__main__':
    eviGen = EvidenceGen(S.SPECIFICATION_XLS, S.SQLRET_DIR, S.SPCIDS_FILE)
    # print eviGen.getEvidences(['ET6400_ER04A_24H'])
    eviGen.out();
        
