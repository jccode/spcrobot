#!/usr/bin/python

from sets import Set
import spec_parser as sp
import ConfigParser
import ibm_db

class ModelSetGen(object):
    """
    """
    
    def __init__(self, datasource):
        """
        """
        self._datasource = datasource
        self._config = ConfigParser.ConfigParser()
        self._config.read(self._datasource)
        self._debug = False

    def getModel(self, spcItem):
        spcId = spcItem["SPCID"]
        sites = spcItem["SITE"]
        groupingKeys = spcItem["GROUPING_KEYS"]
        sql = self.getQuerySQL(spcItem)

        if self._debug:
            print sql

        rets = {}
        for site in sites:
            conn = self.getDBConnection(site)
            stmt = ibm_db.exec_immediate(conn, sql)
            mtypeTuple = ibm_db.fetch_tuple(stmt)
            mtypes = Set([])
            while mtypeTuple != False:
                mtypes.add(mtypeTuple[0])
                mtypeTuple = ibm_db.fetch_tuple(stmt)
            rets[site] = mtypes
            if self._debug:
                print site, mtypes
        
        # union all the results
        uRet = Set([])
        for ret in rets.itervalues():
            uRet = uRet.union(ret)
        
        return list(uRet)


    def getModels(self, spcItems):
        return map(lambda item: (item["SPCID"], item["GROUPING_KEYS"], self.getModel(item)), spcItems)

    
    def getDBProperies(self, site):
        prop = {}
        prop["host"] = self._config.get(site, "host")
        prop["db"] = self._config.get(site, "db")
        prop["port"] = self._config.get(site, "port")
        prop["user"] = self._config.get(site, "user")
        prop["password"] = self._config.get(site, "password")
        return prop

    def getDBConnection(self, site):
        dbprop = self.getDBProperies(site)
        connStr = "DATABASE=%s;HOSTNAME=%s;PORT=%s;PROTOCOL=TCPIP;UID=%s;PWD=%s;" \
                  % (dbprop["db"], dbprop["host"], dbprop["port"], dbprop["user"], dbprop["password"])
        return ibm_db.connect(connStr, "", "")

    def getQuerySQL(self, spcItem):
        unit = spcItem["UNIT"]
        processId = spcItem["PROCESS_ID"]
        product = spcItem["PRODUCT"]
        product = product.replace("(","").replace(")", "").strip()
        prods = product.split(",") if "," in product else product.split("/")
        wheres= map(lambda prod: "MTYPE LIKE '{0}%'".format(prod.strip()), prods)
        select = "SELECT DISTINCT MTYPE FROM COMMON.%s_%s_PROC" % (unit, processId)
        return select + " WHERE " + " OR ".join(wheres)

    

def outputModelset(dsFile, spcidsFile, specXlsFile):
    SEPERATOR = '=================================\n'
    outputFile = "modelset_out.txt"
    spcids = [line.strip() for line in open(spcidsFile)]
    specParser = sp.SpecificationParser(specXlsFile)
    spcItems = specParser.getSpcids(spcids)

    mg = ModelSetGen(dsFile)
    modelsets = mg.getModels(spcItems)
    with open(outputFile, 'w') as f:
        f.write('Modelset mtypes\n')
        f.write(SEPERATOR)
        for spcidMtype in modelsets:
            f.write(spcidMtype[0] + "   grouping-keys:" + spcidMtype[1] + "\n")
            f.write("------------\n")
            for mtype in spcidMtype[2]:
                f.write(mtype + "\n")
            f.write("\n")
    


def main():
    spcidsFile = "spcids.txt"
    datasource = "datasource.ini"
    specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C144/'\
                       'HDD SPC Monitoring Parameter Specification rev.4.1_jc.xls'
    outputModelset(datasource, spcidsFile, specificationXls)


if __name__ == '__main__':
    main()
    
