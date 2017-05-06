import os
import re
import logging
import copy
import constants as const

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

#ANNDIR = 'LDC2015E73/'
# ANNDIR = 'LDC2017E08/'
ANNDIR = const.ANNDIR

class Script:
    """
    eventsList is the list of events object one by one
    """
    def __init__(self, scriptName):
        self.scriptName = scriptName
        self.eventsList, self.referenceObjList = self.loadEvents(scriptName)
        self.afterLinksList = self.getListOfExtraAfterLinks()
        #self.afterLinksList = self.getListOfAfterLinks()
        self.eventsClusters = self.createEventsClusters(self.afterLinksList)

    def getEventByEventId(self, eventId):
        for e in self.eventsList:
            if eventId == e.eventTag:
                return e

    def getEventDetailsByEventId(self, eventId):
        for e in self.eventsList:
            if eventId == e.eventTag:
                return e.eventType, e.eventSubtype, e.eventTextRef, e.textValue, e.realisType, e.realisValue

    # def getListOfEventsWithAfterLinks(self):
    #     """
    #     The lines marked as After are actually the ones that have events with after links. If we want to know the list of events that have after links, we simply have to get the linkArg1 and linkArg2 from all the linkType-s that are marked as 'After'. So that's what I am doing here
    #     :return:
    #     """
    #     listEventsTagsAfter = []
    #     listEvents = []
    #     for eventLink in self.referenceObjList:
    #         if eventLink.linkType == 'After':
    #             listEventsTagsAfter.append(eventLink.linkArg1)
    #             listEventsTagsAfter.append(eventLink.linkArg2)
    #     listEventsAfterSet = set(listEventsTagsAfter)
    #     listEventsAfter = list(listEventsAfterSet)
    #     for event in self.eventsList:
    #         if event.eventTag in listEventsAfter:
    #             listEvents.append(event)
    #     return listEvents


    def getListOfEventsWithAfterLinks(self):
        """
        We just want to know the list of events that have after links, so the unique event identifiers, we can take it from the list of events with after links and make it unique using a set. The result is a list of event objects.
        <type 'list'>: [[['E1509', 'E322']], 0]
        :return: 
        """
        listEventsTagsAfter = []
        listEvents = []
        for afterLink in self.afterLinksList:
            listEventsTagsAfter.append(afterLink[0][0][0])
            listEventsTagsAfter.append(afterLink[0][0][1])
        listEventsAfterSet = set(listEventsTagsAfter)
        listEventsAfter = list(listEventsAfterSet)
        for event in self.eventsList:
            if event.eventTag in listEventsAfter:
                listEvents.append(event)
        return listEvents





    def loadEvents(self, scriptName):
        path = os.getcwd()
        eventsObjList = []
        referenceObjList = []
        with open(path + '/' + ANNDIR + '/' + scriptName + '.ann', "r") as f:
            lines = f.readlines()
        i = 0
        j = 0
        eventList = []
        for line in lines:
            if line[0] != 'R':
                logging.debug("This is the line: %s" % line)
                if i < 3:
                    eventList.append(line)
                    i += 1
                else:
                    logging.debug("These are the event lines: %s" % eventList)
                    event = Event(eventList)
                    eventsObjList.append(event)
                    eventList = []
                    eventList.append(line)
                    i = 1
            else:
                if j == 0:
                    logging.debug("These are the event lines: %s" % eventList)
                    event = Event(eventList)
                    eventsObjList.append(event)
                    j = 1
                if j > 0:
                    logging.debug("These is the link line: %s" % line)
                    link = EventLink(line)
                    referenceObjList.append(link)
                    # Do what's needed for the coreference
        return eventsObjList, referenceObjList

    def getListOfSubEventClusters(self):
        refList = self.referenceObjList
        for link in refList:
            if link.linkType == "After":
                logging.debug("This is the arg1: %s" % link.linkArg1)
                logging.debug("This is the arg2: %s" % link.linkArg2)

    def getListOfCoreferenceClusters(self):
        """
        Not used.
        :return: 
        """
        refList = self.referenceObjList
        corefList = []
        for link in refList:
            if link.linkType == "Coreference":
                logging.info("This is the arg1: %s" % link.linkArg1)
                logging.info("This is the arg2: %s" % link.linkArg2)
                corefLink = [link.linkArg1, link.linkArg2]
                corefList.append(corefLink)
        return corefList

    def getListOfAfterLinks(self):
        eventsTagsPairList = []
        eventLinksList = self.referenceObjList
        for eventLink in eventLinksList:
            if eventLink.linkType == 'After':
                pair = [[[eventLink.linkArg1, eventLink.linkArg2], ], 0]
                eventsTagsPairList.append(pair)
        return eventsTagsPairList

    def getListOfCoreferenceLinks(self):
        """
        Gets the list of coreference links from the script
        :param script: 
        :return: 
        """
        eventsTagsPairList = []
        eventLinksList = self.referenceObjList
        for eventLink in eventLinksList:
            if eventLink.linkType == 'Coreference':
                pair = [[[eventLink.linkArg1, eventLink.linkArg2], ], 0]
                eventsTagsPairList.append(pair)
        return eventsTagsPairList

    def checkIfCorefInListF(self, corefLinks, eventTag):
        returnPar = None
        for link in corefLinks:
            link0Cor = link[0][0][0]
            link1Cor = link[0][0][1]
            if link0Cor == eventTag:
                returnPar = link1Cor
        return returnPar

    def checkIfCorefInListB(self, corefLinks, eventTag):
        returnPar = None
        for link in corefLinks:
            link0Cor = link[0][0][0]
            link1Cor = link[0][0][1]
            if link1Cor == eventTag:
                returnPar = link0Cor
        return returnPar

    def checkExtraAfterFromCorefF(self, corefLinks, afterLink):
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
        corLink0 = self.checkIfCorefInListF(corefLinks, link0)
        if corLink0 != None:
            corLink1 = self.checkIfCorefInListF(corefLinks, link1)
            if corLink1 != None:
                newAfterLink = [[[corLink0, corLink1]], 0]
                returnList.append(newAfterLink)
                partialReturn = self.checkExtraAfterFromCorefF(corefLinks, newAfterLink)
                returnList = returnList + partialReturn
        return returnList

    def checkExtraAfterFromCorefB(self, corefLinks, afterLink):
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
        corLink0 = self.checkIfCorefInListB(corefLinks, link0)
        if corLink0 != None:
            corLink1 = self.checkIfCorefInListB(corefLinks, link1)
            if corLink1 != None:
                newAfterLink = [[[corLink0, corLink1]], 0]
                returnList.append(newAfterLink)
                partialReturn = self.checkExtraAfterFromCorefB(corefLinks, newAfterLink)
                returnList = returnList + partialReturn
        return returnList

    def getListOfExtraAfterLinks(self):
        afterLinks = self.getListOfAfterLinks()
        corefLinks = self.getListOfCoreferenceLinks()
        newAfterLinks = []
        for afterLink in afterLinks:
            newLinksF = self.checkExtraAfterFromCorefF(corefLinks, afterLink)
            newLinksB = self.checkExtraAfterFromCorefB(corefLinks, afterLink)
            newLinks = newLinksF + newLinksB
            newAfterLinks = newAfterLinks + newLinks
        newAfterLinks = afterLinks+newAfterLinks
        return newAfterLinks

    def checkEventAttach(self, eventsTagsPairList, event):
        # first zero is the list itself, the second zero is the first list and the third zero is the first element
        # [ [[a,b], [c,d], ..., [w,z] ] , 0]
        matchA = event[0][0][0]  # this selects a
        matchB = event[0][-1][1]  # this selects z
        n = len(eventsTagsPairList)
        for i in range(n):
            if eventsTagsPairList[i][1] == 0:
                # first element in the list
                matchEA = eventsTagsPairList[i][0][0][0]
                # last element in the list
                matchEB = eventsTagsPairList[i][0][-1][1]
                if matchEA == matchB:
                    logging.debug("There is a match; A: %s, B: %s", matchEA, matchB)
                    newEvent = [event[0] + eventsTagsPairList[i][0], 0]
                    eventsTagsPairList[i][1] = 1
                    return newEvent, 1
                if matchEB == matchA:
                    logging.debug("There is a match; A: %s, B: %s", matchA, matchEB)
                    newEvent = [eventsTagsPairList[i][0] + event[0], 0]
                    eventsTagsPairList[i][1] = 1
                    return newEvent, 1
        eventToReturn = copy.copy(event)
        eventToReturn[1] = 0
        return eventToReturn, 0

    def checkListEmpty(self, eventsTagsPairList, newList):
        for e in eventsTagsPairList:
            if e[1] == 0:
                return 0
        return 1

    def createEventsClusters(self, eventsTagsPairList):
        """
        Creates a list of Events Clusters from the script
        :param eventsTagsPairList:
        :return:
        """
        newList = []
        n = len(eventsTagsPairList)
        doMore = 0
        for i in range(n):
            logging.debug("These are the events: %s", eventsTagsPairList[i])
            # This is the last element of the list to whom we want to attach
            if eventsTagsPairList[i][1] == 0:
                eventsTagsPairList[i][1] = 1
                newEvent, flag = self.checkEventAttach(eventsTagsPairList, eventsTagsPairList[i])
                newList.append(newEvent)
                if flag == 1:
                    doMore = 1
        if doMore == 0:
            listToPass = copy.deepcopy(newList)
            return listToPass
        else:
            newList = self.createEventsClusters(newList)
            return newList


