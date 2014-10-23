#!/usr/bin/python

from sets import Set
import os.path
import xml.etree.ElementTree as ET
import spec_parser as sp
import settings as S

class ExtractionGen(object):
    """
    extraction.xml parser and makeExtraction.pl generator
    """
    
    def __init__(self, specFile, extractionFile):
        """
        Arguments:
        - `specFile`: specification.xls
        - `extractionFile`: extraction.xml
        """
        self._extractionFile = extractionFile
        self._specFile = specFile
        self.root = ET.parse(extractionFile)
        self.specParser = sp.SpecificationParser(specFile)
        

    def generateMakeExtractionPl(self, spcid):
        """
        Generate makeExtractionXML.pl script

        HDD , PR -> Need "sourceParamTable" property. Whereas HSA not need

        Arguments:
        - `self`:
        - `spcid`:
        """
        spcItem = self.specParser.getSpcid(spcid)
        unit = spcItem["UNIT"]
        spcidType = spcItem["SPCID_TYPE"]
        data = spcItem["DATA"]
        
        spcSimilarItem = self.findSimilar([spcid])[0]
        if not spcSimilarItem:
            return "********** WARNNING **********\n"\
                "Not similar spcid found for " + spcid + "\n"

        try:
            (fetcher, extractor) = self.getFetcherExtractor(spcSimilarItem["SPCID"])
        except Exception, e:
            return "********** WARNNING **********\n"\
                "Not fetcher & extractor found in extraction.xml for "\
                + spcid + ", similar spcid is " + spcSimilarItem["SPCID"]

        # sourceTable & sourceParamTable
        sourceParamTable = None
        if spcSimilarItem["PROCESS_ID"] == spcItem["PROCESS_ID"]:
            # get source table & source parameter table
            (sourceTable, sourceParamTable) = self.getSourceTableParamTable(spcSimilarItem["SPCID"])
        else:
            # generate
            sourceTable = self.genSourceTable(spcItem)
            if spcidType == "PR" and ("parameter" in data or "parametric" in data):
                sourceParamTable = unit.lower() + "_" + spcItem["PROCESS_ID"] + ("_head" if "head" in data else "_unit")
                
        
        properties = ', '.join( self.getProperties(spcItem) )
        
        if sourceParamTable:
            properties = ("sourceParamTable => '" + sourceParamTable) + "', " + properties

        site = "[ 'FUJ', " + (", ".join(map(lambda x: "'" + x + "'" , spcItem["SITE"]))) + "]"
        tpl = ''
        if spcItem["CHART_TYPE"] == 'Combined-Error-Ratio':
            tpl += "**** WARNNING *****====> {0} is Combined. please manually correct it.\n".format(spcid)
        if self.isByAsmDate(spcItem):
            tpl += "**** WARNNING *****====> {0} is ByAsmDate. please manually correct it.(remove excludeInlineRetest from properties)\n".format(spcid)
        
        tpl += "&write( { spcIdBase => '" + spcid[:-4] + "', \n" \
              "	  freq => [ '" + spcItem["FREQUENCY"] + "' ],\n" \
              "	  source => [ 'spcdcs' ],\n" \
              "	  cutoff => '" + spcItem["SAMPLE_SIZE"] + "', \n" \
              "	  carryOver => '" + str(spcItem["CARRY_OVER"]).lower() + "', \n" \
              "	  modelSet => '" + spcid + "', \n" \
              "	  parameterSet => '" + spcid + "', \n" \
              "	  extractor => '" + extractor + "',\n" \
              "	  fetcher => '" + fetcher + "',\n" \
              "	  properties => { sourceTable => \"" + sourceTable + "\", " + properties + " },\n" \
              "	  site =>" + site + "\n" \
              "});\n "
        
        

        return tpl

    
    def generateMakeExtractionPls(self, spcids):
        """
        Generate makeExtractionXML.pl script
        
        Arguments:
        - `self`:
        - `spcids`:
        """
        return map(self.generateMakeExtractionPl, spcids)


    
    def findSimilar(self, spcids):
        """
        Find the spcids similar with the given spcid.

        Arguments:
        - `self`:
        - `spcids`:
        
        Return:
        For each spcid in spcids will return a list
        """
        srcItems = filter(lambda item: item["SPCID"] not in spcids, self.specParser.items)
        # destItems = filter(lambda item: item["SPCID"] in spcids, self.specParser.items)
        destItems = self.specParser.getSpcids(spcids)

        def _findSimilarOne(descItem):

            def _chartTypeEquals(item):
                equalsChartTypes = ['Defective', 'Total-Defective']
                if item["CHART_TYPE"] == descItem["CHART_TYPE"]:
                    return True
                elif item["CHART_TYPE"] in equalsChartTypes and descItem["CHART_TYPE"] in equalsChartTypes:
                    return True
                else:
                    return False
            
            ret1 = filter(lambda item: _chartTypeEquals(item)
                          and item["PLOT_UNIT"] == descItem["PLOT_UNIT"]
                          and (item["PROCESS_NAME"] == descItem["PROCESS_NAME"]
                               or item["PROCESS_ID"] == descItem["PROCESS_ID"]), srcItems)
            if len(ret1) > 0:
                ret2 = filter(lambda item: item["PROCESS_ID"] == descItem["PROCESS_ID"], ret1)
                if len(ret2) > 0:
                    ret2_check = filter(self._checkSpcidExistInExtractionXML, ret2)
                    if len(ret2_check) > 0:
                        return ret2_check[0]
                    
                # ret2 not in extraction.xml, so, check ret1
                ret1_check = filter(self._checkSpcidExistInExtractionXML, ret1)
                if len(ret1_check) > 0:
                    return ret1_check[0]
            else:
                return None

        return map(_findSimilarOne, destItems)

    
    def _checkSpcidExistInExtractionXML(self, spcItem):
        """
        Check if spcItem exist in extraction.xml

        Arguments:
        - `self`:
        - `spcItem`:
        """
        if not spcItem:
            return False

        return self.checkSpcidExistInExtractionXML(spcItem["SPCID"])
        

    def checkSpcidExistInExtractionXML(self, spcid):
        """
        Check if spcid exist in extraction.xml

        Arguments:
        - `self`:
        - `spcid`:

        Return:
        bool
        """
        if not spcid:
            return False
        
        return self.root.find("./extraction[@spcId='{0}']".format(spcid)) is not None


    def getSourceTableParamTable(self, spcid):
        """
        Get sourceTable & sourceParamTable from extraction.xml

        Arguments:
        - `self`:
        - `spcid`:
        """
        node = self.root.find("./extraction[@spcId='{0}']".format(spcid))
        if node is not None:
            sourceTable = node.find("property[@key='sourceTable']").get('value')
            sourceParamTable = None
            sourceParamNode = node.find("property[@key='sourceParamTable']")
            if sourceParamNode is not None:
                sourceParamTable = sourceParamNode.get('value')
            return (sourceTable, sourceParamTable)
        return None
        

    def getFetcherExtractor(self, spcid):
        """
        Get fetcher and extractor

        Arguments:
        - `self`:
        - `spcid`:
        """
        node = self.root.find("./extraction[@spcId='{0}']".format(spcid))
        if node is not None:
            extractor = node.find('extractor').get('class')
            fetcher = node.find('fetcher').get('class')
            return (fetcher, extractor)
        return None

    
    def getFetcherExtractors(self, spcids):
        """
        Get fetcher and extractor

        Arguments:
        - `self`:
        - `spcids`:
        """
        return map(self.getFetcherExtractor, spcids)

    def genSourceTable(self, spcItem):
        """
        Generate source table

        Arguments:
        - `self`:
        - `spcItem`:
        """
        fieldsInHead = ['alignment','gram load']
        propNeedRwk = ['Rework', 'Rework_Only', 'Prime', 'First_Cycle_Only']
        unit = spcItem["UNIT"].lower()
        processId = spcItem["PROCESS_ID"]
        data = spcItem["DATA"]
        properties = spcItem["PROPERTIES"]
        procTable = unit + '_' + processId + '_proc'
        rwkTable = unit + '_' + processId + '_rwkcycle'
        headTable = unit + '_' + processId + '_head'
        sourceTable = 'common.{0} p'.format(procTable)
        if any(map(lambda field: field in propNeedRwk)):
            sourceTable += (' left join common.{0} c on p.hsasn=c.hsasn and p.enddate=c.enddate'.format(rwkTable))
        if any(map(lambda field: field in data, fieldsInHead)):
            sourceTable += (' left join common.{0} h on p.hsasn=h.hsasn and p.enddate=h.enddate'.format(headTable))

        return sourceTable


    def getProperties(self, spcItem):
        """
        Get properties

        Arguments:
        - `self`:
        - `spcItem`:
        """
        unit = spcItem["UNIT"]
        properties = spcItem["PROPERTIES"]
        values = Set([])

        # if Rework_Only exist, remove Rework. Because the condition rework_only involve rework.
        if "Rework_Only" in properties and "Rework" in properties:
            del properties["Rework"]

        for k, v in properties.iteritems():
            s = None
            if k == "Rework" and v:
                s = "typeOfHSA => 'NotNew'" if unit == 'HSA' else "typeOfHDE => 'NotPrime'"
                
            elif k == "Prime" and v:
                s = ["typeOfHSA => 'New'" if unit == 'HSA' else "typeOfHDE => 'Prime'", "firstCycleOnly => 'true'"]
                
            elif k == "Latest_Data" and v:
                s = "latestOnly => 'true'"
                
            elif k == "Rework_Only" and v:
                s = "notFirstCycleOnly => 'true'"
                
            elif k == "First_Cycle_Only":
                s = "firstCycleOnly => 'true'" if v else "firstCycleOnly => 'false'"
                
            elif k == "Pass_Only":
                s = "passOnly => 'true'" if v else "passOnly => 'false'"
                
            elif k == "Exclude_Trial":
                s = "excludeTrial => 'true'" if v else "excludeTrial => 'false'"
                
            elif k == "Filter_Fail" and v:
                s = "filterFail => 'true'"
                
            elif k == "Exclude_Inline_Retest":
                s = "excludeInlineRetest => 'true'" if v else "excludeInlineRetest => 'false'"
                
            elif k == "Exclude_Ship_Return":
                s = "excludeShipReturn => 'true'" if v else "excludeShipReturn => 'false'"
                
            else:
                pass
            
            if s:
                if type(s) == list:
                    for i in s:
                        values.add(i)
                else:
                    values.add(s)
        
        return values

    def isByAsmDate(self, spcItem):
        """
        Is By Asm Date
        Arguments:
        - `self`:
        - `spcItem`:
        """
        return "Asm_Date" in spcItem["PROPERTIES"]

    def getMakeInitTableSQL(self, spcids):
        """
        Get makeInitTableSQL.pl

        Arguments:
        - `self`:
        - `spcids`:
        """
        mapping = {'ByLine': 'ASMLINE:CHAR(6)',
                   'ByHead': 'UPDOWN:CHAR(1)',
                   'ByHeadNo': 'HEADNO:CHAR(6)', 
                   'ByCell': 'CELLID:CHAR(12)',
                   'ByTester': 'TESTERID:CHAR(12)',
                   'ByHeadGrade': 'HEADGRADE:CHAR(1)',
                   'BySswType': 'SSWTYPE:CHAR(6)'}
        spcItems = self.specParser.getSpcids(spcids)
        def _translateFun(spcItem):
            spcId = spcItem["SPCID"]
            plotUnit = spcItem["PLOT_UNIT"]
            fields = ",".join( map(lambda u: '"'+mapping[u]+'"', plotUnit) )
            return '&makeTable("{0}",[ {1} ],["{2}"]);'.format(spcId[:-5], fields, spcId[-3:])

        return map(_translateFun, spcItems)
    
    def getMakeInitViewSQL(self, spcids):
        """
        Get makeInitViewSQL.pl

        Arguments:
        - `self`:
        - `spcids`:
        """
        plotUnitMapping = {'ByLine': 'ASMLINE',
                           'ByHead': 'UPDOWN',
                           'ByHeadNo': 'HEADNO', 
                           'ByCell': 'CELLID',
                           'ByTester': 'TESTERID',
                           'ByHeadGrade': 'HEADGRADE',
                           'BySswType': 'SSWTYPE'}

        chartTypeMapping = {'Mean-Sigma': '"AVG", "STD"', 
                            'Yield': '"RATIO"', 
                            'Combined-Error-Ratio': '"RATIO"',
                            'Error-Ratio': '"RATIO"', 
                            'Defective': '"(100.0 - RATIO) as RATIO"', 
                            'Total-Defective': '"(100.0 - RATIO) as RATIO"' }

        spcItems = self.specParser.getSpcids(spcids)
        def _translateFun(spcItem):
            spcId = spcItem["SPCID"]
            plotUnit = spcItem["PLOT_UNIT"]
            fields = ",".join( map(lambda u: '"'+plotUnitMapping[u]+'"', plotUnit) )
            calcField = chartTypeMapping[spcItem["CHART_TYPE"]]
            return '&makeView("{0}",[ {1} ], [ {2} ], ["{3}"]);'.format(spcId[:-5], fields, calcField, spcId[-3:])
        
        return map(_translateFun, spcItems)

    def getExtractionSpcXh(self, spcids):
        """
        Get extraction-spc-xxh.sh

        Arguments:
        - `self`:
        - `spcids`:
        """
        def _extractionStr(spcid):
            return "$APPHOME/bin/remover.sh $site $APPHOME/etc {0} $retention\n"\
                "$APPHOME/bin/invoker.sh $site $APPHOME/etc {0}".format(spcid)
        
        hourSpcids = {"01H": [], "04H": [], "08H": [], "24H": []}
        for spcid in spcids:
            hourSpcids[spcid[-3:]].append(spcid)
        
        ret = {}
        for hour, spcids in hourSpcids.iteritems():
            if len(spcids) > 0 :
                ret[hour] = map(_extractionStr, spcids)
                
        return ret

    def getSpcidsActualNotExist(self, spcids):
        """
        Get those spcids whose related table doesn't exist.
        Arguments:
        - `self`:
        - `spcids`:
        Return: 
        - Tuple: (NotExistSpcidList, ExistSpcidList)
        """
        srcItems = filter(lambda item: item["SPCID"] not in spcids, self.specParser.items)
        tableExists = []
        tableNotExist = []

        def getProfile(spcid):
            return spcid[:11] + spcid[12:]

        def ifExist(spcid):
            ret = filter(lambda item: getProfile(item["SPCID"]) == getProfile(spcid), srcItems)
            return len(ret) > 0

        for spcid in spcids:
            if ifExist(spcid):
                tableExists.append(spcid)
            else:
                tableNotExist.append(spcid)

        return (tableNotExist, tableExists)


    
if __name__ == '__main__':
    eg = ExtractionGen(S.SPECIFICATION_XLS, S.EXTRACTION_FILE)
    # print eg.getFetcherExtractors(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    # print eg.generateMakeExtractionPl('CC1700_PR02A_01H')
    # print eg.generateMakeExtractionPls(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    # print eg.getMakeInitTableSQL(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    # print eg.getMakeInitViewSQL(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    print eg.getExtractionSpcXh(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    
