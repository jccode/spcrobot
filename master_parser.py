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

    COL_IDX_WEBSPC2_SPCID = 1
    COL_IDX_WEBSPC2_MAPPING_BEGIN = 4
    COL_IDX_WEBSPC2_MAPPING_END = 8
    COL_IDX_WEBSPC2_ALIAS_BEGIN = 9
    COL_IDX_WEBSPC2_ALIAS_END = 12
        
    ROW_FROM_SPCID = 4
    ROW_FROM_WEBSPC2 = 4

    ROWOFFSET_PROCESS = 3
    ROWOFFSET_FREQUENCY = 6
    
    
    def __init__(self, masterFile):
        self._masterFile = masterFile
        self.items = {}         # spcItems. key:spcid, value:spcItem
        self.constructItems()


    def findSimilar(self, spcids):
        """
        Find similar spcid with the given spcid

        Arguments:
        - `self`:
        - `spcids`:
        """
        pass


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
            
            item = {}
            spcid = sheet.cell(row, self.COL_IDX_SPCID["SPCID"]).value
            item["SPCID"] = spcid
            item["TABLE_NAME"] = sheet.cell(row, self.COL_IDX_SPCID["TABLE_NAME"]).value
            item["LOADER_PROFILE"] = sheet.cell(row, self.COL_IDX_SPCID["LOADER_PROFILE"]).value
            item["OPERATION"] = sheet.cell(row, self.COL_IDX_SPCID["OPERATION"]).value
            item["PROCESS"] = sheet.cell(row, self.COL_IDX_SPCID["PROCESS"]).value
            item["PLOT_UNIT"] = sheet.cell(row, self.COL_IDX_SPCID["PLOT_UNIT"]).value
            item["PLOT_ITEM"] = sheet.cell(row, self.COL_IDX_SPCID["PLOT_ITEM"]).value
        
            self.items[spcid] = item

            
    def __fromSheetWebspc2(self, sheet):
        """
        Construct items from WEBSPC2 sheet

        Arguments:
        - `self`:
        - `sheet`:
        """
        rowoffset = 0
        spcid = ''
        mapping = []
        for row in range(sheet.nrows):
            if row < self.ROW_FROM_WEBSPC2-1:
                continue

            _spcid = sheet.cell(row, self.COL_IDX_WEBSPC2_SPCID).value
            print _spcid, '**', spcid, '**'
            if _spcid:       # new spcid begin
                print '_spcid not null'
                if mapping:
                    print mapping
                    self.items[spcid]["MAPPING"] = ''.join(mapping)
                spcid = _spcid;
                rowoffset = 0
                mapping = []
                
            else:               # spcid is empty
                rowoffset += 1
                if rowoffset == self.ROWOFFSET_PROCESS:
                    aliasProcess = []
                    for col in range(self.COL_IDX_WEBSPC2_ALIAS_BEGIN, self.COL_IDX_WEBSPC2_ALIAS_END+1):
                        aliasProcess.append(sheet.cell(row, col).value)
                    self.items[spcid]["ALIAS_PROCESS"] = aliasProcess

                if rowoffset == self.ROWOFFSET_FREQUENCY:
                    aliasFrequency = []
                    for col in range(self.COL_IDX_WEBSPC2_ALIAS_BEGIN, self.COL_IDX_WEBSPC2_ALIAS_END+1):
                        aliasFrequency.append(sheet.cell(row, col).value)
                    self.items[spcid]["ALIAS_FREQUENCY"] = aliasFrequency

            # assemble mapping
            for col in range(self.COL_IDX_WEBSPC2_MAPPING_BEGIN, self.COL_IDX_WEBSPC2_MAPPING_END+1):
                if sheet.cell(row, col).value:
                    mapping.append(1)
                else:
                    mapping.append(0)
            
                    
            
    def flatOutputItems(self):
        """
        Output the items flat.

        Arguments:
        - `self`:
        """
        for spcItem in self.items.itervalues():
            print spcItem
        
    
        

def test():
    """
    """
    masterFile = 'C050_HDDWebSPC2_SPCID_Master_List_3.2.xls'
    mp = MasterParser(masterFile)
    mp.flatOutputItems()

    
if __name__ == '__main__':
    test()
