from __future__ import division
import copy
import os
import re
import pickle
import numpy as np
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

fparser = open('parseroutput.tbf', 'r')
fparserOut = open('parseroutputOut.tbf', 'w')


def main():
    lines = fparser.readlines()
    isDoc = 'yes'
    afterLinks = []
    afterLinksOrder = []
    for line in lines:
        if line.startswith("#Begin"):
            print(line)
            isNewDoc = 'yes'
            afterLinks = []
            afterLinksOrder = []
            fparserOut.write(line)
        if line.startswith('system1'):
            fparserOut.write(line)
        if line.startswith('@Coreference'):
            fparserOut.write(line)
        if line.startswith('@After'):
            afterLinks.append(line)
        if line.startswith('#End'):
            for link in afterLinks:
                m = re.search('(E[0-9]+)\,(E[0-9]+)', link)
                ev1 = m.group(1)
                ev2 = m.group(2)
                after = [ev1, ev2]
                afterLinksOrder.append(after)
            ev1 = [ x[0] for x in afterLinksOrder]
            ev2 = [ x[1] for x in afterLinksOrder]
            uniqEv1 = list(set(ev1))
            print(uniqEv1)
            fparserOut.write(line)





if __name__ == "__main__": main()
