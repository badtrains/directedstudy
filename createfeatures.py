from __future__ import division
import constants as c
import importarticle as ia
import gloveFeatures as gf
import statistics as stats
import logging
import pickle
import re
import numpy as np
import createdevset as cds
import operator
import os
import math
import sys
from random import randrange
import random
from collections import Counter
from collections import defaultdict
from operator import itemgetter
import itertools
from event import Script
from event import Event
import constants as const

#ANNDIR = 'LDC2015E73/'
#ANNDIR = 'LDC2017E08/'
ANNDIR = const.ANNDIR


FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)


def saveObj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

class CreateFeatures:
    def __init__(self, allarticles, setType):
        self.counts, self.probabilities = stats.computePairsProbabilities()
        #self.allarticles = ia.ArticlesImport('LDC2015E73/', setType)
        self.allarticles = allarticles
        self.stories = self.allarticles.getStoryArticles(setType)
        self.blogs = self.allarticles.getBlogArticles(setType)
        self.setType = setType
        if setType == 'train':
            self.filesStories, self.inputListStories, self.outputVectorStories, self.distanceFeature = self.getAllEventPairsAndOutputInStories()
            self.filesBlogs, self.inputListBlogs, self.outputVectorBlogs = self.getAllEventPairsAndOutputInBlogs()
        else:
            self.filesStories, self.inputListStories, self.outputVectorStories, self.distanceFeature = self.getAllEventPairsAndOutputInStoriesDev()
            self.filesBlogs, self.inputListBlogs, self.outputVectorBlogs = self.getAllEventPairsAndOutputInBlogsDev()

        self.files = self.filesStories + self.filesBlogs
        self.inputList = self.inputListStories + self.inputListBlogs
        self.filesList = self.filesStories + self.filesBlogs
        self.outputVector = self.outputVectorStories + self.outputVectorBlogs

        self.TypeSubtypeFeature = self.createEventPairsFeature(self.inputList)
        featureSet = self.TypeSubtypeFeature
        self.probabilityFeature = self.createSequenceProbabilityFeature()
        featureSet = self.stackFeature(featureSet, self.probabilityFeature, 'single')
        self.storyOrBlogFeature = [ 1 for x in range(len(self.inputListStories)) ] + [ 2 for x in range(len(self.inputListBlogs)) ]
        featureSet = self.stackFeature(featureSet, self.storyOrBlogFeature, 'single')
        featureSet = self.stackFeature(featureSet, self.distanceFeature, 'single')

        logging.info("Starting to create the embedding feature for the set: %s", setType)
        self.embeddingsFeature = self.createContextWordsFeature()
        featureSet = self.stackFeature(featureSet, self.embeddingsFeature.transpose(), 'array')
        logging.info("Done creating the embedding feature for the set: %s", setType)

