#!/usr/bin/python

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
        spcSimilarItem = self.specParser.findSimilar([spcid])[0]
        (fetcher, extractor) = self.getFetcherExtractor(spcSimilarItem["SPCID"])
        sourceTable = self.genSourceTable(spcItem)
        properties = ', '.join( self.getProperties(spcItem) )
        if unit == "HDD" and spcidType == "PR":
            sourceParamTable = "hdd_" + spcItem["PROCESS_ID"] + "_head"
            properties = ("sourceParamTable => '" + sourceParamTable) + "', " + properties

        site = "[" + (", ".join(spcItem["SITE"])) + "]"
        print site
        tpl = "&write( { spcIdBase => '" + spcid[:-4] + "', "\
              "	  freq => [ '" + spcItem["FREQUENCY"] + "' ],"\
              "	  source => [ 'spcdcs' ],"\
              "	  cutoff => '" + spcItem["SAMPLE_SIZE"] + "', "\
              "	  carryOver => '" + spcItem["CARRY_OVER"] + "', "\
              "	  modelSet => '" + spcid + "', "\
              "	  parameterSet => '" + spcid + "', "\
              "	  extractor => '" + extractor + "',"\
              "	  fetcher => '" + fetcher + "',"\
              "	  properties => { sourceTable => '" + sourceTable + "', " + properties + " },"\
              "	  site =>" + site + ""\
              "      });"

        return tpl

    
    def generateMakeExtractionPls(self, spcids):
        """
        Generate makeExtractionXML.pl script
        
        Arguments:
        - `self`:
        - `spcids`:
        """
        pass


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
        unit = spcItem["UNIT"]
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
            "Prime": "typeOfHSA => 'New'" if unit == 'HSA' else "typeOfHDE => 'Prime', firstCycleOnly => 'true'",
            "New_Only": "" if unit == 'HDD' and "Prime" in properties else "firstCycleOnly => 'true'",
            "Latest_Data": "latestOnly => 'true'",
            "Rework_Only": "notFirstCycleOnly => 'true'",
            "Pass_And_Fail": "passOnly => 'false'",
            "Without_HSAL": "excludeTrial => 'true'",
            "Cycle_GT_1": "passOnly => 'false"
        }
        values = []
        for p in properties:
            values.append(mapping[p])
        return values

    

if __name__ == '__main__':
    specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
                       'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    extractionFile = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/config_code/etc/extraction.xml'
    eg = ExtractionGen(specificationXls, extractionFile)
    # print eg.getFetcherExtractors(['CC1700_PR02A_01H','CC1985_PR01A_01H'])
    print eg.generateMakeExtractionPl('CC1700_PR02A_01H')