class EventLink:
    def __init__(self, linkLine):
        self.linkTag, self.linkType, self.linkArg1, self.linkArg2 = self.parseEventLinks(linkLine)

    def parseEventLinks(self, textLine):
        # R13     Coreference Arg1:E208 Arg2:E247
        logging.debug("These is the link line: %s" % textLine)
        m = re.search('^(R[0-9]+?)\s+(.*)\sArg1:(E[0-9]+)\sArg2:(E[0-9]+)', textLine)
        s = re.search('^(R[0-9]+?)\s+(.*)\sParent:(E[0-9]+)\sChild:(E[0-9]+)', textLine)
        if m:
            return m.group(1), m.group(2), m.group(3), m.group(4)
        elif s:
            return s.group(1), s.group(2), s.group(3), s.group(4)
        else:
            return 0

class Event:
    def __init__(self, eventLines):
        logging.debug("These are the event lines: %s" % eventLines)
        lines = eventLines
        self.eventTag, self.eventType, self.eventSubtype, self.eventTextRef = self.parseEventLine(lines[1])
        #self.textStart, self.textStop, self.textValue = self.parseEventText(lines[0])
        self.textStartStop, self.textValue = self.parseEventText(lines[0])
        self.realisType, self.realisValue = self.parseRealis(lines[2])

    def parseEventLine(self, eventLine):
        #E714        Transaction_Transfer - Money:T7
        logging.debug("This is the event line: %s", eventLine)
        m = re.search('^(E[0-9]+?)\s+(.*)_(.*):(.*)$', eventLine)
        try:
            eventTag = m.group(1)
        except:
            logging.debug('Issue with parsing: %s', eventLine)
        eventType = m.group(2)
        eventSubtype = m.group(3)
        eventTextRef = m.group(4)
        return eventTag, eventType, eventSubtype, eventTextRef

    def parseEventText(self, textLine):
        #T7      Transaction_Transfer-Money 18562 18567  gives
        #T11     Personnel_End - Position 869 876;877 881 stepped down
        #m = re.search('^(T[0-9]+?)\s+(.*)_(.*)\s([0-9]+)\s([0-9]+)\s+(.*)$', textLine)
        m = re.search('^(T[0-9]+?)\s+(.*)_(.*?)\s([0-9]+.*)\t(.*)$', textLine)
        try:
            textStartStop = m.group(4)
        except:
            print(1)
        textValue = m.group(5)
        # textStart = m.group(4)
        # textStop = m.group(5)
        # textStart = m.group(4)
        #return textStart, textStop, textValue
        return textStartStop, textValue

    def parseRealis(self, realisText):
        #A7      Realis E714 Actual
        m = re.search('^(A[0-9]+?)\s+(.*)\s+(.*)\s+(.*)$', realisText)
        realisType = m.group(2)
        realisValue = m.group(3)
        return realisType, realisValue
