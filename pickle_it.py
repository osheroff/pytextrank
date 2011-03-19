#!/usr/bin/env python

import textrank.tagger
import nltk.corpus
import pickle
tagger = textrank.tagger.TextRankTagger(nltk.corpus.brown.tagged_sents())
pickle.dump(tagger, open("./textrank_tagger.pickle", "w+"))
