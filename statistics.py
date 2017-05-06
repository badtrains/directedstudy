import os
import numpy
import re
import copy
import logging
import event
import constants as c
from collections import Counter
import importarticle as ia
from itertools import cycle, islice, dropwhile
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

#ANNDIR = 'LDC2015E73/'
#ANNDIR = 'LDC2017E08/'
ANNDIR = c.ANNDIR

mypath = ANNDIR


from os import listdir
from os.path import isfile, join


def checkEventAttach(eventsTagsPairList, event):
    # first zero is the list itself, the second zero is the first list and the third zero is the first element
    # [ [[a,b], [c,d], ..., [w,z] ] , 0]
    matchA = event[0][0][0] # this selects a
    matchB = event[0][-1][1] # this selects z
    n = len(eventsTagsPairList)
    for i in range(n):
        if eventsTagsPairList[i][1] == 0:
            # first element in the list
            matchEA = eventsTagsPairList[i][0][0][0]
            # last element in the list
            matchEB = eventsTagsPairList[i][0][-1][1]
            if matchEA == matchB:
                logging.debug("There is a match; A: %s, B: %s", matchEA, matchB)
                newEvent = [event[0]+eventsTagsPairList[i][0],0]
                eventsTagsPairList[i][1] = 1
                return newEvent, 1
            if matchEB == matchA:
                logging.debug("There is a match; A: %s, B: %s", matchA, matchEB)
                newEvent = [eventsTagsPairList[i][0]+event[0], 0]
                eventsTagsPairList[i][1] = 1
                return newEvent, 1
    eventToReturn = copy.copy(event)
    eventToReturn[1] = 0
    return eventToReturn, 0

def checkListEmpty(eventsTagsPairList, newList):
    for e in eventsTagsPairList:
        if e[1] == 0:
            return 0
    return 1

def createEventsClusters(eventsTagsPairList):
    newList = []
    n = len(eventsTagsPairList)
    doMore = 0
    for i in range(n):
        logging.debug("These are the events: %s", eventsTagsPairList[i])
        # This is the last element of the list to whom we want to attach
        if eventsTagsPairList[i][1] == 0:
            eventsTagsPairList[i][1] = 1
            newEvent, flag = checkEventAttach(eventsTagsPairList, eventsTagsPairList[i])
            newList.append(newEvent)
            if flag == 1:
                doMore = 1
    if doMore == 0:
        listToPass = copy.deepcopy(newList)
        return listToPass
    else:
        newList = createEventsClusters(newList)
        return newList

def getListOfAfterLinks(script):
    eventsTagsPairList = []
    eventLinksList = script.referenceObjList
    for eventLink in eventLinksList:
        if eventLink.linkType == 'After':
            pair = [ [[eventLink.linkArg1, eventLink.linkArg2],], 0]
            eventsTagsPairList.append(pair)
    return eventsTagsPairList
#    self.linkTag, self.linkType, self.linkArg1, self.linkArg2

def getExpandedListOfAfterLinks(script):
    """
    This returns the global list of after links, including the expanded coreferences
    :param script: 
    :return: 
    """
    eventsTagsPairList = getListOfAfterLinks(script)
    newLinks = getListOfExtraAfterLinks(script)
    eventsTagsPairList = eventsTagsPairList + newLinks
    return eventsTagsPairList

def getListOfCoreferenceLinks(script):
    """
    Gets the list of coreference lings from the script
    :param script: 
    :return: 
    """
    eventsTagsPairList = []
    eventLinksList = script.referenceObjList
    for eventLink in eventLinksList:
        if eventLink.linkType == 'Coreference':
            pair = [ [[eventLink.linkArg1, eventLink.linkArg2],], 0]
            eventsTagsPairList.append(pair)
    return eventsTagsPairList


def checkIfCorefInListF(corefLinks, eventTag):
    returnPar = None
    for link in corefLinks:
        link0Cor = link[0][0][0]
        link1Cor = link[0][0][1]
        if link0Cor == eventTag:
            returnPar = link1Cor
    return returnPar

def checkIfCorefInListB(corefLinks, eventTag):
    returnPar = None
    for link in corefLinks:
        link0Cor = link[0][0][0]
        link1Cor = link[0][0][1]
        if link1Cor == eventTag:
            returnPar = link0Cor
    return returnPar

