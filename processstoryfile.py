import os
import numpy
import re
import copy
import itertools
import logging
import statistics as stats
import event
import constants as c
from collections import Counter
import importarticle as ia
from itertools import cycle, islice, dropwhile
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

#ANNDIR = 'LDC2015E73'
ANNDIR = 'LDC2017E08'
mypath = ANNDIR

from os import listdir
from os.path import isfile, join


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

    eventTypeNumber = c.EVENTTYPES[eventType1]
    eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype1)
    eventPairString1 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    logging.debug("Events: %s, %s", eventType2, eventSubtype2)
    eventTypeNumber = c.EVENTTYPES[eventType2]
    eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype2)
    eventPairString2 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    eventPairString = eventPairString1 + 'e' + eventPairString2
    return eventPairString


def getPositiveExamplesList(story):
    positiveExamplesPairs = []
    eventClusters = story.script.eventsClusters
    for oel in eventClusters:
        eventList = oel[0]
        for ev in eventList:
            event1 = story.script.getEventByEventId(ev[0])
            event2 = story.script.getEventByEventId(ev[1])
            eventPair = [event1, event2]
            positiveExamplesPairs.append(eventPair)
    return positiveExamplesPairs

def getAllEventPairsInStory(story):
    """
    :return:
    """
    outputVector = []
    inputList = []
    distanceFeature = []
    tot = 0
    eventsList = story.articleEventsList
    logging.info("There are %d events in story %s", len(eventsList), story.script.scriptName)
    tot = tot + len(eventsList) * (len(eventsList) - 1)
    logging.debug("Total Events: %d", tot)
    eventsPairs = list(itertools.combinations(eventsList, 2))
    for eventPair in eventsPairs:
        eventPairFlip = (eventPair[1], eventPair[0])
        inputList.append(list(eventPair))
        inputList.append(list(eventPairFlip))
    return inputList


def main():
    allarticles = ia.ArticlesImport('LDC2015E73/')
    stories = allarticles.getStoryArticles('dev')
    counts, probabilities = stats.computePairsProbabilities()
    stories = [stories[0]]
    eventsToCluster = []
    for story in stories:
        print(story.script.scriptName)
        allEventPairs = getAllEventPairsInStory(story)
        for eventPair in allEventPairs:
            distance = story.getDistanceBetweenEvents(eventPair[1], eventPair[0])
            if distance < 1:
                scriptText = createEventsPairScript(eventPair[0], eventPair[1])
                if scriptText in counts.keys():
                    pair = [[[eventPair[0].eventTag, eventPair[1].eventTag], ], 0]
                    eventsToCluster.append(pair)
                    print("I found one: %s %s, counts: %d" % (eventPair[0].eventTag, eventPair[1].eventTag, counts[scriptText]))
                else:
                    print("Skipping: %s %s" % (eventPair[0].eventTag, eventPair[1].eventTag), counts[scriptText])
    clusters = stats.createEventsClusters(eventsToCluster)
    afterLinks = stats.getListOfAfterLinks(story.script)
    goodClusters = stats.createEventsClusters(afterLinks)
    print(1)

if __name__ == "__main__": main()