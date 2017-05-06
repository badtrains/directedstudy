from __future__ import division
import copy
import os
import event as ev
import re
import pickle
import numpy as np
import time
import constants as const
import importarticle as ia
import statistics as stats
import logging

from event import Script
from event import Event

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

def saveObj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def loadObj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def createEventsPairScript(event1, event2):
    eventType1 = event1.eventType
    eventSubtype1 = event1.eventSubtype
    eventType2 = event2.eventType
    eventSubtype2 = event2.eventSubtype

    logging.debug("Events: %s, %s", eventType1, eventSubtype1)
    if eventSubtype1 == 'Beborn':
        eventSubtype1 = 'Be-Born'
    if eventSubtype2 == 'Beborn':
        eventSubtype2 = 'Be-Born'

    eventTypeNumber = const.EVENTTYPES[eventType1]
    eventSubTypeNumber = const.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype1)
    eventPairString1 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    logging.debug("Events: %s, %s", eventType2, eventSubtype2)
    eventTypeNumber = const.EVENTTYPES[eventType2]
    eventSubTypeNumber = const.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype2)
    eventPairString2 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    eventPairString = eventPairString1 + 'e' + eventPairString2
    return eventPairString

def getClusterGroup(clusterGroup, event):
    returnValue = -1
    for i in range(len(clusterGroup)):
        if event in clusterGroup[i]:
            returnValue = i
    return returnValue

def main():
    parserName = 'parseroutput-'+const.ANNDIR[0:-1]+'.tbf'
    with open(parserName, 'r') as po:
        lines = po.readlines()
    lines = [l.rstrip() for l in lines]
    probs = stats.computePairsProbabilities()
    countersProbs = probs[0]
    documents = {}
    first = True
    parserNameOut = 'postprocessoutput'+const.ANNDIR[0:-1]+'.tbf'
    with open(parserNameOut, 'w') as ppo:
        for line in lines:
            m = re.match('^#BeginOfDocument (.*)$', line)
            c = re.match('^@Coreference\tR[0-9]+\t(.*)$', line)
            a = re.match('^@After\tR[0-9]+\t(E[0-9]+),(E[0-9]+)$', line)
            if m:
                ppo.write("%s\n" % line)
                if documents == {} and first == True:
                    key = m.group(1)
                    script = ev.Script(key)
                    first = False
                    list = []
                    cList = []
                    caList = []
                else:
                    documents[key] = list
                    key = m.group(1)
                    script = ev.Script(key)
                    list = []
                    cList = []
                    caList = []
            elif c:
                clusterGroup = c.group(1)
                clusterGroup = clusterGroup.split(',')
                cList.append(clusterGroup)
                ppo.write("%s\n" % line)
            elif a:
                skipPair = False
                event1 = script.getEventByEventId(a.group(1))
                event2 = script.getEventByEventId(a.group(2))
                eventsPairScript = createEventsPairScript(event1,event2)
                event1cg = getClusterGroup(cList, a.group(1))
                event2cg = getClusterGroup(cList, a.group(2))

                logging.debug("These are the cluster groups: %s %s", event1cg, event2cg)
                if event1cg != -1 and event2cg != -1:
                    logging.debug("Found a pair: %s %s, for the document %s", event1cg, event2cg, key)
                    logging.debug("This is the current list: %s", caList)
                    if(event1cg == event2cg):
                        skipPair = True
                    elif ((event1cg, event2cg) in caList):
                        skipPair = True
                    else:
                        skipPair = False
                        caList.append((event1cg, event2cg))
                        caList.append((event2cg, event1cg))

                if (event1cg == -1) ^ (event2cg == -1):
                    logging.debug("Found a pair: %s %s, for the document %s", event1cg, event2cg, key)
                    logging.debug("This is the current list: %s", caList)
                    if(event1cg == -1):
                        event1cg = a.group(1)
                    else:
                        event2cg = a.group(2)
                    if ((event1cg, event2cg) in caList):
                        skipPair = True
                    else:
                        skipPair = False
                        caList.append((event1cg, event2cg))
                        caList.append((event2cg, event1cg))

                if eventsPairScript in countersProbs:
                    if ((a.group(1), a.group(2)) not in list and (a.group(2), a.group(1)) not in list and skipPair == False):
                        ppo.write("%s\n" % line)
                        list.append((a.group(1), a.group(2)))
            else:
                ppo.write("%s\n" % line)






if __name__ == "__main__": main()
