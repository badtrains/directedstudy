import os
from random import randint
import random
import constants as const

TOTAL_FILES = const.TOTAL_FILES
DEV_FRACTION = const.DEV_FRACTION
# TOTAL_FILES = 148
# DEV_FRACTION = 20
TRAIN_FILES_NUM = int((TOTAL_FILES/(100.0))*(100-DEV_FRACTION))

class CreateDataSets:
    def __init__(self, path):
        self.path = path
        totalFiles = range(0, TOTAL_FILES)
        filenames = self.getDirectoryListing(self.path)
        self.filenames = [x.replace('.txt', '') for x in filenames]
        self.trainingSetFiles = random.sample(range(0, TOTAL_FILES), TRAIN_FILES_NUM)
        devSetFiles = set(totalFiles) - set(self.trainingSetFiles)
        # Changed temporarily to have one single file
        self.devSetFiles = list(devSetFiles)
        with open('devsetfiles.txt', 'w') as d:
            for devFile in self.devSetFiles:
                d.write('%s\n' % self.filenames[devFile])

    def getDirectoryListing(self, path):
        # for dirname, dirnames, filenames in os.walk(path):
        #     continue
        for dirname, dirnames, filenames in os.walk(path):
            continue
        filenamespath = [f for f in filenames if f.endswith(".txt")]
        return filenamespath

def main():
#    dataSets = CreateDataSets('LDC2015E73/')
    dataSets = CreateDataSets('LDC2017E08/')
    test = [dataSets.filenames[x] for x in dataSets.trainingSetFiles]
    print(test)
"""
How to copy the files
for f in `cat devsetfiles.txt`; do cp data/LDC2015E73/$f.ann data/goldfiles/; done
"""


if __name__ == "__main__": main()
