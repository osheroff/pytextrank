#!/usr/bin/env python
# coding=UTF-8

import pickle
import sys
import os
from textrank.ranker import TextRank


pickle_file = open(os.path.dirname(__file__) + "/textrank_tagger.pickle")
tagger = pickle.load(pickle_file)
pickle_file.close() 
ranker = TextRank(tagger)

comments = sys.stdin.read()
processed = ranker.preprocess(comments)
keywords = ranker.extract_keywords(processed)    
for x in keywords:
  sys.stdout.write("%s - %.2f\n" % (str(x), x.score()))

