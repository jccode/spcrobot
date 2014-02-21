#!/usr/bin/python

# input files
# ####################

CR_FOLDER = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C159/'

SPECIFICATION_XLS = CR_FOLDER + 'HDD SPC Monitoring Parameter Specification rev.4.4_jc.xls'
MASTER_XLS = CR_FOLDER + 'C050_HDDWebSPC2_SPCID_Master_List_3.5.xls'

EXTRACTION_FILE = "d:/HGST/MFG/processing/HDD_WEBSPC_CR/config_code/etc/extraction.xml"

SPCIDS_FILE = CR_FOLDER + 'spcids_pure.txt'
MASTER_PROFILEIDS_FILE = CR_FOLDER + 'profileIds.txt'

DATASOURCE_FILE = "datasource.ini"

# For evidence_gen.py

LOG_DIR = CR_FOLDER + "ph2/log/"
SQLRET_DIR = CR_FOLDER + 'ph2/sqlret/'
UT_LOG = CR_FOLDER + 'ut.log'


# output files
# ####################

MAIN_OUT = CR_FOLDER + "exs_out.txt"
MODELSET_OUT = CR_FOLDER + "modelset_out.txt"
EVIDENCE_OUT = CR_FOLDER + "evidence_out.txt"
MASTER_OUT = CR_FOLDER + "master_out.txt"
