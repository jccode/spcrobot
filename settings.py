#!/usr/bin/python

# input files
# ####################

BASE_DIR = '/home/jcchen/hgst/hdd_spc'
# BASE_DIR = 'D:/HGST/MFG/processing/HDD_WEBSPC_CR'
CR_FOLDER = BASE_DIR + '/PN16575'

SPECIFICATION_XLS = CR_FOLDER + '/spec' + '/HDD SPC Monitoring Parameter Specification rev.5.5.xlsx'
MASTER_XLS = CR_FOLDER + '/spec' + '/C050_HDDWebSPC2_SPCID_Master_List_4.4.xls'

EXTRACTION_FILE = BASE_DIR + "/repo" + "/etc/extraction.xml"

SPCIDS_FILE = CR_FOLDER + '/spcids_pure.txt'
MASTER_PROFILEIDS_FILE = CR_FOLDER + '/profileIds.txt'

DATASOURCE_FILE = "datasource.ini"

# For evidence_gen.py

LOG_DIR = CR_FOLDER + "/ut/log"
SQLRET_DIR = CR_FOLDER + '/ut/sqlret'
UT_LOG = CR_FOLDER + '/ut/ut.log'


# output files
# ####################

MAIN_OUT = CR_FOLDER + "/exs_out.txt"
MODELSET_OUT = CR_FOLDER + "/modelset_out.txt"
EVIDENCE_OUT = CR_FOLDER + "/evidence_out.txt"
MASTER_OUT = CR_FOLDER + "/master_out.txt"
