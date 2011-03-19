#!/usr/bin/env python
# coding=UTF-8

import nltk
import nltk.corpus
import re
import glob
import textrank.tagger
import textrank.prefilter
import pickle
import sys

DEFAULT_WORD_WINDOW = 3

class Node:
  def __init__(self, word, pos):
    self.word = word
    self.pos = pos
    self.edges = {}
    self.score = 0.0
    self.new_score = 0.0
    self.count = 1

  def add_edge(self, node):
    self.edges[node.word] = node

  def __repr__(self):
    return "'%s'<%s>" % (self.word, self.pos)
  
  def __hash__(self):
    return hash(self.word + str(self.pos))

class Phrase:
  def __init__(self, node):
    self.nodes = [node]
  
  def score(self):
    score = 0
    for x in self.nodes:
      score += x.score
    return score

  def append(self, node):
    return self.nodes.append(node)

  def __str__(self):
    return " ".join([x.word for x in self.nodes])

  def __hash__(self):
    return str(self).__hash__()

  def __cmp__(self, other):
    return cmp(str(self), str(other))

class TextRank:
  def __init__(self, tagger, prefilter=None, 
                     window=DEFAULT_WORD_WINDOW, stopwords=(), use_names_as_stopwords=True, debug=True):
    self.tagger = tagger
    if prefilter is None:
      self.prefilter = textrank.prefilter.Prefilter()

    self._init_stopwords(stopwords, use_names_as_stopwords)
    self.word_window = window
    self.do_debug = debug

  def _init_stopwords(self, stopwords, use_names):
    self.stopwords = {}
    for word in stopwords:
      self.stopwords[word.lower()] = True

    if use_names:   
      for name in nltk.corpus.names.words():
        self.stopwords[name.lower()] = True

  def debug(self, string):
    sys.stderr.write(string)

  def word_is_interesting(self, word, pos, before_pos, after_pos):
    if len(word) < 3:
      return False
    if word.lower() in self.stopwords:
      return False
    if pos == 'NN' or pos == 'JJ' or pos == 'NNS':
      return True
    if pos == 'VBG': # the pricing, but not he is pricing it
      retval = before_pos in ('AT', 'PP$')
      self.debug("Considering VBG %s: (before_pos == %s) (%s)" % (word, before_pos, retval))
      return retval
    if pos == 'VBD' or pos == 'VBN': # closed doors, but not the door is closed
      retval = after_pos in ('NN', 'NNS')
      self.debug("Considering %s %s: (after_pos == %s) (%s)" % (pos, word, after_pos, retval))
      return retval
    if pos is None:
      return re.match(r"^[A-Za-z_]+$", word)
    else:
      return False

  def build_node_dict(self, sentences):
    node_dict = {}
    uninteresting = set()
    i = 0
    for sentence in sentences:
      for index, (word, pos) in enumerate(sentence):
        before_pos = sentence[index - 1][1] if index > 0 else None
        after_pos = sentence[index + 1][1] if index < len(sentence) - 1 else None

        if self.word_is_interesting(word, pos, before_pos, after_pos):
          node = Node(word.lower(), pos)
          if not word.lower() in node_dict:
            node_dict[word.lower()] = node
          else:
            node_dict[word.lower()].count += 1
        else:
          uninteresting.add(word.lower() + "/" + str(pos))
        i += 1
    self.debug("Interesting words:\n%s\n" % "\n".join([str(x) for x in sorted(node_dict.values(), key=lambda x: x.word)]))
    self.debug("Uninteresting words:\n%s\n" % "\n".join(sorted(uninteresting)))
    return node_dict

  def build_edges(self, sentence, dictionary):
    for i in range(len(sentence)):
      this_word = sentence[i][0].lower()
      if this_word in dictionary:
        this_node = dictionary[this_word]
        j = 1 
        while i + j < len(sentence) and j < self.word_window:
          other_word = sentence[i + j][0].lower()
          if other_word in dictionary:
            other_node = dictionary[other_word] 
            this_node.add_edge(other_node)
            other_node.add_edge(this_node)
          j += 1


  def rank(self, dictionary):
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

  def find_ngram_keywords_sentence(self, final_keywords, sentence):
    phrase = None
    output = set()
    for word, pos in sentence:
      if word in final_keywords:
        if phrase is None:
          phrase = Phrase(final_keywords[word])
        else:
          phrase.append(final_keywords[word])
      else:
        if phrase is not None:
          output.add(phrase)
          phrase = None
    
    if phrase is not None: 
      output.add(phrase)
    return output

  def find_ngram_keywords(self, final_keywords, sentences):
    output = set()
    for sentence in sentences:
      output |= self.find_ngram_keywords_sentence(final_keywords, sentence)
   
    return output 

  def preprocess(self, text):
    out = self.prefilter.filter(text)
    return out

  def _downcase_maybe(self, text):
    if re.match("^[A-Z]+$", text) and len(text) > 1:
      self.debug("downcasing %s" % (text))
      return text.lower()
    else:
      return text

  def preprocess_split(self, sentences):
    output = []
    for sent in sentences:
      output.append(map(self._downcase_maybe, sent))
    return output
 
  def extract_keywords(self, text):
    sentences = nltk.sent_tokenize(text)
    split_sentences = self.preprocess_split([nltk.word_tokenize(x) for x in sentences])
    tagged_sentences = [self.tagger.tag(x) for x in split_sentences]
    dictionary = self.build_node_dict(tagged_sentences)

    for sentence in tagged_sentences:
      self.build_edges(sentence, dictionary)

    dictionary = self.rank(dictionary)

    freq_ranked_nodes = sorted(dictionary.values(), 
                              key=lambda x: x.count, reverse = True)
    ranked_nodes =  sorted(freq_ranked_nodes,
                              key=lambda x: x.score, reverse=True)
    final_dict = {}
    count = 0
    if False:
      max_count = len(ranked_nodes) / 3
      for node in ranked_nodes:
        if count > max_count:
          break
        final_dict[node.word] = node
        count += 1
    else:
      final_dict = dict([[node.word, node] for node in ranked_nodes])

    phrases = self.find_ngram_keywords(final_dict, tagged_sentences) 
    phrases = sorted(phrases, key=lambda x: x.score(), reverse=True)
    return phrases
      

