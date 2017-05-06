from __future__ import division
import copy
import os
import re
import pickle
import numpy as np
import time
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn import datasets, metrics
from sklearn import linear_model
from sklearn import svm

import constants as c
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

def getListOfCorefLinks(script):
    eventsTagsPairList = []
    eventLinksList = script.referenceObjList
    for eventLink in eventLinksList:
        if eventLink.linkType == 'Coreference':
            pair = [ [[eventLink.linkArg1, eventLink.linkArg2],], 0]
            eventsTagsPairList.append(pair)
    return eventsTagsPairList

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


def getTextStartStop(textStamp):
    m = re.search('^([0-9]+) ([0-9]+)$', textStamp)
    n = re.search('^([0-9]+) ([0-9]+);([0-9]+) ([0-9]+)$', textStamp)
    if m:
        textStart = m.group(1)
        textStop = m.group(2)
    elif n:
        textStart = n.group(1)
        textStop = n.group(4)
    else:
        logging.info("There was a problem with this string: %s", textStamp)
    return textStart, textStop

def adaBoostClassifier(X, Y, devX, devLabels):
    bdt = AdaBoostClassifier(svm.SVC(probability=True, kernel='linear'), n_estimators=50, learning_rate=.1, algorithm='SAMME')
    bdt.fit(X, Y)
    print("fitted")
    saveObj(bdt, 'adaBoostTrained-1.model')
    #predicted = bdt.predict(devX)
    #print(predicted)
    #accuracy = accuracy_score(devLabels, predicted)
    #print("Accuracy AdaBoost Classifier: %f" % accuracy)
    #print(bdt.predict_log_proba(X))
    #print(bdt.predict_proba(devX))
    return bdt


def logisticRegression(X, Y, devX, devLabels):
    logreg = linear_model.LogisticRegression(C=1e5)
    logreg.fit(X, Y)
    logreg_predictions = logreg.predict(devX)
    accuracy = accuracy_score(devLabels, logreg_predictions)
    saveObj(logreg, 'logRegTrained955.model')
    probabilities = logreg.predict_proba(devX)
    print("Accuracy LogReg Classifier: %f" % accuracy)
    return logreg_predictions, probabilities

def unique_rows(a):
    a = np.ascontiguousarray(a)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))

def main():
    X = loadObj('XTrain')
    Y = loadObj('YTrain')
    devX = loadObj('XDev')
    devLabels = loadObj('YDev')
    parserName = 'parseroutput-'+c.ANNDIR[0:-1]+'.tbf'

    fparser = open(parserName, 'w')
    #
    # start = time.time()
    # bdt = adaBoostClassifier(X, Y, devX, devLabels)
    # end = time.time()
    # logging.info("This is the time needed to fit the model: %s", (end - start))




    # This is loading the stories and the blogs
    stories = loadObj('devstoriesfeatures')
    blogs = loadObj('devblogsfeatures')

    # This is the list of the event pairs for stories and for blogs
    inputStories = loadObj('inputliststories')
    inputBlogs = loadObj('inputlistsblogs')
    inputList = inputStories + inputBlogs
    filesListStories = loadObj('filenamesstories')
    filesListBlogs = loadObj('filenamesblogs')

    bdt = loadObj('adaBoostTrained-1.model')
    start = time.time()
    predicted = bdt.predict(devX)
    end = time.time()
    logging.info("This is the time needed to predict: %s", (end - start))

    #accuracy = accuracy_score(devLabels, predicted)
    #print("Accuracy AdaBoost Classifier: %f" % accuracy)

    saveObj(predicted, 'predicteddevX')
    predicted = loadObj('predicteddevX')

    ini = 0
    fin = 0
    i = 0
    for story in stories:
        storyName = story.script.scriptName
        fparser.write('#BeginOfDocument %s\n' % storyName)
#        length = story.getGlobalNumberOfEventsPairs()
        length = filesListStories.count(storyName)
        fin = fin + length
        predictedS = predicted[ini:fin]
