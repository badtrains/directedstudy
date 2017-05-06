import numpy as np
import importarticle as ia
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import constants as const
import logging

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

def loadGloveModel(gloveFile):
    embeddingsIndex = {}
    f = open(gloveFile)
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddingsIndex[word] = coefs
    f.close()
    model = embeddingsIndex
    return model

MODEL = loadGloveModel('glove.6B.100d.txt')


def computeGloveFeature(wordList):
    model = MODEL
    EMBLEN = 100
    listLen = len(wordList)
    avgEmbedding = np.zeros(EMBLEN)
#    unkEmbedding = np.random.uniform(-1,1, EMBLEN)
    if wordList == []:
        returnValue = avgEmbedding
        logging.debug("This is the embedding: %s", returnValue)
    else:
        for word in wordList:
            try:
                wordEmbedding = model[word]
            except:
                wordEmbedding = model['unknown']
            avgEmbedding = avgEmbedding+wordEmbedding
        avgEmbedding = avgEmbedding/listLen
        returnValue = avgEmbedding
        logging.debug("This is the embedding: %s", returnValue)
    return returnValue

def getArticleObject(file):
    # ANNDIR = 'LDC2015E73/'
    ANNDIR = const.ANNDIR
#    ANNDIR = 'LDC2017E08/'
    article = ia.Article(file+'.txt', ANNDIR)
    return article

def main():
    model = loadGloveModel('glove.6B.100d.txt')
    tokenizer = RegexpTokenizer(r'\w+')
#    importArticles = ia.ArticlesImport('LDC2015E73/')
    importArticles = ia.ArticlesImport('LDC2017E08/')

    # article = ia.Article('bolt-eng-DF-170-181122-8808533.txt', 'LDC2015E73/')
    # article = ia.Article('bolt-eng-DF-170-181122-8803967.txt', 'LDC2015E73/')

        # eventsList = article.articleEventsList
        # for event in eventsList:
        #     #number = article.getTreePositionFromEvent(event)
        #     leftWordsList, rightWordsList, eventWord = article.getNeighboringWords(event)
        #     #sentence, offsetStart, offsetStop = article.getSentenceFromEvent(event)
        #     print("This is the event: %s" % eventWord)
        #     print("This is the event: %s %s" % (leftWordsList, rightWordsList))

    allStories = importArticles.getBlogArticles('train')

    for article in allStories:
        eventsList = article.articleEventsList
        for event in eventsList:
            #number = article.getTreePositionFromEvent(event)
            leftWordsList, rightWordsList, eventWord = article.getNeighboringWords(event)
            #sentence, offsetStart, offsetStop = article.getSentenceFromEvent(event)
            print("This is the event: %s" % eventWord)
            print("This is the lists: %s %s" % (leftWordsList, rightWordsList))
            leftEmb = computeGloveFeature(model, leftWordsList)
            rightEmb = computeGloveFeature(model, rightWordsList)
            print(leftEmb)
            print(rightEmb)



    # for story in allStories:
    #     sentences = story.getStorySentences()
    #     for sentence in sentences:
    #         words = tokenizer.tokenize(sentence)
    #         words = [word.lower() for word in words if word not in stopwords.words('english')]
    #         for word in words:
    #             if word not in model.keys():
    #                 print("I can't find this word: %s" % word)



if __name__ == "__main__": main()
