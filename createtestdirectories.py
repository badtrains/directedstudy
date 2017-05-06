from __future__ import division
import logging
import pickle
import operator
import os
import shutil
from shutil import copyfile
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


ANNDIR = 'LDC2017E08'
ORIGDIR = 'LDC2017E08.M/'
SCRIPTSPERDIR = 10

def main():

    files = getDirectoryListing(ANNDIR)
    filesNoExt = []
    for file in files:
        m = re.match('^(.*)\.ann', file)
        fileName = m.group(1)
        filesNoExt.append(fileName)

    nFiles = len(filesNoExt)
    nDirs = int(nFiles/SCRIPTSPERDIR)
    extra = nFiles % SCRIPTSPERDIR
    if extra != 0:
        nDirs = nDirs+1

    for i in range(1,nDirs):
        dirName = ANNDIR+'-'+str(i)
        if not os.path.exists(dirName):
            os.makedirs(dirName, mode=0755)
        else:
            shutil.rmtree(dirName)
            os.makedirs(dirName, mode=0755)
        filesToCopy = filesNoExt[SCRIPTSPERDIR*(i-1):SCRIPTSPERDIR*i]
        for file in filesToCopy:
            src = ANNDIR+'/'+file+'.txt'
            dst = dirName+'/'+file+'.txt'
            copyfile(src, dst)

            src = ANNDIR+'/'+file+'.ann'
            dst = dirName+'/'+file+'.ann'
            copyfile(src, dst)

    filesToCopy = filesNoExt[SCRIPTSPERDIR * (nDirs-1):]

    dirName = ANNDIR + '-' + str(nDirs)
    if not os.path.exists(dirName):
        os.makedirs(dirName, mode=0755)
    else:
        shutil.rmtree(dirName)
        os.makedirs(dirName, mode=0755)

    for file in filesToCopy:
        src = ANNDIR + '/' + file + '.txt'
        dst = dirName + '/' + file + '.txt'
        copyfile(src, dst)

        src = ANNDIR + '/' + file + '.ann'
        dst = dirName + '/' + file + '.ann'
        copyfile(src, dst)

if __name__ == "__main__": main()
