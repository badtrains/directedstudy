from __future__ import division
import logging
import pickle
import operator
import os
import shutil
import re
import math
import sys
from random import randrange
import random
from collections import Counter
from collections import defaultdict
from operator import itemgetter
from event import Script
from event import Event

#ANNDIR = 'LDC2015E73'
ANNDIR = 'LDC2017E08/'

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)


def getDirectoryListing(path):
    # for dirname, dirnames, filenames in os.walk(path):
    #     continue
    for dirname, dirnames, filenames in os.walk(path):
        continue
    filenamespath = [f for f in filenames if f.endswith(".ann")]
    return filenamespath


ANNDIR = 'LDC2017E08/'
ORIGDIR = 'LDC2017E08.M/'

def main():

    files = getDirectoryListing('LDC2017E08.M')
    if not os.path.exists(ANNDIR):
        os.makedirs(ANNDIR, mode=0755)
    else:
        shutil.rmtree(ANNDIR)
        os.makedirs(ANNDIR, mode=0755)

    for file in files:
        listRLines = []
        with open(ORIGDIR+file, 'r') as f:
            lines = f.readlines()
        with open(ANNDIR+file, 'w') as df:
            for line in lines:
                if line.startswith('R'):
                    listRLines.append(line)
                else:
                    df.write(line)
            for line in listRLines:
                if 'Coreference' in line:
                    df.write(line)
            for line in listRLines:
                if 'Subevent' in line:
                    df.write(line)
            for line in listRLines:
                if 'After' in line:
                    df.write(line)

if __name__ == "__main__": main()
