#!/usr/bin/python

# ####################
# The main entrance of spcrobot
# ####################

import spec_parser
import extraction_gen


def main():
    """
    main
    """
    inputFile = 'spcids.txt'
    spcids = readInputSpcids(inputFile)
    specificationXls = 'd:/HGST/MFG/processing/HDD_WEBSPC_CR/C140_C141_C142/'\
                       'HDD SPC Monitoring Parameter Specification rev.4.0_jc.xls'
    sp = SpecificationParser(specificationXls)
    print spcids


def readInputSpcids(inputFile):
    """
    Read input spcids from input file

    Arguments:
    - `inputFile`:

    Return:
    - list of spcids
    """
    lines = [line.strip() for line in open(inputFile)]
    return lines


if __name__ == '__main__':
    main()
    
