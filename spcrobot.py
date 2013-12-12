#!/usr/bin/python

# ####################
# The main entrance of spcrobot
# ####################

import spec_parser as sp
import extraction_gen as eg
import settings as S

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
        self.outputFile = S.MAIN_OUT
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

    def getMakeLoaderInis(self, spcids):
        """
        Get makeLoaderIni.pl
        Arguments:
        - `self`:
        - `spcids`:
        """
        def _makeLoaderIniOneRow(spcid):
            return "&writeINI( { loaderBaseName => '%s', types => [ 'NONE' ], freq => [ '%s' ]});" % (spcid[:11], spcid[-3:])

        return map(_makeLoaderIniOneRow, spcids)
        
    def out(self):
        """
        Write output files
        """
        with open(self.outputFile, 'w') as f:
            self._out_spcids(f)
            self._out_product_data(f)
            self._out_extrafields(f)
            self._out_site(f)
            self._out_makeInitTable(f)
            self._out_makeInitView(f)
            self._out_makeExtractionPl(f)
            self._out_extraction_xh(f)
            self._out_makeLoaderIni(f)
            self._out_runHDDLoader(f)
            

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
        f.write('makeExtractionXML.pl\n')
        f.write(self.SEPERATOR)
        extractionPls = self.getMakeExtractionPls()
        for pl in extractionPls:
            f.write(pl + "\n")
        f.write("\n\n")


    def _out_product_data(self, f):
        """
        Write out the value of column product, data
        Arguments:
        - `self`:
        - `f`:
        """
        f.write('Product and Data\n')
        f.write(self.SEPERATOR)
        f.write('   SPCID \t    PRODUCT \t     DATA \t \n')
        f.write('-----------\t ----------- \t ---------\n')
        spcItems = self.specParser.getSpcids(self.spcids)
        for spcItem in spcItems:
            f.write(spcItem["SPCID"] + "\t"
                    + spcItem["PRODUCT"] + "\t"
                    + spcItem["DATA"] + "\n")
        f.write("\n\n")

    def _out_site(self, f):
        """
        Write out the site of spcid.

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('Site\n')
        f.write(self.SEPERATOR)
        spcItems = self.specParser.getSpcids(self.spcids)
        for spcItem in spcItems:
            f.write(spcItem["SPCID"] + "\t" + ','.join(spcItem["SITE"]) + "\n")
        f.write("\n\n")

    def _out_makeInitTable(self, f):
        """
        Write out makeInitTableSQL.pl

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('makeInitTableSQL.pl\n')
        f.write(self.SEPERATOR)
        f.write( "\n".join(self.extraGen.getMakeInitTableSQL(self.spcids)) )
        f.write("\n\n")
        
    def _out_makeInitView(self, f):
        """
        Write out makeInitViewSQL.pl

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('makeInitViewSQL.pl\n')
        f.write(self.SEPERATOR)
        f.write("\n".join(self.extraGen.getMakeInitViewSQL(self.spcids)))
        f.write("\n\n")

    def _out_extraction_xh(self, f):
        """
        Write out extraction-spc-xxh.sh

        Arguments:
        - `self`:
        - `f`:
        """
        f.write('extraction-spc-xxh.sh\n')
        f.write(self.SEPERATOR)
        hourStrDict = self.extraGen.getExtractionSpcXh(self.spcids)
        for hour, rets in hourStrDict.iteritems():
            f.write(hour+"\n")
            f.write("-------------\n")
            f.write("\n\n".join(rets))
            f.write("\n\n")
        f.write("\n\n")

    def _out_makeLoaderIni(self, f):
        """
        Arguments:
        - `self`:
        - `f`:
        """
        f.write('makeLoaderIni.pl\n')
        f.write(self.SEPERATOR)
        f.write("\n".join(self.getMakeLoaderInis(self.spcids)))
        f.write("\n\n")

    def _out_runHDDLoader(self, f):
        """
        """
        spcItems = self.specParser.getSpcids(self.spcids)
        ret = {"GSP":[], "SGP":[], "PRB":[]}
        for spcItem in spcItems:
            spcid = spcItem["SPCID"]
            hour = spcid[-3:]
            profileId = spcid[:11] + '_' + hour
            sites = spcItem["SITE"]
            for site in sites:
                ret[site].append((hour, profileId))

        f.write('RunHDDLoader_xxx.bat\n')
        f.write(self.SEPERATOR)
        
        for site, tupList in ret.iteritems():
            if len(tupList) > 0:
                f.write(site+"\n")
                f.write("--------------\n")
                
                outputMap = {}
                tupList.sort()
                for tup in tupList:
                    if tup[0] not in outputMap:
                        outputMap[tup[0]] = []
                    else:
                        outputMap[tup[0]].append(tup[1])

                # output
                for hour, spcids in outputMap.iteritems():
                    f.write(hour+"\n")
                    f.write("-------\n")
                    f.write( "\n".join(map(lambda spcid: "%javabindir%java mpc.webspc2.dataextract.DataExtract e:\spclds\etc\{0}.ini".format(spcid), spcids)) )
                    f.write("\n")

            f.write("\n")
        # end for

        f.write("\n\n")

        
        
def main():
    """
    main
    """
    sr = SpcRobot(S.SPCIDS_FILE, S.SPECIFICATION_XLS, S.EXTRACTION_FILE)
    # print sr.spcids
    # print sr.getExtraFields()
    sr.out()

    
if __name__ == '__main__':
    main()
    
