#!/usr/bin/env python
# coding=UTF-8

import pickle
import re
import sys
import os
from textrank.ranker import TextRank


pickle_file = open(os.path.dirname(__file__) + "/textrank_tagger.pickle")
tagger = pickle.load(pickle_file)
pickle_file.close() 
ranker = TextRank(tagger)

comments = ""
while True:
    line = sys.stdin.readline()
    if line == '':
        break

    if re.match("__TEXTRANK_EOB", line):
        processed = ranker.preprocess(comments)
        keywords = ranker.extract_keywords(processed)    
        for x in keywords:
          sys.stdout.write("%s - %.2f\n" % (str(x), x.score()))
        sys.stdout.write("__TEXTRANK_EOB\n")
        sys.stdout.flush()
        comments = ""
    else:
        comments += line

