#!/usr/bin/python

# ####################
# The main entrance of spcrobot
# ####################

import spec_parser as sp
import extraction_gen as eg


class SpcRobot(object):
    """
    """
    SEPERATOR = '=================================\n'
    
    def __init__(self, spcidsFile, specFile, extractionXmlFile):
        """
        
        Arguments:
        - `spcidsFile`:
        - `specFile`:
        - `extractionXmlFile`: 
        """
        self._spcidsFile = spcidsFile
        self._specFile = specFile
        self._extractionXmlFile = extractionXmlFile
        self.outputFile = 'out.txt'
        self.spcids = [line.strip() for line in open(spcidsFile)]
        self.specParser = sp.SpecificationParser(specFile)
        self.extraGen = eg.ExtractionGen(specFile, extractionXmlFile)
        

    def getExtraFields(self):
        """
        Write extra fields

        Arguments:
        - `self`:
        """
        return self.specParser.getExtraFields(self.spcids)


    def getMakeExtractionPls(self):
        """
        Get makeExtractionXML.pl template

        Arguments:
        - `self`:
        """
        return self.extraGen.generateMakeExtractionPls(self.spcids)
        
        
        
    def out(self):
        """
        Write output files
        """
        with open(self.outputFile, 'w') as f:
            self._out_spcids(f)
            self._out_extrafields(f)
            self._out_makeExtractionPl(f)
            

    def _out_spcids(self, f):
        """
        Write out spcids

        Arguments:
        - `self`:
        - `f`: output file
        """
        f.write('Spcids to be processed\n')
        f.write(self.SEPERATOR)
        f.write("\n".join(self.spcids))
        f.write("\n\n")

    def _out_extrafields(self, f):
        """
        Write out extra fields

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('Extra Fields\n')
        f.write(self.SEPERATOR)
        extrafields = self.getExtraFields()
        for (spcid, extrafield) in extrafields:
            f.write(spcid + "\t" + extrafield + "\n")
        f.write("\n\n")

    def _out_makeExtractionPl(self, f):
        """
        Write out makeExtractionXML.pl

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('makeExtractionXML.pl')
        f.write(self.SEPERATOR)
        extractionPls = self.getMakeExtractionPls()
        for pl in extractionPls:
            f.write(pl + "\n")
        f.write("\n\n")
        

def main():
    """
    main
    """
    inputFile = 'spcids.txt'
    # specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
    #                    'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    # extractionFile = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/config_code/etc/extraction.xml'
    specificationXls = 'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    extractionFile = 'extraction.xml'
    
    sr = SpcRobot(inputFile, specificationXls, extractionFile)
    # print sr.spcids
    # print sr.getExtraFields()
    sr.out()

    
if __name__ == '__main__':
    main()
    
