from collections import Counter
from lxml import etree
import os
import logging
import string
import itertools
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import re
import event as ev
import createdevset as cds

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

class ArticlesImport:
    def __init__(self, path):
        self.path = path

#        self.fileNames = self.getDirectoryListinbg(path)
        dataSets = cds.CreateDataSets(path)
        self.fileNamesTrain = [ dataSets.filenames[x]+'.txt' for x in dataSets.trainingSetFiles ]
        self.fileNamesDev = [dataSets.filenames[x] + '.txt' for x in dataSets.devSetFiles]

        # fileNamesDev = []
        # fileNamesTrain = []
        # for x in dataSets.devSetFiles:
        #     print(x)
        #     print("Filenames Dev: %s" % dataSets.filenames[x])
        #     fileNamesDev.append(dataSets.filenames[x] + '.txt')
        #
        # for x in dataSets.trainingSetFiles:
        #     print(x)
        #     print("Filenames Train: %s" % dataSets.filenames[x])
        #     fileNamesTrain.append(dataSets.filenames[x] + '.txt')



    # if setType == 'train':
        #     self.storyArticlesList = self.getStoryArticles(self.fileNamesTrain)
        #     self.blogArticlesList = self.getBlogArticles(self.fileNamesTrain)
        # else:
        #     self.storyArticlesList = self.getStoryArticles(self.fileNamesDev)
        #     self.blogArticlesList = self.getBlogArticles(self.fileNamesDev)

    def getDirectoryListing(self, path):
        # for dirname, dirnames, filenames in os.walk(path):
        #     continue
        for dirname, dirnames, filenames in os.walk(path):
            continue
        filenamespath = [ f for f in filenames if f.endswith(".txt")]
        return filenamespath

    def getStoryArticles(self, setType):
        articles = []
        if setType == 'train':
            fileNames = self.fileNamesTrain
        else:
            fileNames = self.fileNamesDev
        for file in fileNames:
            article = Article(file, self.path)
            if article.articleType == 'story':
                articles.append(article)
        return articles

    def getBlogArticles(self, setType):
        articles = []
        if setType == 'train':
            fileNames = self.fileNamesTrain
        else:
            fileNames = self.fileNamesDev
        for file in fileNames:
            article = Article(file, self.path)
            if article.articleType != 'story':
                articles.append(article)
        return articles

