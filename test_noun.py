import nltk
import nltk.corpus
from nltk.corpus import brown 


class Node:
  def __init__(self, word):
    self.word = word
    self.edges = {}

class TextRank:
  def __init__(self, tagger):
    self.tagger = tagger

  def build_node_dict(selc, sentences):
    node_dict = {}
    for sentence in sentences:
      for tagged in sentence:
        if tagged[1] == 'NN' or tagged[1] == 'JJ' or tagged[1] is None:
          if not tagged[0].lower() in node_dict:
            node_dict[tagged[0].lower()] = Node(tagged[0].lower())
    return node_dict


  def extract_keywords(self, text):
    sentences = nltk.sent_tokenize(text)
    split_sentences = [nltk.word_tokenize(x) for x in sentences]
    tagged_sentences = [self.tagger.tag(x) for x in split_sentences]
    print tagged_sentences
    print self.build_node_dict(tagged_sentences)


tagger = nltk.UnigramTagger(nltk.corpus.brown.tagged_sents())
ranker = TextRank(tagger)
ranker.extract_keywords("The quick brown fox, yo")    