def checkExtraAfterFromCorefF(corefLinks, afterLink):
    """
    Checks that there are coreference links mapping after links forward for instance:
    R1      Coreference Arg1:E51 Arg2:E38
    R2      Coreference Arg1:E38 Arg2:E64
    R3      Coreference Arg1:E90 Arg2:E77
    R4      Coreference Arg1:E77 Arg2:E103
    R5      Coreference Arg1:E129 Arg2:E116
    R6      Coreference Arg1:E142 Arg2:E155
    R7      Coreference Arg1:E298 Arg2:E324
    R8      Coreference Arg1:E324 Arg2:E311
    R9      After Arg1:E207 Arg2:E220
    R10     After Arg1:E38 Arg2:E77
    Detects E64 - E103
    :param corefLinks: 
    :param afterLink: 
    :return: 
    """
    link0 = afterLink[0][0][0]
    link1 = afterLink[0][0][1]
    returnList = []
    corLink0 = checkIfCorefInListF(corefLinks, link0)
    if corLink0 != None:
        corLink1 = checkIfCorefInListF(corefLinks, link1)
        if corLink1 != None:
            newAfterLink = [[[corLink0, corLink1]], 0]
            returnList.append(newAfterLink)
            partialReturn = checkExtraAfterFromCorefF(corefLinks, newAfterLink)
            returnList = returnList + partialReturn
    return returnList

def checkExtraAfterFromCorefB(corefLinks, afterLink):
    """
    Checks that there are coreference links mapping after links forward for instance:
    R1      Coreference Arg1:E51 Arg2:E38
    R2      Coreference Arg1:E38 Arg2:E64
    R3      Coreference Arg1:E90 Arg2:E77
    R4      Coreference Arg1:E77 Arg2:E103
    R5      Coreference Arg1:E129 Arg2:E116
    R6      Coreference Arg1:E142 Arg2:E155
    R7      Coreference Arg1:E298 Arg2:E324
    R8      Coreference Arg1:E324 Arg2:E311
    R9      After Arg1:E207 Arg2:E220
    R10     After Arg1:E38 Arg2:E77
    Detects E51 - E77

    :param corefLinks: 
    :param afterLink: 
    :return: 
    """

    link0 = afterLink[0][0][0]
    link1 = afterLink[0][0][1]
    returnList = []
    corLink0 = checkIfCorefInListB(corefLinks, link0)
    if corLink0 != None:
        corLink1 = checkIfCorefInListB(corefLinks, link1)
        if corLink1 != None:
            newAfterLink = [[[corLink0, corLink1]], 0]
            returnList.append(newAfterLink)
            partialReturn = checkExtraAfterFromCorefB(corefLinks, newAfterLink)
            returnList = returnList + partialReturn
    return returnList

def getListOfExtraAfterLinks(script):
    afterLinks = getListOfAfterLinks(script)
    corefLinks = getListOfCoreferenceLinks(script)
    newAfterLinks = []
    for afterLink in afterLinks:
        newLinksF = checkExtraAfterFromCorefF(corefLinks, afterLink)
        newLinksB = checkExtraAfterFromCorefB(corefLinks, afterLink)
        newLinks = newLinksF+newLinksB
        newAfterLinks = newAfterLinks+newLinks
    newAfterLinks = afterLinks+newAfterLinks
    return newAfterLinks

def getAverageStoryEventPairsDistance():
    allarticles = ia.ArticlesImport('LDC2015E73/')
    stories = allarticles.getStoryArticles('train')
    distances = []
    for story in stories:
        eventsClusters = story.script.eventsClusters
        for cluster in eventsClusters:
            for eventPair in cluster[0]:
                ev1 = story.script.getEventByEventId(eventPair[0])
                ev2 = story.script.getEventByEventId(eventPair[1])
                distance = story.getDistanceBetweenEvents(ev1, ev2)
                distances.append(abs(distance))
    return distances


def getCoreferenceLinks():
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    i = 0
    for file in onlyfiles:
        fileNoExtension = os.path.splitext(file)[0]
        logging.debug("This is the file I am processing: %s" % fileNoExtension)
        if os.path.splitext(file)[1]:
            script = event.Script(fileNoExtension)
            # <type 'list'>: [[[['E225', 'E459']], 0], [[['E446', 'E407']], 0]]
            eventsTagsPairList = getListOfAfterLinks(script)
            coreferenceLinks = script.getListOfCoreferenceClusters()
            logging.debug("This is the list of unordered events: %s", eventsTagsPairList)
            for eventPair in eventsTagsPairList:
                i = i+1
                logging.info("Event1: %d %s", i, eventPair[0][0][0])
                logging.info("Event2: %d %s", i, eventPair[0][0][1])
    return 1


def computeOrderedSequenceList():
    """
    This procedure returns a list of ordered events
    :return:
    """
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for file in onlyfiles:
        fileNoExtension = os.path.splitext(file)[0]
        logging.debug("This is the file I am processing: %s" % fileNoExtension)
        if os.path.splitext(file)[1]:
            script = event.Script(fileNoExtension)
            eventsTagsPairList = getListOfAfterLinks(script)
            logging.debug("This is the list of unordered events: %s", eventsTagsPairList)
            orderedEventsLists = createEventsClusters(eventsTagsPairList)
            logging.debug("This is the list of ordered events: %s", orderedEventsLists)
    return orderedEventsLists