#        embeddingFeature = np.vstack((self.embeddingFeatureLeftA, self.embeddingFeatureVectorA, self.embeddingFeatureRightA, self.embeddingFeatureLeftB, self.embeddingFeatureVectorB, self.embeddingFeatureRightB))

        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureLeftA, 'single')
        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureVectorA, 'single')
        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureRightA, 'single')
        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureLeftB, 'single')
        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureVectorB, 'single')
        # featureSet = self.stackFeature(featureSet, self.embeddingFeatureRightB, 'single')

        self.Y = self.stackFeature(None, self.outputVector, 'single')
        self.featureSet = featureSet


    def stackFeature(self, featureSet, feature, featureType):
        if featureType == 'single':
            if featureSet == None:
                stackedFeature = np.array([feature]).transpose()
            else:
                tempStackedFeature = np.array([feature]).transpose()
                stackedFeature = np.column_stack((featureSet, tempStackedFeature))
        if featureType == 'multiple':
            if featureSet == None:
                stackedFeature = np.array([np.array(xi) for xi in feature]).transpose()
            else:
                tempStackedFeature = np.array([np.array(xi) for xi in feature]).transpose()
                stackedFeature = np.column_stack((featureSet, tempStackedFeature))
        if featureType == 'array':
            if featureSet == None:
                stackedFeature = feature.transpose()
            else:
                tempStackedFeature = feature.transpose()
                stackedFeature = np.column_stack((featureSet, tempStackedFeature))
        return stackedFeature

    def createEventPairsFeature(self, inputList):
        """
        This feature returns the script/subscript type, it is going to be four columns
        :param inputList:
        :return:
        """
        ev1a = []
        ev1b = []
        ev2a = []
        ev2b = []
        for eventPair in inputList:
            # scriptForEventPair is something like '1-0e1-0' it says what is the relationship between the events
            # It shows the group-subgroup of the origin event and the one of the destination event.
            scriptForEventPair = self.createEventsPairScript(eventPair[0], eventPair[1])
            m = re.search('^([0-9]+)-([0-9]+)e([0-9]+)-([0-9]+)$', scriptForEventPair)
            if m:
                ev1a.append(m.group(1))
                ev1b.append(m.group(2))
                ev2a.append(m.group(3))
                ev2b.append(m.group(4))
        #ev1a, ev1b, ev2a, ev2b are lists of
        featureSet = self.stackFeature(None, ev1a, 'single')
        featureSet = self.stackFeature(featureSet, ev1b, 'single')
        featureSet = self.stackFeature(featureSet, ev2a, 'single')
        featureSet = self.stackFeature(featureSet, ev2b, 'single')
        return featureSet

    def createEventsPairScript(self, event1, event2):
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

    def getAllEventPairsAndOutputInStories(self):
        """
        In a story the events are not divided into scripts kind of units, therefore at the moments we are only dealing with all the events altogether. So if there are n events in a story type of article, we need to pull all of them, and there will therefore be n(n-1) links, because we need to keep in mind also the direction of the event.
        :return:
        """
        stories = self.stories
        i = 0
        j = 0
        outputVector = []
        filesList = []
        inputList = []
        distanceFeature = []
        for story in stories:
            # if story.script.scriptName == "NYT_ENG_20130816.0069":
            #     logging.info("Here We are")
            eventsList = story.articleEventsList
            eventsPairs = list(itertools.combinations(eventsList, 2))
            positiveEventsPairs = self.getPositiveExamplesList(story)
            for eventPair in eventsPairs:
                eventPairFlip = (eventPair[1], eventPair[0])
                if list(eventPair) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    filesList.append(story.script.scriptName)
                    inputList.append(list(eventPair))
                    # Distance is the distance between sentences so if the events are in the same sentence, then their distance is equal to 1
                    distanceFeature.append(story.getDistanceBetweenEvents(eventPair[0], eventPair[1]))
                    i = i + 1
                    logging.debug("Adding a positive example. Value of i: %d, value of pair: %s" % (i, eventPair))
                else:
                    distance = story.getDistanceBetweenEvents(eventPair[1], eventPair[0])
                    # I am limiting the number of negative examples to 50 so that we don't get a crazy training set
                    # This is just temporary for now. Also I am only taking negative examples for events within the same sentence: abs(distance) < 1.
                    if abs(distance) < 1 and (i-j) < 50:
                        logging.debug("This is i: %d:", i)
                        filesList.append(story.script.scriptName)
                        inputList.append(list(eventPair))
                        outputVector.append(0)
                        i = i + 1
                        logging.debug("Adding a negative example. Value of i: %d, value of pair: %s" % (i, eventPair))
                        distanceFeature.append(0)
                if list(eventPairFlip) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    inputList.append(list(eventPair))
                    filesList.append(story.script.scriptName)
                    distanceFeature.append(story.getDistanceBetweenEvents(eventPairFlip[1], eventPairFlip[0]))
                    i = i + 1
                    logging.debug("Adding a positive example. Value of i: %d, value of pair: %s" % (i, eventPair))
                else:
                    distance = story.getDistanceBetweenEvents(eventPairFlip[1], eventPairFlip[0])
                    if abs(distance) < 1 and (i-j) < 50:
                        logging.debug("This is i: %d:", i)
                        inputList.append(list(eventPairFlip))
                        filesList.append(story.script.scriptName)
                        outputVector.append(0)
                        distanceFeature.append(0)
                        i = i + 1
                        logging.debug("Adding a negative example. Value of i: %d, value of pair: %s" % (i, eventPair))
            logging.info("This is the number of event pairs in this file %s: %d" % (story.script.scriptName,(len(eventsPairs))  ))
            logging.info("Added %d examples for file %s in the training set" % ((i-j), story.script.scriptName))
            j = i
        return filesList, inputList, outputVector, distanceFeature

    def getAllEventPairsAndOutputInStoriesDev(self):
        """
        In a story the events are not divided into scripts kind of units, therefore at the moment we are only dealing with all the events altogether. So if there are n events in a story type of article, we need to pull all of them, and there will therefore be n(n-1) links, because we need to keep in mind also the direction of the event.
        I am now limiting the number of event pairs to a distance of 3
        :return:
        """
        # the devSet will decide which are the stories files to present
        MINDISTANCE=2
        stories = self.stories
        i = 0
        outputVector = []
        inputList = []
        filesList = []
        distanceFeature = []
        tot = 0
        for story in stories:
            i = 0
            # I will do more of this if I have time.
            # corefTagsPairList = story.script.getListOfCoreferenceLinks()
            # orderedCorefClusters = story.script.createEventsClusters(corefTagsPairList)
            # cClusters = []
            # for cluster in orderedCorefClusters:
            #     evList = []
            #     cluster = cluster[0]
            #     for evP in cluster:
            #         evList.append(evP[0])
            #     evList.append(cluster[-1][1])
            # cClusters.append(evList)


            eventsList = story.articleEventsList
            logging.info("There are %d events in story %s", len(eventsList), story.script.scriptName)
            tot = tot + len(eventsList)*(len(eventsList)-1)
            logging.debug("Total Events: %d", tot)
            eventsPairs = list(itertools.combinations(eventsList, 2))
            positiveEventsPairs = self.getPositiveExamplesList(story)
            for eventPair in eventsPairs:
                eventPairFlip = (eventPair[1], eventPair[0])
                if list(eventPair) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    inputList.append(list(eventPair))
                    filesList.append(story.script.scriptName)
                    distanceFeature.append(story.getDistanceBetweenEvents(eventPair[0], eventPair[1]))
                    i = i + 1
                else:
                    distance = story.getDistanceBetweenEvents(eventPair[1], eventPair[0])
                    if abs(distance) < MINDISTANCE+1:
                        logging.debug("This is i: %d:", i)
                        inputList.append(list(eventPair))
                        filesList.append(story.script.scriptName)
                        outputVector.append(0)
                        i = i + 1
                        distanceFeature.append(distance)
                if list(eventPairFlip) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    inputList.append(list(eventPair))
                    filesList.append(story.script.scriptName)
                    distanceFeature.append(story.getDistanceBetweenEvents(eventPairFlip[1], eventPairFlip[0]))
                    i = i + 1
                else:
                    distance = story.getDistanceBetweenEvents(eventPairFlip[1], eventPairFlip[0])
                    if abs(distance) < 2:
                        logging.debug("This is i: %d:", i)
                        inputList.append(list(eventPairFlip))
                        filesList.append(story.script.scriptName)
                        outputVector.append(0)
                        distanceFeature.append(distance)
                        i = i + 1
            logging.info("Added %d examples for file %s in the stories dev set" % (i, story.script.scriptName))
        return filesList, inputList, outputVector, distanceFeature

    def getAllEventPairsAndOutputInBlogs(self):
        """
        In a blog the events are divided into units, therefore we only take events that are confined inside one of those units when computing the features.
        For the time being we are considering only positive examples in blogs, for the training part
        :return:
        """
        blogs = self.blogs
        i = 0
        outputVector = []
        inputList = []
        filesList = []
        for blog in blogs:
            positiveEventsPairs = self.getPositiveExamplesList(blog)
            for eventPair in positiveEventsPairs:
                outputVector.append(1)
                inputList.append(list(eventPair))
                filesList.append(blog.script.scriptName)
                self.distanceFeature.append(0)
        return filesList, inputList, outputVector

    def getAllEventPairsAndOutputInBlogsDev(self):
        """
        In a blog the events are divided into units, therefore we only take events that are confined inside one of those units when computing the features.
        :return:
        """
        blogs = self.blogs
        i = 0
        outputVector = []
        inputList = []
        filesList = []
        tot = 0
        for blog in blogs:
            i = 0
            article = ia.Article(blog.script.scriptName + '.txt', ANNDIR)
            eventsList = blog.articleEventsList
            eventsPairs = list(itertools.combinations(eventsList, 2))
            positiveEventsPairs = self.getPositiveExamplesList(blog)
            logging.info("There are %d events in blog %s", len(eventsList), blog.script.scriptName)
            tot = tot + len(eventsList)*(len(eventsList)-1)
            logging.debug("Total Events: %d", tot)

            for eventPair in eventsPairs:
                eventPairFlip = (eventPair[1], eventPair[0])
                if list(eventPair) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    inputList.append(list(eventPair))
                    filesList.append(blog.script.scriptName)
                    self.distanceFeature.append(0)
                    i = i + 1
                else:
                    logging.debug("This is i: %d:", i)
                    eventA = eventPair[0]
                    eventB = eventPair[1]
                    postA = article.getPostIdentifierForBlogsFromEvents(eventA)
                    postB = article.getPostIdentifierForBlogsFromEvents(eventB)
                    if postA == postB:
                        logging.debug("Adding the link in the blog for this event pair")
                        inputList.append(list(eventPair))
                        filesList.append(blog.script.scriptName)
                        outputVector.append(0)
                        i = i + 1
                        self.distanceFeature.append(0)
                    else:
                        logging.debug("Not adding the link in the blog for this event pair")
                if list(eventPairFlip) in positiveEventsPairs:
                    logging.debug("This is i: %d:", i)
                    outputVector.append(1)
                    inputList.append(list(eventPair))
                    filesList.append(blog.script.scriptName)
                    self.distanceFeature.append(0)
                    i = i + 1
                else:
                    logging.debug("This is i: %d:", i)
                    eventA = eventPairFlip[0]
                    eventB = eventPairFlip[1]
                    postA = article.getPostIdentifierForBlogsFromEvents(eventA)
                    postB = article.getPostIdentifierForBlogsFromEvents(eventB)
                    if postA == postB:
                        logging.debug("Adding the link in the blog for this event pair")
                        inputList.append(list(eventPairFlip))
                        filesList.append(blog.script.scriptName)
                        outputVector.append(0)
                        self.distanceFeature.append(0)
                        i = i + 1
                    else:
                        logging.debug("Not adding the link in the blog for this event pair")
            logging.info("Added %d examples in blog %s", i, blog.script.scriptName)
        return filesList, inputList, outputVector

    def createContextWordsFeature(self):
        """
        This creates a matrix with 600 colums and as many rows as there are event pairs in the set
        :return: 
        """
        contextFeature = None
        totalPairs = len(self.inputList)
        iPair = 0
        logging.info("There are %d event pairs to examine in set %s", totalPairs, self.setType)
        done = False
        completion = 0
        for eventsPair in self.inputList:
            iPair += 1
            total = (iPair/float(totalPairs))*100
            if completion != int(total):
                done = False
            if (int(math.floor(total)%5) == 0 and int(total) > 0 and done == False):
                completion = int(total)
                done = True
                logging.info("Total Completion: %d%% for set: %s", int(total), self.setType)

            idx = self.inputList.index(eventsPair)
            eventsFile = self.filesList[idx]
            eventsArticle = gf.getArticleObject(eventsFile)
            eventA = eventsPair[0]
            eventB = eventsPair[1]
            leftWordsListA, rightWordsListA, eventWordA = eventsArticle.getNeighboringWords(eventA)
            leftWordsListB, rightWordsListB, eventWordB = eventsArticle.getNeighboringWords(eventB)

            leftWordsListEmbA = gf.computeGloveFeature(leftWordsListA)
            wordsListVectorEmbA = gf.computeGloveFeature([eventWordA])
            rightWordsListEmbA = gf.computeGloveFeature(rightWordsListA)
            leftWordsListEmbB = gf.computeGloveFeature(leftWordsListA)
            wordsListVectorEmbB = gf.computeGloveFeature([eventWordB])
            rightWordsListEmbB = gf.computeGloveFeature(rightWordsListA)
            feature = []
            feature = np.append(feature,leftWordsListEmbA)
            feature = np.append(feature, wordsListVectorEmbA)
            feature = np.append(feature, rightWordsListEmbA)
            feature = np.append(feature, leftWordsListEmbB)
            feature = np.append(feature, wordsListVectorEmbB)
            feature = np.append(feature, rightWordsListEmbB)

            if contextFeature == None:
                contextFeature = feature
            else:
                contextFeature = np.vstack((contextFeature, feature))
        return contextFeature

    def createSequenceProbabilityFeature(self):
        probabilityFeature = []
        for eventsPair in self.inputList:
            script = self.createEventsPairScript(eventsPair[0], eventsPair[1])
            if script in self.probabilities.keys():
                probabilityFeature.append(self.probabilities[script])
            else:
                probabilityFeature.append(0)
        return probabilityFeature

    def getPositiveExamplesList(self, story):
        positiveExamplesPairs = []
        eventClusters = story.script.eventsClusters
        for oel in eventClusters:
            eventList = oel[0]
            for ev in eventList:
                event1 = story.script.getEventByEventId(ev[0])
                event2 = story.script.getEventByEventId(ev[1])
                eventPair = [ event1, event2]
                positiveExamplesPairs.append(eventPair)
        return positiveExamplesPairs

    # def getPositiveExamplesList(story):
    #     eventClusters = story.script.eventsClusters
    #     for oel in eventClusters:
    #         eventList = oel[0]
    #         for ev in eventList:
    #             eventsPair = []
    #             eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = story.script.getEventDetailsByEventId(ev[0])
    #             logging.debug("Events: %s, %s", eventType, eventSubtype)
    #             eventTypeNumber = c.EVENTTYPES[eventType]
    #             eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype)
    #             eventPairString1 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    #             eventType, eventSubtype, eventTextRef, textValue, realisType, realisValue = story.script.getEventDetailsByEventId(ev[1])
    #             logging.debug("Events: %s, %s", eventType, eventSubtype)
    #             eventTypeNumber = c.EVENTTYPES[eventType]
    #             eventSubTypeNumber = c.EVENTSUBTYPES[eventTypeNumber].index(eventSubtype)
    #             eventPairString2 = str(eventTypeNumber) + '-' + str(eventSubTypeNumber)
    #             eventPairString = eventPairString1 + 'e' + eventPairString2

def main():
    # allarticles = ia.ArticlesImport('LDC2015E73/')
    allarticles = ia.ArticlesImport(ANNDIR)

    # setType = 'train'
    # features = CreateFeatures(allarticles, setType)
    # saveObj(features.featureSet, 'XTrain')
    # saveObj(features.Y, 'YTrain')

    setType = 'dev'
    features = CreateFeatures(allarticles, setType)
    # for each of the event pairs it contain the file to which it belongs to
    saveObj(features.filesStories, 'filenamesstories')
    # for each of the event pairs it contain the file to which it belongs to
    saveObj(features.filesBlogs, 'filenamesblogs')
    # stories and blogs are just the article objects, nothing to so with features, it's a wrong file name
    saveObj(features.stories, 'devstoriesfeatures')
    saveObj(features.blogs, 'devblogsfeatures')
    # Input list contains the list of event pairs in the stories one by one, same for the blogs
    saveObj(features.inputListStories, 'inputliststories')
    saveObj(features.inputListBlogs, 'inputlistsblogs')
    # These are the real features and the corresponding value of the output
    saveObj(features.featureSet, 'XDev')
    saveObj(features.Y, 'YDev')

    logging.info("Finished Creating the features")

if __name__ == "__main__": main()
