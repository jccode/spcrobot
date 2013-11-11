#!/usr/bin/python

from mmap import mmap, ACCESS_READ
from xlrd import open_workbook
from re import findall
from sets import Set

# #################### Class SpecificationParser ####################

class SpecificationParser(object):
    """
    HDD SPC Monitoring Parameter Specification xxx.xls Parser
    """

    """ Constants """
    COL_INDEX = {
        "SPCID": 1,
        "SITE": {"PRB": 3, "GSP": 4, "SGP": 5},
        "PROCESS_NAME": 9,
        "PRODUCT": 10,
        "DATA": 11,
        "TARGET_DATA": 12,
        "PLOT_UNIT": 14,
        "SAMPLE_SIZE": 15,
        "CARRY_OVER": 16,
        "CHART_TYPE": 17,
        "FREQUENCY": 18
    }
    
    
    def __init__(self, filePath):
        """
        """
        self.file = filePath
        self.items = []         # spcid items
        self.constructItems()
        

    def getSpcid(self, spcid):
        """
        Get item by spcid

        Arguments:
        - `self`:
        - `spcid`:
        """
        return filter(lambda item: item["SPCID"] == spcid, self.items)[0]


    def getSpcids(self, spcids):
        """
        Get items by spcids

        Arguments:
        - `self`:
        - `spcids`: list of spcid
        """
        return map(self.getSpcid, spcids)
        
    
    def findSimilar(self, spcids):
        """
        Find the spcid similar with the given spcid.

        Arguments:
        - `self`:
        - `spcids`:
        """
        srcItems = filter(lambda item: item["SPCID"] not in spcids, self.items)
        destItems = filter(lambda item: item["SPCID"] in spcids, self.items)

        def _findSimilarOne(descItem):
            ret1 = filter(lambda item: item["CHART_TYPE"] == descItem["CHART_TYPE"]
                          and item["PLOT_UNIT"] == descItem["PLOT_UNIT"]
                          and item["PROCESS_NAME"] == descItem["PROCESS_NAME"], srcItems)
            if len(ret1) > 0:
                ret1_1 = filter(lambda item: item["PROCESS_ID"] == descItem["PROCESS_ID"], ret1)
                return ret1_1[0] if len(ret1_1) > 0 else ret1[0]
            else:
                return None

        return map(_findSimilarOne, destItems)
        
    
    def constructItems(self):
        """
        construct items, and set the value to self.items
        each item is a dictionary.

        CHART_TYPE :: Mean-Sigma, Yield, Defective, Total-Defective, Error-Ratio, Combined-Error-Ratio
        """
        wb = open_workbook(self.file)
        for s_index in range(wb.nsheets):
            sheet = wb.sheet_by_index(s_index)
            if s_index < 4 or sheet.name == "Legacy Item":         # skip the first 4 sheet & last "Legacy" sheet
                continue

            # print 'Sheet:', sheet.name
            
            for row in range(sheet.nrows):
                if row < 1: # skip the first line
                    continue

                try: 
                    # construct
                    spcid = sheet.cell(row, self.COL_INDEX["SPCID"]).value
                    chartType = sheet.cell(row, self.COL_INDEX["CHART_TYPE"]).value.lower()

                    # if spcid is empty, the chartType should be sigma or cpk. skip.
                    if not spcid:   
                        if not (chartType == "mean" or chartType == "sigma" or chartType == "cpk" ):
                            errorMsg = "{0} file parse error in {1} sheet {2} row." \
                                       "The chart_type column should be 'mean' or 'sigma' or 'cpk'" \
                                       .format(self.file, sheet.name, row)
                            raise Exception(errorMsg)
                        else:
                            continue

                    processId = spcid[2:6]
                    spcidType = spcid[7:9] # ER,YD,PR etc
                    frequency = spcid[-3:]

                    item = {}
                    item["SPCID"] = spcid
                    item["PROCESS_ID"] = processId
                    item["SPCID_TYPE"] = spcidType
                    item["FREQUENCY"] = frequency
                    item["PROCESS_NAME"] = sheet.cell(row, self.COL_INDEX["PROCESS_NAME"]).value
                    item["TARGET_DATA"] = sheet.cell(row, self.COL_INDEX["TARGET_DATA"]).value

                    sampleSize = sheet.cell(row, self.COL_INDEX["SAMPLE_SIZE"]).value
                    item["SAMPLE_SIZE"] = (findall('\d+', sampleSize))[0]

                    carryOver = sheet.cell(row, self.COL_INDEX["CARRY_OVER"]).value.upper()
                    item["CARRY_OVER"] = True if carryOver == 'Y' else False

                    unit = "HSA" if "HSA" in sheet.name else "HDD"
                    item["UNIT"] = unit

                    data = sheet.cell(row, self.COL_INDEX["DATA"]).value.lower()
                    item["DATA"] = data
                    item["PRODUCT"] = sheet.cell(row, self.COL_INDEX["PRODUCT"]).value.lower()

                    # CHART_TYPE
                    detectedChartType = self._detectChartType(chartType, data, spcidType)
                    # if not detectedChartType:
                    #     errorMsg = "detect chart type fail, in sheet: {0}, row: {1}, spcid:{2},"\
                    #                "chartType:{3}, data:{4}".format(sheet.name, row, spcid, chartType, data)
                    #     raise Exception(errorMsg)
                    item["CHART_TYPE"] = detectedChartType

                    # PLOT_UNIT
                    plotUnit = sheet.cell(row, self.COL_INDEX["PLOT_UNIT"]).value.lower()
                    item["PLOT_UNIT"] = self._detectPlotUnit(plotUnit)

                    # SITE
                    sites = Set([])
                    for site,col in self.COL_INDEX["SITE"].iteritems():
                        if not sheet.cell(row, col).value:
                            sites.add(site)
                    item["SITE"] = sites

                    # TARGET_DATA, PROPERTIES(for generate makeExtractionXML.pl)
                    targetData = sheet.cell(row, self.COL_INDEX["TARGET_DATA"]).value.lower()
                    properties = self._detectProperties(processId, targetData, plotUnit)
                    item["PROPERTIES"] = properties

                    self.items.append(item)

                except Exception as e:
                    print type(e)
                    print e.args
                    print e
                    errorMsg = "Some error occur in sheet: {0}, row: {1}, spcid: {2}"\
                               .format(sheet.name, row, spcid)
                    raise Exception(errorMsg)
                
        # ok
        # self.listItems()

    def _detectProperties(self, targetData, plotUnit):
        """
        PROPERTIES: Rework, Prime, Latest_Data, Rework_Only, New_Only, Pass_And_Fail, Without_HSAL, Cycle_GT_1

        Arguments:
        - `self`:
        - `targetData`:
        - `plotUnit`:
        """
        properties = Set([])
        if "rework" in plotUnit or "rework" in targetData:
            properties.add("Rework")
        if "prime" in plotUnit or "prime" in targetData:
            properties.add("Prime")
        if "latest data" in targetData:
            properties.add("Latest_Data")
        if "rework only" in targetData:
            properties.add("Rework_Only")
        if "new only" in targetData:
            properties.add("New_Only")
        if "pass and fail" in targetData:
            properties.add("Pass_And_Fail")
        if "without hsat" in targetData:
            properties.add("Without_HSAL")
        if "cycle > 1" in targetData or "cycle 1" in targetData or "cycle >1" in targetData:
            properties.add("Cycle_GT_1")
            
            
    def _detectPlotUnit(self, plotUnit):
        """
        PLOT_UNIT: ByLine, ByHead, ByHeadNo, ByCell, BySswType
        @return array
        """
        plotUnits = Set([])
        if "by" not in plotUnit:
            return plotUnits
        
        if "line" in plotUnit:
            plotUnits.add("ByLine")
            
        if "head" in plotUnit:
            if "no" in plotUnit:
                plotUnits.add("ByHeadNo")
            else:
                plotUnits.add("ByHead")

        if "cell" in plotUnit:
            plotUnits.add("ByCell")

        if "ssw" in plotUnit:
            plotUnits.add("BySswType")

        return plotUnits
            

    def _detectChartType(self, chartTypeValue, dataValue, spcidType):
        """
        CHART_TYPE :: Mean-Sigma, Yield, Defective, Total-Defective, Error-Ratio, Combined-Error-Ratio
        """
        chartTypeRet = ""
        if "mean" in chartTypeValue:
            chartTypeRet = "Mean-Sigma"

        elif "yield" in chartTypeValue:
            chartTypeRet = "Yield"

        elif "p-chart" in chartTypeValue:

            if "yield" in dataValue: # yield
                chartTypeRet = "Yield"

            elif "defective" in dataValue and "total" in dataValue: # total-defective
                chartTypeRet = "Total-Defective"

            elif "defective" in dataValue: # defective
                chartTypeRet = "Defective"

            elif "error" in dataValue or spcidType == "ER": # error-ratio & combined-error-ratio
                if "combined" in dataValue:
                    chartTypeRet = "Combined-Error-Ratio"
                else:
                    chartTypeRet = "Error-Ratio"
            else:
                raise Exception("Detect chart type fail.")

        else:
            raise Exception("Detect chart type fail.")

        return chartTypeRet


    def simpleWalkThroughExcelFiles(self):
        wb = open_workbook(specificationXls)
        for s_index in range(wb.nsheets):
            if s_index < 4:         # skip the first 4 sheet.
                continue
            else:
                sheet = wb.sheet_by_index(s_index)
                print 'Sheet:', sheet.name
                for row in range(sheet.nrows):
                    if row < 1: # skip the first line
                        continue
                    values = []
                    for key in self.COL_INDEX:
                        v = sheet.cell(row, self.COL_INDEX[key]).value
                        values.append(key + ":" + (repr(v) if type(v) == float else v))
                    print row, ','.join(values).encode('utf-8')
                print
        


    def listItems(self):
        """
        print self.items
        """
        for item in self.items:
            values = []
            for value in item.itervalues():
                if type(value) is list:
                    values.append(";".join(value))
                else:
                    values.append(value if type (value) is str else repr(value))
            print ','.join(values)
        print


    def test(self):
        for key in self.COL_INDEX:
            print key, ":", self.COL_INDEX[key]
        

# #################### End of class SpecificationParser ####################            

        
if __name__ == '__main__':

    specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
                       'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    # specificationXls = 'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'

    sp = SpecificationParser(specificationXls)
    
    # sp.constructItems()
    # print sp.getSpcid('CC1800_PR01B_01H')
    # print sp.getSpcids(['CC1800_PR01B_01H', 'ET1700_PR01A_08H'])
    # print sp.findSimilar(['CC1800_PR01B_01H', 'ET3100_PR01B_08H'])
    sp.listItems()
    

