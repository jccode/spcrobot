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
        # destItems = filter(lambda item: item["PROFILE"] in profileIds, profiles)
        destItems = self.getProfilesByProfileIds(profileIds)

        def _findSimilarOne(destItem):
            
            def _dist(item, field):
                return 1 if item[field] == destItem[field] else 0
            
            ret1 = filter(lambda item: item["MAPPING"] == destItem["MAPPING"]
                          and item["PLOT_UNIT"] == destItem["PLOT_UNIT"]
                          , srcItems)

            ld = len(destItem["PROFILE"])
            if len(ret1) > 0:
                ret2 = map(lambda item: 40 * _dist(item, "PROCESS_ID")
                           + 20 * _dist(item, "PLOT_ITEM")
                           + 10 * _dist(item, "OPERATION")
                           + 5 * _dist(item, "FREQUENCY")
                           - 5 * (1 if len(item["PROFILE"]) != ld else 0)
                           , ret1)
                ret3 = max(ret2)
                idx = ret2.index(ret3)
                return ret1[idx]
                
            else:
                return None
            
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
            
        # clear those profile with "MAPPING"
        self.items = dict((k, v) for k, v in self.items.iteritems() if "MAPPING" in v )

        
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
            plotItemValue = sheet.cell(row, self.COL_IDX_SPCID["PLOT_ITEM"]).value
            plotUnit = sheet.cell(row, self.COL_IDX_SPCID["PLOT_UNIT"]).value
            operationValue = sheet.cell(row, self.COL_IDX_SPCID["OPERATION"]).value
            profileValue = sheet.cell(row, self.COL_IDX_SPCID["LOADER_PROFILE"]).value
            processId = profileValue[2:6]
            frequency = profileValue[12:15]

            lowerplotItemValue = plotItemValue.lower()
            if "mean" in lowerplotItemValue and "cpk" in lowerplotItemValue:
                plotItem = "CPK"
            elif "mean" in lowerplotItemValue:
                plotItem = "MeanSigma"
            else:
                plotItem = plotItemValue
            
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
                item["FREQUENCY"] = frequency
                
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

                
    def getProfileBySpcid(self, spcid):
        """
        Get profile by spcid

        Arguments:
        - `self`:
        - `spcid`:
        """
        profiles = self.items.values()
        return filter(lambda item: item["SPCID"] == spcid, profiles)


    def getProfilesBySpcids(self, spcids):
        """
        Get profiles 

        Arguments:
        - `self`:
        - `spcids`:
        """
        return map(self.getProfileBySpcid, spcids)

    def getProfileByProfileId(self, profileId):
        """
        Get profile by profileId

        Arguments:
        - `self`:
        - `profileId`:
        """
        profiles = self.items.values()
        return filter(lambda item: item["PROFILE"] == profileId, profiles)[0]

    def getProfilesByProfileIds(self, profileIds):
        """
        Get profiles by profileIds
        Arguments:
        - `self`:
        - `profileIds`:
        """
        return map(self.getProfileByProfileId, profileIds)
    
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
    # print mp.getProfileBySpcid('ET1985_PR01A_01H')
    # print mp.getProfilesBySpcids(['ET1985_PR01A_01H', 'MB3700_PR01A_01H'])
    
    # similars = mp.findSimilar(['DT3100_PR01_08H', 'DT3100_YD01_08H', 'DT3600_ER02_08H'])
    # similars2 = mp.findSimilar(['DT3100_PR01_08H', 'DT3600_ER02_08H'])
    # print map(lambda item: item["PROFILE"], similars)
    # print map(lambda item: item["PROFILE"], similars2)
    
    # print mp.findSimilar(['ET1985_PR01_01H', 'MB3700_PR01_01H'])
    # mp.outputMapping()


    

    
def main():
    """
    """
    SEPERATOR = '=================================\n'
    masterFile = 'C050_HDDWebSPC2_SPCID_Master_List_3.2.xls'
    profileIdInput = 'profileIds.txt'
    outputFile = 'master_out.txt'
    profileIds = [line.strip() for line in open(profileIdInput)]

    mp = MasterParser(masterFile)
    similars = mp.findSimilar(profileIds)
    
    with open(outputFile, 'w') as f:
        f.write('load profile to be process\n')
        f.write(SEPERATOR)
        f.write("\n".join(profileIds))
        f.write("\n\n")

        f.write('similar profile\n')
        f.write(SEPERATOR)
        for i in range(len(profileIds)):
            f.write("{0}    similar profile is: {1}\n".format(profileIds[i], similars[i]["PROFILE"]) )
        f.write("\n")
        
    
if __name__ == '__main__':
    # test()
    main()
