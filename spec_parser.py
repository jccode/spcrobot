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
        "SITE": {"PRB": 3, "GSP": 5, "SGP": 6},
        "PROCESS_NAME": 9,
        "PRODUCT": 10,
        "DATA": 11,
        "TARGET_DATA": 12,
        "GROUPING_KEYS": 13,
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
        rets = filter(lambda item: item["SPCID"] == spcid, self.items)
        if(len(rets) == 0):
            raise Exception('Cannot find {0} spcid.'.format(spcid))
        else:
            return rets[0];



    def getSpcids(self, spcids):
        """
        Get items by spcids

        Arguments:
        - `self`:
        - `spcids`: list of spcid
        """
        return map(self.getSpcid, spcids)
        


    def getExtraField(self, spcId):
        """
        Get extra field for ut sql

        Arguments:
        - `self`:
        - `spcId`:
        """
        mapping = {'ByLine': 'ASMLINE',
                   'ByHead': 'UPDOWN',
                   'ByHeadNo': 'HEADNO', 
                   'ByCell': 'CELLID',
                   'ByTester': 'TESTERID',
                   'ByHeadGrade': 'HEADGRADE',
                   'BySswType': 'SSWTYPE'}
        
        spcItem = self.getSpcid(spcId)
        field = ''
        chartType = spcItem['CHART_TYPE']
        plotUnit = spcItem['PLOT_UNIT']
        for unit in plotUnit:
            field += (',' + mapping[unit])
        if chartType == 'Mean-Sigma':
            field += ',AVG,STD'
        else:
            field += ",RATIO"
        return (spcItem['SPCID'], field)
        

    def getExtraFields(self, spcids):
        """
        Get extra fields

        Arguments:
        - `self`:
        - `spcids`:
        """
        return map(self.getExtraField, spcids)
    
    
    def constructItems(self):
        """
        construct items, and set the value to self.items
        each item is a dictionary.

        CHART_TYPE :: Mean-Sigma, Yield, Defective, Total-Defective, Error-Ratio, Combined-Error-Ratio
        GROUPING_KEYS :: MTYPE, PRODUCT, PROD_DISKNUM
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
                    item["PRODUCT"] = sheet.cell(row, self.COL_INDEX["PRODUCT"]).value

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
                        if sheet.cell(row, col).value:
                            sites.add(site)
                    item["SITE"] = sites

                    # GROUPING_KEYS
                    groupingKey = sheet.cell(row, self.COL_INDEX["GROUPING_KEYS"]).value.lower()
                    item["GROUPING_KEYS"] = self._detectGroupingKeys(groupingKey)
                    
                    
                    # TARGET_DATA, PROPERTIES(for generate makeExtractionXML.pl)
                    
                    targetData = sheet.cell(row, self.COL_INDEX["TARGET_DATA"]).value.lower()
                    properties = self._detectProperties(targetData, plotUnit)
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

    def _detectGroupingKeys(self, groupingKey):
        """
        detect grouping keys
        Arguments:
        - `self`:
        - `groupingKey`:
        """
        if "m/t" in groupingKey:
            return "MTYPE"
        if "product" in groupingKey and "disknum" in groupingKey:
            return "PROD_DISKNUM"
        if "product" in groupingKey:
            return "PRODUCT"

    def _detectProperties(self, targetData, plotUnit):
        """
        PROPERTIES: Rework, Prime, Latest_Data, Rework_Only, First_Cycle_Only, Pass_Only, Without_HSAL, Filter_Fail, Exclude_Trial, Exclude_Inline_Retest, Exclude_Ship_Return

        Arguments:
        - `self`:
        - `targetData`:
        - `plotUnit`:
        """
        properties = {}
        if "include rework" in targetData:
            properties["Exclude_Ship_Return"] = False
        elif "exclude rework" in targetData:
            properties["Exclude_Ship_Return"] = True
        elif "rework" in plotUnit or "rework" in targetData:
            properties['Rework'] = True
        else:
            pass
            
        if "prime" in plotUnit or "prime" in targetData:
            properties["Prime"] = True
        if "latest" in targetData:
            properties["Latest_Data"] = True
        if "rework only" in targetData:
            properties["Rework_Only"] = True
            
        if "new only" in targetData or "cycle 1" in targetData:
            properties["First_Cycle_Only"] = True
        elif "include rework" in targetData or "include retest" in targetData:
            properties["First_Cycle_Only"] = False
        else:
            pass

        if ("pass and fail" in targetData or "pass & fail" in targetData
            or "cycle > 1" in targetData or "cycle >1" in targetData):
            properties["Pass_Only"] = False
        elif ("test pass" in targetData
              or "only passer" in targetData or "only pass" in targetData
              or "passer only" in targetData or "only passer" in targetData):
            properties["Pass_Only"] = True
        else:
            pass

        if ("with hsat" in targetData or "with hddt" in targetData
            or "include trial unit" in targetData):
            properties["Exclude_Trial"] = False
        elif ("without hsat" in targetData or "without hddt" in targetData
              or "exclude trial unit" in targetData or "without hdd trial" in targetData
              or "trial" in targetData):
            properties["Exclude_Trial"] = True
        else:
            pass

        if "all except" in targetData:
            properties["Filter_Fail"] = True
            
        if "include inline retest fail" in targetData:
            properties["Exclude_Inline_Retest"] = False
        elif "exclude inline retest fail" in targetData:
            properties["Exclude_Inline_Retest"] = True
        else:
            pass
            
        
            
        return properties
            
            
    def _detectPlotUnit(self, plotUnit):
        """
        PLOT_UNIT: ByLine, ByHead, ByHeadNo, ByCell, BySswType, ByHeadGrade, ByTester
        @return array
        """
        plotUnits = Set([])

        # by lpp is rather special. complete statement is:
        # By Lpp line(=TESTERID) .
        # so, need to return immediately when encounter "by lpp".
        if "by lpp" in plotUnit:
            plotUnits.add("ByCell")
            return plotUnits

        # It's not always true that "by" in front of "Tester"
        if "tester" in plotUnit:
            plotUnits.add("ByTester")

        # For others, "by" should ahead of the type.
        # if "by" not in plotUnit:
        #     return plotUnits
        
        if "line" in plotUnit:
            plotUnits.add("ByLine")
            
        if "head" in plotUnit:
            if "no" in plotUnit:
                plotUnits.add("ByHeadNo")
            elif "grade" in plotUnit:
                plotUnits.add("ByHeadGrade")
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

        elif "p-chart" in chartTypeValue or "p chart" in chartTypeValue:

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

    # specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
    #                    'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    specificationXls = 'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'

    sp = SpecificationParser(specificationXls)
    
    # sp.constructItems()
    # print sp.getSpcid('CC1800_PR01B_01H')
    # print sp.getSpcids(['CC1800_PR01B_01H', 'ET1700_PR01A_08H'])

    # print sp.getExtraField('CC1800_PR01B_01H')
    print sp.getExtraFields(['CC1800_PR01B_01H', 'ET3100_PR01B_08H'])
    
    # sp.listItems()
    

