#!/usr/bin/python

from sets import Set
import xml.etree.ElementTree as ET
import spec_parser as sp

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
            
        sourceTable = self.genSourceTable(spcItem)
        properties = ', '.join( self.getProperties(spcItem) )
        
        if spcidType == "PR" and ("parameter" in data or "parametric" in data):
            sourceParamTable = unit.lower() + "_" + spcItem["PROCESS_ID"] + "_head"
            properties = ("sourceParamTable => '" + sourceParamTable) + "', " + properties

        site = "[ 'FUJ', " + (", ".join(map(lambda x: "'" + x + "'" , spcItem["SITE"]))) + "]"
        tpl = ''
        if spcItem["CHART_TYPE"] == 'Combined-Error-Ratio':
            tpl += "**** WARNNING *****====> {0} is Combined. please manually correct it.".format(spcid)
        tpl += "&write( { spcIdBase => '" + spcid[:-4] + "', \n" \
              "	  freq => [ '" + spcItem["FREQUENCY"] + "' ],\n" \
              "	  source => [ 'spcdcs' ],\n" \
              "	  cutoff => '" + spcItem["SAMPLE_SIZE"] + "', \n" \
              "	  carryOver => '" + str(spcItem["CARRY_OVER"]).lower() + "', \n" \
              "	  modelSet => '" + spcid + "', \n" \
              "	  parameterSet => '" + spcid + "', \n" \
              "	  extractor => '" + extractor + "',\n" \
              "	  fetcher => '" + fetcher + "',\n" \
              "	  properties => { sourceTable => '" + sourceTable + "', " + properties + " },\n" \
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
        destItems = filter(lambda item: item["SPCID"] in spcids, self.specParser.items)

        def _findSimilarOne(descItem):
            ret1 = filter(lambda item: item["CHART_TYPE"] == descItem["CHART_TYPE"]
                          and item["PLOT_UNIT"] == descItem["PLOT_UNIT"]
                          and item["PROCESS_NAME"] == descItem["PROCESS_NAME"], srcItems)
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
        unit = spcItem["UNIT"].lower()
        processId = spcItem["PROCESS_ID"]
        data = spcItem["DATA"]
        properties = spcItem["PROPERTIES"]
        procTable = unit + '_' + processId + '_proc'
        rwkTable = unit + '_' + processId + '_rwkcycle'
        headTable = unit + '_' + processId + '_head'
        sourceTable = 'common.{0} p'.format(procTable)
        if 'Rework' in properties or 'Rework_Only' in properties:
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
        mapping = {
            "Rework": "typeOfHSA => 'NotNew'" if unit == 'HSA' else "typeOfHDE => 'NotPrime'",
            "Prime": "typeOfHSA => 'New'" if unit == 'HSA' else ["typeOfHDE => 'Prime'", "firstCycleOnly => 'true'"],
            "New_Only": "firstCycleOnly => 'true'",
            "Latest_Data": "latestOnly => 'true'",
            "Rework_Only": "notFirstCycleOnly => 'true'",
            "Pass_And_Fail": "passOnly => 'false'",
            "Test_Pass": "passOnly => 'true'",
            "Without_HSAL": "excludeTrial => 'true'",
            "Cycle_GT_1": "passOnly => 'false'"
        }
        values = Set([])
        for p in properties:
            values.add(mapping[p])
        return values


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
    
    

if __name__ == '__main__':
    specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
                       'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    extractionFile = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/config_code/etc/extraction.xml'
    # specificationXls = 'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    # extractionFile = 'extraction.xml'
    eg = ExtractionGen(specificationXls, extractionFile)
    # print eg.getFetcherExtractors(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    # print eg.generateMakeExtractionPl('CC1700_PR02A_01H')
    # print eg.generateMakeExtractionPls(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    # print eg.getMakeInitTableSQL(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    print eg.getMakeInitViewSQL(['CC1700_PR02A_01H','CC1985_PR01A_01H'])