def computePairsProbabilities():
    """
    This procedure takes all the events with after links from a newsarticle file. It then creates the ordered events clusters (pairs of events), and then it computes the statistics on the events type-subtype for instance:
    7-3e7-0 means type 7-subtype 4 goes to type 7-subtype 0 (as per the constants file).
    It turns out that there are only 133 pairs of possible events with after links in the whole corpus.
    :return:
    """
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    allGoodEventPairs = []
    for file in onlyfiles:
        fileNoExtension = os.path.splitext(file)[0]
        logging.debug("This is the file I am processing: %s" % fileNoExtension)
        if os.path.splitext(file)[1]:
            script = event.Script(fileNoExtension)
            eventsTagsPairList = getListOfExtraAfterLinks(script)
            logging.debug("This is the list of unordered events: %s", eventsTagsPairList)
            orderedEventsLists = createEventsClusters(eventsTagsPairList)
            logging.debug("This is the list of ordered events: %s", orderedEventsLists)
            for oel in orderedEventsLists:
                eventList = oel[0]
                n = 1
                for ev in eventList:
                    eventsPair = []
                    try:
                        eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = script.getEventDetailsByEventId(ev[0])
                    except:
                        logging.info('Scramble issue with %s', script.scriptName)
                    logging.debug("Events: %s, %s", eventType, eventSubtype)
                    eventTypeNumber = c.EVENTTYPES[eventType]
                    eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype)
                    eventPairString1 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
                    try:
                        eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = script.getEventDetailsByEventId(ev[1])
                    except:
                        logging.info('Scramble issue with %s', script.scriptName)
                    logging.debug("Events: %s, %s", eventType, eventSubtype)
                    eventTypeNumber = c.EVENTTYPES[eventType]
                    eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype)
                    eventPairString2 = str(eventTypeNumber)+'-'+str(eventSubTypeNumber)
                    eventPairString = eventPairString1+'e'+eventPairString2
                    allGoodEventPairs.append(eventPairString)
    counts = Counter(allGoodEventPairs)
    keys = counts.keys()
    numberOfEvents = len(allGoodEventPairs)
    probabilities = {}
    for key in keys:
        probabilities[key] = counts[key]/float(numberOfEvents)
    return counts, probabilities


def computeEventPairProbability(event1, event2):
    orderedEventsLists = computeOrderedSequenceList()
    pass

def main():
    scriptsDatabase = []
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for file in onlyfiles:
        fileNoExtension = os.path.splitext(file)[0]
        # fileNoExtension = 'bolt-eng-DF-170-181125-9125545'
        # file = 'bolt-eng-DF-170-181125-9125545.ann'
        logging.debug("This is the file I am processing: %s" % fileNoExtension)
        if os.path.splitext(file)[1] == '.ann':
            script = event.Script(fileNoExtension)
            eventsTagsPairList = getListOfAfterLinks(script)
            newLinks = getListOfExtraAfterLinks(script)
            eventsTagsPairList = eventsTagsPairList + newLinks
            logging.debug("This is the list of unordered events: %s", eventsTagsPairList)
            orderedEventsLists = createEventsClusters(eventsTagsPairList)
            logging.debug("This is the list of ordered events: %s", orderedEventsLists)
            for oel in orderedEventsLists:
                eventList = oel[0]
                eventsSequenceList = []
                n = 1
                for ev in eventList:
                    eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = script.getEventDetailsByEventId(ev[0])
                    eventsSequenceList.append(eventType + '-' + eventSubtype)
                eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = script.getEventDetailsByEventId(ev[1])
                eventsSequenceList.append(eventType + '-' + eventSubtype)
                scriptsDatabase.append([script.scriptName, eventsSequenceList])
    scripts = ['#'.join(x[1]) for x in scriptsDatabase]

    counts = Counter(scripts)
    print(counts)

    # logging.debug("This is the total number of files %d", len(onlyfiles))
    #
    script = event.Script('bolt-eng-DF-170-181125-9125545')
    eventsTagsPairList = getListOfAfterLinks(script)
    #
    orderedEventsLists = createEventsClusters(eventsTagsPairList)
    print(orderedEventsLists)

    distances = getAverageStoryEventPairsDistance()
    print(distances)
    print(numpy.mean(distances))
    oel = computeOrderedSequenceList()
    probabilities = computePairsProbabilities()

    coreferences = getCoreferenceLinks()
    print(1)
if __name__ == "__main__": main()