class Article:
    """
    Unlike the Script class that gets more pure events stuff, this class is performing some stats on the Article
    """
    def __init__(self, articleName, path):
        self.path = path
        self.articleNameNoPath = articleName
        self.articleName = path+articleName
        logging.debug(self.articleName)
        scriptName = articleName.replace(".txt", "")
        self.script = ev.Script(scriptName)
        # The following is the list of all the event objects in the script.
        self.articleEventsList = self.script.eventsList
        self.articleTree = etree.parse(self.articleName)
        self.articleType = self.getArticleType()
        if self.articleType == "story":
            self.docRoot = self.articleTree.xpath("//DOC[@type='story']")
            self.headline = self.getStoryHeadline()
            self.sentences = self.getStorySentences()
        else:
            self.docRoot = self.articleTree.getroot()
            #self.posts = self.getPosts()
        logging.debug("This is the file name: %s", articleName)
        with open(path+articleName) as f:
            lines = f.read().splitlines()
        fileAsCharactersList = '\n'.join(lines)
        self.fileAsCharactersList = re.sub(r'[^\x00-\x7F]+', ' ', fileAsCharactersList)

    def getSentenceFromEvent(self, event):
        """
        Returns the sentence number inside the article for a story type of article.
        :param event:
        :return:
        """
        """
        Returns the sentence number inside the article for a story type of article.
        :param event:
        :return:
        """
        eventPosition = event.textStartStop
        eventText = event.textValue
        charsFile = self.fileAsCharactersList
        m = re.search('^([0-9]+).*?([0-9]+)$', eventPosition)
        if m:
            startChar = int(m.group(1))
            stopChar = int(m.group(2))
        notYet = 1
        movingChar = startChar
        while notYet:
            movingChar = movingChar - 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                startPos = movingChar
        notYet = 1
        movingChar = stopChar-1
        while notYet:
            movingChar = movingChar + 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                stopPos = movingChar
        logging.debug("This is the start position for the sentence including the event: %d", startPos)
        logging.debug("This is the stop position for the sentence including the event: %d", stopPos)

        sentence = charsFile[startPos:stopPos]
        sentence = sentence.lstrip()
        sentence = sentence.rstrip()
        offsetStart = startChar-startPos
        offsetStop = stopChar-startPos
        logging.debug("This is the event text %s: ", eventText)
        logging.debug("This is the event sentence %s: ", sentence)
        return sentence, offsetStart, offsetStop

    def getNeighboringWords(self, event):
        WINDOWLEN = 3
        tokenizer = RegexpTokenizer(r'\w+')
        sentence, offsetStart, offsetStop = self.getSentenceFromEvent(event)

        eventWords = tokenizer.tokenize(re.sub(r'[^\x00-\x7F]+', ' ', event.textValue))
        logging.debug("These are the tokenized words of the event: %s", eventWords)
        eventWord = eventWords[0].lower()

        stopWords = stopwords.words('english')
        if eventWord in stopWords:
            del stopWords[stopWords.index(eventWord)]

        logging.debug("This is the sentence: %s", sentence)
        sentenceWords = tokenizer.tokenize(sentence)
        sentenceWords = [word.lower() for word in sentenceWords if word not in stopWords]
        logging.debug("This is the tokenized sentence: %s", sentenceWords)
        for w in sentenceWords:
            if eventWord in w:
                eventWordIndex =  sentenceWords.index(w)
                break
        sentenceLength = len(sentenceWords)
        if eventWordIndex == 0:
            leftWordsList = []
        else:
            minIndex = max(0,(eventWordIndex-WINDOWLEN))
            maxIndex = eventWordIndex-1
            leftWordsList = sentenceWords[minIndex:(maxIndex+1)]

        if eventWordIndex == (sentenceLength-1):
            rightWordsList = []
        else:
            minIndex = eventWordIndex+1
            maxIndex = min((sentenceLength-1), (eventWordIndex+WINDOWLEN))
            rightWordsList = sentenceWords[minIndex:maxIndex+1]
        logging.debug("This is the tokenized left list: %s", leftWordsList)
        logging.debug("This is the tokenized right list: %s", rightWordsList)
        return leftWordsList, rightWordsList, eventWord


    def getSentenceNumberFromEvent(self, event):
        """
        Returns the sentence number inside the article for a story type of article.
        :param event:
        :return:
        """
        eventPosition = event.textStartStop
        eventText = event.textValue
        charsFile = self.fileAsCharactersList
        m = re.search('^([0-9]+).*?([0-9]+)$', eventPosition)
        if m:
            startChar = int(m.group(1))
            stopChar = int(m.group(2))
        notYet = 1
        movingChar = startChar
        while notYet:
            movingChar = movingChar - 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                startPos = movingChar
        notYet = 1
        movingChar = stopChar-1
        while notYet:
            movingChar = movingChar + 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                stopPos = movingChar
        logging.debug("This is the start position for the sentence including the event: %d", startPos)
        logging.debug("This is the stop position for the sentence including the event: %d", stopPos)
        logging.debug("This is the event text %s", eventText)
        logging.debug("This is the event position %s", eventPosition)
        sentence = charsFile[startPos:stopPos]
        sentence = sentence.lstrip()
        sentence = sentence.rstrip()
        sentenceNumber = 0
        for i in range(len(self.sentences)):
            logging.debug("This is the sentence I want to find: %s", sentence)
            logging.debug("This is the sentence in the article: %s", self.sentences[i])
            if sentence in self.sentences[i]:
                logging.debug("I have found the sentence at this par: %d", i)
                sentenceNumber = i
        return sentenceNumber

    def getPostText(self, nodeRoot):
        nodeTextResults = ""
        nodeText = [x for x in nodeRoot.itertext()]
        logging.debug("This is the post text to dissect: %s", nodeText)
        nodeText = [ re.sub(r'[^\x00-\x7F]+', ' ', x) for x in nodeText ]

        if len(nodeRoot.getchildren()) > 0:
            quoteText = nodeRoot.getchildren()[0].text
            for line in nodeText:
                if line != quoteText:
                    nodeTextResults = nodeTextResults + line
            nodeTextResults = nodeTextResults.lstrip()
            nodeTextResults = nodeTextResults.rstrip()
            nodeTextResults = nodeTextResults.replace('\n', ' ')
            nodeTextResults = nodeTextResults.strip()
        else:
            nodeTextResults = nodeRoot.text
        return nodeTextResults

    def getPositionInTree(self, nodeRoot, sentence):
        """
        The tree here is the xml structure of the document. This is a recursive procedure that gets the position of a sentence in the tree
        :param nodeRoot: 
        :param sentence: 
        :return: 
        """
        if nodeRoot.tag == "post":
            nodeText = self.getPostText(nodeRoot)
        else:
            nodeText = nodeRoot.text
            if nodeText == None:
                nodeText = []
        logging.debug("This is the node text: %s", nodeText)
        logging.debug("This is the sentence I want to match: %s", sentence)
        logging.debug("The node type is a: %s", nodeRoot.tag)
        if sentence in nodeText:
            logging.debug("This is the nodeId: %s", (nodeRoot.tag+nodeRoot.getparent().get('id')))
            logging.debug("Found the sentence\n\n\n")
            return nodeRoot.tag+nodeRoot.getparent().get('id')
        else:
            logging.debug("Sentence not found\n\n\n")
            children = nodeRoot.getchildren()
            if children != []:
                for child in children:
                    isSentence = self.getPositionInTree(child, sentence)
                    logging.debug("This is the value of isSentence: %s", isSentence)
                    if (isSentence != None) and (isSentence != 0):
                        return isSentence
            else:
                return 0

    def getPostIdentifierForBlogsFromEvents(self, event):
        """
        This function identifies the start and end characters for the post of a specific blog event. Given an event we identify the post in which the event occurs by the start and stop character of the event, by finding the occurrence of <post and /post>.
        :param event: 
        :return: 
        """
        eventPosition = event.textStartStop
        eventText = event.textValue
        charsFile = self.fileAsCharactersList
        m = re.search('^([0-9]+).*?([0-9]+)$', eventPosition)
        if m:
            startChar = int(m.group(1))
            stopChar = int(m.group(2))
        notYet = 1
        movingChar = startChar
        while notYet:
            movingChar = movingChar - 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '<':
                if charsFile[movingChar+1] == 'p':
                    notYet = 0
                    startPos = movingChar
        notYet = 1
        movingChar = stopChar-1
        while notYet:
            movingChar = movingChar + 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '>':
                if charsFile[movingChar-1] == 't':
                    notYet = 0
                    stopPos = movingChar
        logging.debug("This is the start position for the post for this event: %d", startPos)
        logging.debug("This is the stop position for the post for this event: %d", stopPos)
        return [startPos, stopPos]

    def getTreePositionFromEvent(self, event):
        posts = []
        logging.debug("Starting processing of Event: %s", event.eventTag)
        eventPosition = event.textStartStop
        eventText = event.textValue
        charsFile = self.fileAsCharactersList
        m = re.search('^([0-9]+).*?([0-9]+)$', eventPosition)
        if m:
            startChar = int(m.group(1))
            stopChar = int(m.group(2))
        notYet = 1
        movingChar = startChar
        while notYet:
            movingChar = movingChar - 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                startPos = movingChar
        notYet = 1
        movingChar = stopChar-1
        while notYet:
            movingChar = movingChar + 1
            charToCheck = charsFile[movingChar]
            if charToCheck == '\n':
                notYet = 0
                stopPos = movingChar
        logging.debug("This is the start position: %d", startPos)
        logging.debug("This is the stop position: %d", stopPos)
        logging.debug("This is the event text %s", eventText)
        logging.debug("This is the event position %s", eventPosition)
        sentence = charsFile[startPos:stopPos]
        sentence = sentence.lstrip()
        sentence = sentence.rstrip()
        sentence = re.sub(r'<[A-Za-z]+.*/[A-Za-z]>', '', sentence)
        sentence = sentence.strip()

        logging.debug("This is the sentence I want to find: %s", sentence)
        if sentence == "":
            return 0
        else:
            position = self.getPositionInTree(self.docRoot, sentence)
        return position

    def getArticleType(self):
        docRoot = self.articleTree.xpath("//DOC[@type='story']")
        if docRoot:
            return 'story'
        else:
            return 'posts'

    def parseParagraph(self, text):
        text = text.rstrip()
        text = text.lstrip()
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        return text

    def getStoryHeadline(self):
        headline = self.docRoot[0].find('HEADLINE')
        if headline != None:
            headlineText = self.parseParagraph(headline.text)
            logging.debug("This is the headline: %s", headlineText)
        else:
            headlineText = ""
        return headlineText

    def getStorySentences(self):
        sentences = []
        headline = [self.getStoryHeadline()]
        articleText = self.docRoot[0].find('TEXT')
        articlesPars = articleText.getchildren()
        for article in articlesPars:
            articleText = article.text
            articleText = self.parseParagraph(articleText)
            sentences.append(articleText)
        return(headline+sentences)

    # def getStorySentences(self):
    #     sentences = []
    #     articleText = self.docRoot[0].find('TEXT')
    #     articlesPars = articleText.getchildren()
    #     for article in articlesPars:
    #         articleText = article.text
    #         articleText = self.parseParagraph(articleText)
    #         sentences.append(articleText)
    #     return(sentences)

    def checkLinksConsistency(self):
        incons = 0
        articleName = self.articleName.replace(self.path, "")
        articleName = articleName.replace(".txt", "")
        script = ev.Script(articleName)
        eventsList = script.getListOfEventsWithAfterLinks()
        logging.debug("This is the list of events: %s", eventsList)
        eventsPositions = {}
        for event in eventsList:
            eventId = event.eventTag
            logging.debug("This is the start and stop: %s", event.textStartStop)
            # eventPosition = article.getSentenceNumberFromEvent(event)
            eventPosition = self.getTreePositionFromEvent(event)
            logging.debug("The sentence is at this position: %s\n\n\n", eventPosition)
            eventsPositions[eventId] = eventPosition
        clusters = script.eventsClusters
        logging.debug("This is the positions of the events: %s", eventsPositions)
        logging.debug("These are the events clusters: %s", clusters)
        clusterPositionsList = []
        for cluster in clusters:
            positionList = []
            for eventPair in cluster[0]:
                ev1 = eventPair[0]
                ev2 = eventPair[1]
                pos1 = eventsPositions[ev1]
                pos2 = eventsPositions[ev2]
                positionList.append(pos1)
                positionList.append(pos2)
            clusterPositionsList.append(positionList)
        logging.debug("These are the position lists: %s", clusterPositionsList)
        for posList in clusterPositionsList:
            #for position in posList:
            unique = set(posList)
            if len(unique) > 1:
                incons = 1
                logging.debug("I have found an exception, ")
        return incons

    def getDistanceBetweenEvents(self, event1, event2):
        """
        This procedure applies only to stories type of events for now
        :param event1: This is an event as in an object, so it has already been translated from the event Id to an object
        :param event2: This is an event as in an object, so it has already been translated from the event Id to an object
        :return:
        """
        distance = self.getSentenceNumberFromEvent(event2)-self.getSentenceNumberFromEvent(event1)
        return distance

    def getGlobalNumberOfEventsPairs(self):
        eventsList = self.articleEventsList
        logging.debug("There are %d events in article %s", len(eventsList), self.script.scriptName)
        eventsPairs = list(itertools.combinations(eventsList, 2))
        numberOfEventsPairs = 2 * len(eventsPairs)
        return numberOfEventsPairs

