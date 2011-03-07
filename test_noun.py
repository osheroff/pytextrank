#!/usr/bin/env python
# coding=UTF-8

import nltk
import nltk.corpus
import re
from nltk.corpus import brown 
from nltk.corpus import names


WINDOW = 3

replacement_patterns = [
  ( r'won\'t', 'will not' ),
  ( r'can\'t', 'cannot' ),
  ( r'i\'m', 'i am' ),
  ( r'ain\'t', 'is not' ),
  ( r'(\w+)\'ll', '\g<1> will' ),
  ( r'(\w+)n\'t', '\g<1> not' ),
  ( r'(\w+)\'ve', '\g<1> have' ),
  ( r'(\w+)\'s', '\g<1> is' ),
  ( r'(\w+)\'re', '\g<1> are' ),
  ( r'(\w+)\'d', '\g<1> would' ),
  ( r'http://[\S+]\s', ' ')
]

name_words = {}

for name in names.words():
  name_words[name.lower()] = True


class RegexpReplacer(object):
  def __init__( self, patterns=replacement_patterns):
    self.patterns = [(re.compile(regex, re.I), repl) for (regex, repl) in patterns]

  def replace(self, text):
    s = text
    for (pattern, repl) in self.patterns:
      (s, count) = re.subn(pattern, repl, s)
      if count > 0:
        print count
        print str(pattern)
    return s


class Node:
  def __init__(self, word, pos):
    self.word = word
    self.pos = pos
    self.edges = {}
    self.score = 0.0
    self.new_score = 0.0

  def add_edge(self, node):
    self.edges[node.word] = node

  def __repr__(self):
    return "Node '%s'<%s>,%.4f,(%s)" % (self.word, self.pos, self.score, ",".join(self.edges.keys()))

class TextRank:
  def __init__(self, tagger):
    self.tagger = tagger

  def word_is_interesting(self, word, pos):
    if len(word) < 3:
      return False
    if word in name_words:
      return False
    if pos == 'NN' or pos == 'JJ':
      return True
    if pos is None:
      return re.match(r"^[A-Za-z\._]+$", word)
    else:
      return False

  def build_node_dict(self, sentences):
    node_dict = {}
    i = 0
    for sentence in sentences:
      for word, pos in sentence:
        if self.word_is_interesting(word, pos):
          if not word.lower() in node_dict:
            print "Interesting word: %s--%s @ %d" % (word, pos, i)
            node_dict[word.lower()] = Node(word.lower(), pos)
        i += 1
    return node_dict

  def build_edges(self, sentence, dictionary):
    for i in range(len(sentence)):
      this_word = sentence[i][0].lower()
      if this_word in dictionary:
        this_node = dictionary[this_word]
        j = 1 
        while i + j < len(sentence) and j < WINDOW:
          other_word = sentence[i + j][0].lower()
          if other_word in dictionary:
            other_node = dictionary[other_word] 
            this_node.add_edge(other_node)
            other_node.add_edge(this_node)
          j += 1



  def rank(self, dictionary)
    for node in dictionary.values():
      node.score = 1.0 / len(dictionary.keys())
    
    for x in range(100):  
      for node in dictionary.values():
        node.new_score = 0
        for other in node.edges.values():
          node.new_score += other.score / len(other.edges)
        node.new_score *= 0.85
        node.new_score += 1 - 0.85
      for node in dictionary.values():
        node.score = node.new_score
    return dictionary

  def extract_keywords(self, text):
    uncontract = RegexpReplacer().replace(text.lower())
    sentences = nltk.sent_tokenize(uncontract)
    split_sentences = [nltk.word_tokenize(x) for x in sentences]
    tagged_sentences = [self.tagger.tag(x) for x in split_sentences]
    dictionary = self.build_node_dict(tagged_sentences)

    for sentence in tagged_sentences:
      self.build_edges(sentence, dictionary)

    dictionary = self.rank(dictionary)

    print("\n".join([str(x) for x in sorted(dictionary.values(),key=lambda x: x.score, reverse=True)]))
    
regexp_tagger = nltk.RegexpTagger(
     [(r'^-?[0-9]+(.[0-9]+)?$', 'CD'),   # cardinal numbers
      (r'(The|the|A|a|An|an)$', 'AT'),   # articles
      (r'.*able$', 'JJ'),                # adjectives
      (r'.*ness$', 'NN'),                # nouns formed from adjectives
      (r'.*ly$', 'RB'),                  # adverbs
      (r'.*s$', 'NNS'),                  # plural nouns
      (r'.*ing$', 'VBG'),                # gerunds
      (r'.*ed$', 'VBD'),                 # past tense verbs
      (r'^i$', 'AT'),
      (r'^AND$', 'AT'),
      (r'^IN$', 'AT'),
      (r'.*', None)])
tagger = nltk.UnigramTagger(nltk.corpus.brown.tagged_sents(), backoff=regexp_tagger)
ranker = TextRank(tagger)

foo = open("sample").read()
ranker.extract_keywords(foo)    
