#!/usr/bin/env python

import os
import sys
import pickle
import glob
import textrank.ranker
import textrank.tagger

pickle_file = open(os.path.dirname(__file__) + "/textrank_tagger.pickle")
tagger = pickle.load(pickle_file)
pickle_file.close() 
#tagger = TextRankTagger(nltk.corpus.brown.tagged_sents())
ranker = textrank.ranker.TextRank(tagger)

comments = sys.stdin.read()
ranker.extract_sentences(comments, 10)