def main():
    scriptsStories = ArticlesImport('LDC2015E73/')
#     article = Article('bolt-eng-DF-170-181125-9125545.txt', 'LDC2015E73/')

    storyFiles = scriptsStories.getStoryArticles('train')
    for story in storyFiles:
        corefTagsPairList = story.script.getListOfCoreferenceLinks()
        orderedCorefClusters = story.script.createEventsClusters(corefTagsPairList)
        if orderedCorefClusters != []:
            print("%s %s" % (story.script.scriptName, orderedCorefClusters))

        # blogFiles = scriptsStories.getBlogArticles('train')
    # i = 0
    # for blogFile in blogFiles:
    #     events = blogFile.script.eventsList
    #     for event in events:
    #         i = i+1
    #         positions = blogFile.getPostIdentifierForBlogsFromEvents(event)
    #         logging.info("%d ---> This is the start and the stop of this event: %d, %d", i, positions[0], positions[1])


#     script = ev.Script('XIN_ENG_20090915.0127')
#     event = script.getEventByEventId('E77')
#     sentenceNumber = article.getSentenceNumberFromEvent(event)
#     print(sentenceNumber)

#    script = ev.Script('XIN_ENG_20090915.0127')
#    article = Article('bolt-eng-DF-170-181125-9125545.txt', 'LDC2015E73/')
#    consistency = article.checkLinksConsistency()
#    print(consistency)

    # blogFiles = scriptsStories.getBlogArticles()
    # for blogFile in blogFiles:
    #     print(blogFile.articleName)
    #     consistency = blogFile.checkLinksConsistency()
    #     if consistency == 1:
    #         print(consistency)

    # script = ev.Script('bolt-eng-DF-212-191668-3064026')
    # event = script.getEventByEventId('E277')
    # article = Article('bolt-eng-DF-212-191668-3064026'+'.txt', 'LDC2015E73/')
    # article.getTreePositionFromEvent(event)
    # article.checkLinksConsistency()


    # script = ev.Script('bolt-eng-DF-170-181125-9125545')
    # eventsList = script.getListOfEventsWithAfterLinks()
    # logging.debug("This is the list of events: %s", eventsList)
    # eventsPositions = {}
    # for event in eventsList:
    #     eventId = event.eventTag
    #     logging.debug("This is the start and stop: %s", event.textStartStop)
    #     #eventPosition = article.getSentenceNumberFromEvent(event)
    #     eventPosition = article.getTreePositionFromEvent(event)
    #     logging.debug("The sentence is at this position: %s\n\n\n", eventPosition)
    #     eventsPositions[eventId] = eventPosition
    # clusters = script.eventsClusters
    #
    # logging.debug("This is the list of events: %s", eventsList)
    # logging.debug("This is the positions of the events: %s", eventsPositions)
    # logging.debug("These are the events clusters: %s", clusters)
    # clusterPositionsList = []
    # for cluster in clusters:
    #     howMany = len(cluster[0])
    #     positionList = []
    #     for eventPair in cluster[0]:
    #         ev1 = eventPair[0]
    #         ev2 = eventPair[1]
    #         pos1 = eventsPositions[ev1]
    #         pos2 = eventsPositions[ev2]
    #         positionList.append(pos1)
    #         positionList.append(pos2)
    #     clusterPositionsList.append(positionList)
    # for posList in clusterPositionsList:
    #     for position in posList:
    #         unique = set(position)
    #         if len(unique) < 1:
    #             logging.debug("I have found an exception")

if __name__ == "__main__": main()