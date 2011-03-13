import nltk.tag
import nltk.corpus
import pickle
from nltk.tag import brill
from nltk.tag import UnigramTagger, DefaultTagger
import os.path
import re
import yaml


class LambdaRegexpTagger(nltk.tag.RegexpTagger, yaml.YAMLObject):
  def choose_tag(self, tokens, index, history):
    for arr in self._regexps:
      if len(arr) == 3:
        regexp, tag, func = arr
      else:
        regexp, tag = arr
        func = None

      test_re = True
      if func:
        if not func(index, tokens[index], history):
          test_re = False

      if test_re and re.match(regexp, tokens[index]): # ignore history
        return tag
    return None
  
def begins_sentence(cls, index, *args):
  return index == 0 

word_patterns = [
    (r'^-?[0-9]+(.[0-9]+)?$', 'CD'),
    (r'.*ould$', 'MD'),
    (r'.*ing$', 'VBG'),
    (r'.*ness$', 'NN'),
    (r'.*ment$', 'NN'),
    (r'.*ful$', 'JJ'),
    (r'.*ious$', 'JJ'),
    (r'.*ble$', 'JJ'),
    (r'.*ic$', 'JJ'),
    (r'.*ive$', 'JJ'),
    (r'.*est$', 'JJ'),
    (r'^a$', 'PREP'),
    (r'^i$', 'PN'),
    (r'^[A-Z][a-z]$', 'PN', begins_sentence),
]

class TextRankTagger:
  def __init__(self, train_sents):
    print "building taggers......."
    
       
    self.tagger = nltk.tag.UnigramTagger(train_sents, backoff=LambdaRegexpTagger(word_patterns))
    #self.raubt_tagger = self.backoff_tagger(train_sents, 
    #      [nltk.tag.AffixTagger, nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger],
    #      backoff=nltk.tag.RegexpTagger(word_patterns))
    #self.tagger = self.brill_tagger(nltk.corpus.brown.tagged_sents(categories=['news', 'reviews']), nltk.tag.UnigramTagger(train_sents))
    #self.rubt_tagger = self.backoff_tagger(train_sents, 
    #      [nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger],
    #      backoff=nltk.tag.RegexpTagger(word_patterns))
    #self.tagger = self.rubt_tagger
    #self.tagger = pickle.load(open(os.path.dirname(__file__) + "/../brown_unigram.pickle"))
    #self.tagger.backoff = nltk.tag.RegexpTagger(word_patterns)  
    print "... done"

  def load_pickled(cls, pickle_filename):
    f = open(pickle_filename, "r+")
    instance = unpickle(f)
    f.close()
    return instance

  def tag(self, words):
    return self.tagger.tag(words)
  
