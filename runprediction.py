import os
import sys
import re
import shutil
import argparse

def getDirectoryListing(path):
    # for dirname, dirnames, filenames in os.walk(path):
    #     continue
    for dirname, dirnames, filenames in os.walk(path):
        continue
    filenamespath = [f for f in filenames if f.endswith(".ann")]
    return filenamespath


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--anndir', help='Annotation directory')
    args = vars(parser.parse_args())
    ANNDIR = args['anndir']

    with open('constantstempl.py', 'r') as f:
        lines = f.readlines()

    files = getDirectoryListing(ANNDIR)
    nFiles = len(files)

    with open('constants.py', 'w') as f:
        f.write("ANNDIR = \'%s/\'\n" % ANNDIR)
        f.write("TOTAL_FILES = %d\n" % nFiles)
        f.write("DEV_FRACTION = 100\n")
        f.write("\n")
        for line in lines[4:]:
            f.write(line)

if __name__=='__main__':
    main(sys.argv[1:])