#        labels = devLabels[ini:fin]
        i = 0
        gotit = 0
        eventsStore = []
        for label in predictedS:
            if label == 1:
                # if predictedS[i] == label:
                #     print(story.script.scriptName)
                # print("Got one")
                # gotit = gotit+1
                eventsStore.append(inputList[ini+i])
                # event1 = eventPair[0]
                # event2 = eventPair[1]
          #      self.eventTag, self.eventType, self.eventSubtype, self.eventTextRef = self.parseEventLine(lines[1])
            i = i + 1
        #print(predictedS)
        #print(labels)
        ini = fin + 1
        eventsMentions = story.script.eventsList
        #coreferenceLinks = story.script.referenceObjList
        corefTagsPairList = getListOfCorefLinks(story.script)
        orderedCorefClusters = createEventsClusters(corefTagsPairList)
        """
        [[[['E37', 'E24'], ['E24', 'E50'], ['E50', 'E210'], ['E210', 'E63']], 0], [[['E89', 'E76']], 0], [[['E283', 'E298']], 0]]
        """
        for event in eventsMentions:
            textStart, textStop = getTextStartStop(event.textStartStop)
            fparser.write('system1\t%s\t%s\t%s,%s\t%s\t%s_%s\t%s\t1 1 1\n' % (story.script.scriptName, event.eventTag, textStart, textStop, event.textValue, event.eventType, event.eventSubtype, event.realisValue))

        for cluster in orderedCorefClusters:
            string = ""
            cluster = cluster[0]
            j = 0
            for evP in cluster:
                if j == 0:
                    string = evP[0]
                else:
                    string = string+','+evP[0]
                j = j +1
            string = string+','+cluster[-1][1]
            gotit = gotit + 1
            fparser.write('@Coreference\tR%d\t%s\n' % (gotit, string))

        for eventPair in eventsStore:
            gotit = gotit + 1
            event1 = eventPair[0]
            event2 = eventPair[1]
            fparser.write('@After\tR%d\t%s,%s\n' % (gotit, event1.eventTag, event2.eventTag))
        fparser.write('#EndOfDocument\n')

    for blog in blogs:
        blogName = blog.script.scriptName
        fparser.write('#BeginOfDocument %s\n' % blogName)
        #        length = blog.getGlobalNumberOfEventsPairs()
        length = filesListBlogs.count(blogName)

        fin = fin + length
        predictedS = predicted[ini:fin]
#        labels = devLabels[ini:fin]
        i = 0
        gotit = 0
        eventsStore = []
        for label in predictedS:
            if label == 1:
                # print("got one")
                # if predictedS[i] == label:
                #     print(blog.script.scriptName)
                #     print("Got one")
                eventsStore.append(inputList[ini+i])
                # eventPair = inputList[ini + i]
                # event1 = eventPair[0]
                # event2 = eventPair[1]
                #      self.eventTag, self.eventType, self.eventSubtype, self.eventTextRef = self.parseEventLine(lines[1])
            i = i + 1
        #print(predictedS)
        #print(labels)
        ini = fin + 1
        eventsMentions = blog.script.eventsList
#        coreferenceLinks = blog.script.referenceObjList
        corefTagsPairList = getListOfCorefLinks(blog.script)
        orderedCorefClusters = createEventsClusters(corefTagsPairList)

        for event in eventsMentions:
            textStart, textStop = getTextStartStop(event.textStartStop)
            fparser.write('system1\t%s\t%s\t%s,%s\t%s\t%s_%s\t%s\t1 1 1\n' % (blog.script.scriptName, event.eventTag, textStart, textStop, event.textValue, event.eventType, event.eventSubtype, event.realisValue))

        for cluster in orderedCorefClusters:
            string = ""
            cluster = cluster[0]
            j = 0
            for evP in cluster:
                if j == 0:
                    string = evP[0]
                else:
                    string = string + ',' + evP[0]
                j = j + 1
            string = string + ',' + cluster[-1][1]
            gotit = gotit + 1
            fparser.write('@Coreference\tR%d\t%s\n' % (gotit, string))

        for eventPair in eventsStore:
            event1 = eventPair[0]
            event2 = eventPair[1]
            gotit = gotit + 1
            fparser.write('@After\tR%d\t%s,%s\n' % (gotit, event1.eventTag, event2.eventTag))
        fparser.write('#EndOfDocument\n')

#    accuracy = accuracy_score(devLabels, predicted)
#    print("Accuracy AdaBoost Classifier: %f" % accuracy)

if __name__ == "__main__": main()
