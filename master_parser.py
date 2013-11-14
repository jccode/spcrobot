#!/usr/bin/python

from xlrd import open_workbook


class MasterParser(object):
    """
    HDD WEBSPC2 SPCID Master List.xls Parser
    """

    """ Constants """
    COL_IDX_SPCID = {
        "SPCID": 1, 
        "TABLE_NAME": 2,
        "LOADER_PROFILE": 3,
        "OPERATION": 4,
        "PROCESS": 6,
        "PLOT_UNIT": 7,
        "PLOT_ITEM": 9
    }

    COL_IDX_WEBSPC2_PROFILE = 1
    COL_IDX_WEBSPC2_MAPPING_BEGIN = 4
    COL_IDX_WEBSPC2_MAPPING_END = 8
    COL_IDX_WEBSPC2_ALIAS_BEGIN = 9
    COL_IDX_WEBSPC2_ALIAS_END = 12
        
    ROW_FROM_SPCID = 4
    ROW_FROM_WEBSPC2 = 4

    ROWOFFSET_PROCESS = 3
    ROWOFFSET_FREQUENCY = 6

    
    showNotMatchItems = False
    
    
    def __init__(self, masterFile):
        self._masterFile = masterFile
        self.items = {}         # spcItems. key:spcid, value:spcItem
        self.constructItems()


    def findSimilar(self, profileIds):
        """
        Find similar spcid with the given spcid

        Arguments:
        - `self`:
        - `spcids`:
        """
        profiles = self.items.values()
        srcItems = filter(lambda item: item["PROFILE"] not in profileIds, profiles)
        destItems = filter(lambda item: item["PROFILE"] in profileIds, profiles)

        
        def _findSimilarOne(destItem):
            ret1 = filter(lambda item: item["MAPPING"] == destItem["MAPPING"], srcItems)
            return ret1
            
        return map(_findSimilarOne, destItems)

    def constructItems(self):
        """
        parse xls and init items
        """
        wb = open_workbook(self._masterFile)
        for sheet in wb.sheets():
            sheetName = sheet.name.upper()
            if sheetName == "SPCID":
                self.__fromSheetSpcid(sheet)
            elif sheetName == "WEBSPC2":
                self.__fromSheetWebspc2(sheet)
            else:
                pass


    def __fromSheetSpcid(self, sheet):
        """
        Construct items from SPCID sheet

        Arguments:
        - `self`:
        - `sheet`:
        """
        for row in range(sheet.nrows):
            if row < self.ROW_FROM_SPCID-1:
                continue

            spcid = sheet.cell(row, self.COL_IDX_SPCID["SPCID"]).value
            tableName = sheet.cell(row, self.COL_IDX_SPCID["TABLE_NAME"]).value
            process = sheet.cell(row, self.COL_IDX_SPCID["PROCESS"]).value
            plotItem = sheet.cell(row, self.COL_IDX_SPCID["PLOT_ITEM"]).value
            plotUnitValue = sheet.cell(row, self.COL_IDX_SPCID["PLOT_UNIT"]).value
            operationValue = sheet.cell(row, self.COL_IDX_SPCID["OPERATION"]).value
            profileValue = sheet.cell(row, self.COL_IDX_SPCID["LOADER_PROFILE"]).value
            processId = profileValue[2:6]

            lowerPlotUnitValue = plotUnitValue.lower()
            if "mean" in lowerPlotUnitValue and "cpk" in lowerPlotUnitValue:
                plotUnit = "CPK"
            elif "mean" in lowerPlotUnitValue:
                plotUnit = "MeanSigma"
            else:
                plotUnit = plotUnitValue
            
            profiles = profileValue.split("\n")
            operations = operationValue.split("\n")
            lenProfiles = len(profiles)
            lenOperations = len(operations)

            
            for i in range(lenProfiles):
                item = {}
                profile = profiles[i]
                item["PROFILE"] = profile
                item["TABLE_NAME"] = tableName
                item["PROCESS"] = process
                item["PLOT_ITEM"] = plotItem
                item["SPCID"] = spcid
                item["PROCESS_ID"] = processId
                
                item["PLOT_UNIT"] = plotUnit
                
                j = i if i < lenOperations else (lenOperations - 1)
                item["OPERATION"] = operations[j][5:]
                
                self.items[profile] = item

            
    def __fromSheetWebspc2(self, sheet):
        """
        Construct items from WEBSPC2 sheet

        Arguments:
        - `self`:
        - `sheet`:
        """
        rowoffset = 0
        profile = ''
        mapping = []
        errorOccur = False

        for row in range(sheet.nrows):
            if row < self.ROW_FROM_WEBSPC2-1:
                continue

            try:
                _profile = sheet.cell(row, self.COL_IDX_WEBSPC2_PROFILE).value
                if _profile:       # new profile begin
                    if errorOccur:
                        mapping = []
                        errorOccur = False
                        # delete it from self.items
                        # del self.items[profile]
                        
                    if mapping:
                        self.items[profile]["MAPPING"] = ''.join(mapping)

                    profile = _profile;
                    rowoffset = 0
                    mapping = []

                else:               # spcid is empty
                    if errorOccur:
                        continue
                        
                    rowoffset += 1
                    if rowoffset == self.ROWOFFSET_PROCESS:
                        aliasProcess = []
                        for col in range(self.COL_IDX_WEBSPC2_ALIAS_BEGIN, self.COL_IDX_WEBSPC2_ALIAS_END+1):
                            aliasProcess.append(sheet.cell(row, col).value)
                        self.items[profile]["ALIAS_PROCESS"] = aliasProcess

                    if rowoffset == self.ROWOFFSET_FREQUENCY:
                        aliasFrequency = []
                        for col in range(self.COL_IDX_WEBSPC2_ALIAS_BEGIN, self.COL_IDX_WEBSPC2_ALIAS_END+1):
                            aliasFrequency.append(sheet.cell(row, col).value)
                        self.items[profile]["ALIAS_FREQUENCY"] = aliasFrequency

                # assemble mapping
                for col in range(self.COL_IDX_WEBSPC2_MAPPING_BEGIN, self.COL_IDX_WEBSPC2_MAPPING_END+1):
                    v = sheet.cell(row, col).value.strip()
                    if v == '0' or v == 'O' or v == 'o':
                        mapping.append(str(1))
                    else:
                        mapping.append(str(0))

            except  KeyError as e:
                if self.showNotMatchItems:
                    # print e
                    errorMsg = "loader profile {0} not found in SPCID sheet.".format(profile)
                    # raise Exception(errorMsg)
                    print errorMsg
                errorOccur = True
                    

    def getProfile(self, spcid):
        """
        Get profile by spcid

        Arguments:
        - `self`:
        - `spcid`:
        """
        profiles = self.items.values()
        return filter(lambda item: item["SPCID"] == spcid, profiles)


    def getProfiles(self, spcids):
        """
        Get profiles 

        Arguments:
        - `self`:
        - `spcids`:
        """
        return map(self.getProfile, spcids)

    
    def flatOutputItems(self):
        """
        Output the items flat.

        Arguments:
        - `self`:
        """
        for spcItem in self.items.itervalues():
            print spcItem
        
    def outputMapping(self):
        """
        Output mappings, purpose for debug
        Arguments:
        - `self`:
        """
        for spcItem in self.items.itervalues():
            try:
                print spcItem["PROFILE"], "\t\t", spcItem["MAPPING"]
            except KeyError as e:
                print spcItem["PROFILE"], " has not keys"

def test():
    """
    """
    masterFile = 'C050_HDDWebSPC2_SPCID_Master_List_3.2.xls'
    mp = MasterParser(masterFile)
    # mp.flatOutputItems()
    # print mp.getProfile('ET1985_PR01A_01H')
    # print mp.getProfiles(['ET1985_PR01A_01H', 'MB3700_PR01A_01H'])
    # print mp.findSimilar('DT3600_ER02_08H')
    mp.outputMapping()
    
    
if __name__ == '__main__':
    test()
