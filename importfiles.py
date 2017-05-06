from __future__ import division
import logging
import pickle
import operator
import os
import math
import sys
from random import randrange
import random
from collections import Counter
from collections import defaultdict
from operator import itemgetter
from event import Script
from event import Event
import constants as const

#ANNDIR = 'LDC2015E73'
#ANNDIR = 'LDC2017E08/'
ANNDIR = const.ANNDIR

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

def loadAnnotation(fileName):
    """
    :param args:
    :return:
    """
    path = os.getcwd()
    eventsObjList = []
    with open(path + '/' + ANNDIR + '/' + fileName + '.ann', "r") as f:
        lines = f.readlines()
    i = 0
    eventList = []
    for line in lines:
        if line[0] != 'R':
            logging.debug("This is the line: %s" % line)
            if i < 3:
                eventList.append(line)
            i = 0
            event = Event(eventList, fileName)
            eventsObjList.append(event)
    return eventsObjList

def main():

#    script = Script('NYT_ENG_20130822.0211')
    script = Script('XIN_ENG_20090915.0127')
#    script = Script('bolt-eng-DF-170-181103-8900160')
#    annotations = loadAnnotation('bolt-eng-DF-170-181103-8900160')
    #for event in script.eventsList:
    #    logging.debug("This is the tag of the event: %s" % event.eventTag)
    script.getListOfSubEventClusters()

if __name__ == "__main__": main()
