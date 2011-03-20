#!/usr/bin/env python

import pickle
import glob
import textrank.ranker
import textrank.tagger

pickle_file = open("./textrank_tagger.pickle", "r+")
tagger = pickle.load(pickle_file)
pickle_file.close() 
#tagger = TextRankTagger(nltk.corpus.brown.tagged_sents())
ranker = textrank.ranker.TextRank(tagger)

for fname in glob.glob("comments/*"):
  f = open(fname)
  comments = f.read()
  processed = ranker.preprocess(comments)
  #for phrase in ranker.extract_keywords(processed):
  #  print "%s (%.4f)" % (str(phrase), phrase.score())
  ranker.extract_sentences(processed, 10)


