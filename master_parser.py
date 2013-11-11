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
    
    COL_IDX_WEBSPC2_MAPPING_BEGIN = 4
    COL_IDX_WEBSPC2_MAPPING_END = 8
    COL_IDX_WEBSPC2_ALIAS_BEGIN = 9
    COL_IDX_WEBSPC2_ALIAS_END = 12
        
    ROW_FROM_SPCID = 2
    ROW_FROM_WEBSPC2 = 3
    
    
    def __init__(self, masterFile):
        self._masterFile = masterFile
        self.items = []         # for spcid sheet
        self.webspcItems = []   # for webspc2 sheet
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
            if row < self.ROW_FROM_SPCID:
                continue

            item = {}
            item["SPCID"] = sheet.cell(row, self.COL_IDX_SPCID["SPCID"]).value
            item["TABLE_NAME"] = sheet.cell(row, self.COL_IDX_SPCID["TABLE_NAME"]).value
            item["LOADER_PROFILE"] = sheet.cell(row, self.COL_IDX_SPCID["LOADER_PROFILE"]).value
            item["OPERATION"] = sheet.cell(row, self.COL_IDX_SPCID["OPERATION"]).value
            item["PROCESS"] = sheet.cell(row, self.COL_IDX_SPCID["PROCESS"]).value
            item["PLOT_UNIT"] = sheet.cell(row, self.COL_IDX_SPCID["PLOT_UNIT"]).value
            item["PLOT_ITEM"] = sheet.cell(row, self.COL_IDX_SPCID["PLOT_ITEM"]).value
        
            self.items.append(item)

            
    def __fromSheetWebspc2(self, sheet):
        """
        Construct items from WEBSPC2 sheet

        Arguments:
        - `self`:
        - `sheet`:
        """
        for row in range(sheet.nrows):
            if row < self.ROW_FROM_WEBSPC2:
                continue
            

    
        

def test():
    """
    """
    masterFile = 'C050_HDDWebSPC2_SPCID_Master_List_3.2.xls'
    mp = MasterParser(masterFile)
    print mp.items
    print 'master parser'

    
if __name__ == '__main__':
    test()
