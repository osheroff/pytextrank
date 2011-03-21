#!/usr/bin/env python
# coding=UTF-8

import itertools
import re
import sys
import glob
import numpy
import nltk
import nltk.corpus
import nltk.stem.porter
import textrank.tagger
import textrank.prefilter

porter_stemmer = nltk.stem.porter.PorterStemmer()

DEFAULT_WORD_WINDOW = 3

class Node(object):
    def __init__(self, value):
        self.edges = {}
        self.score = 0.0
        self.new_score = 0.0
        self.count = 1
        self.value = value
    
    def add_edge(self, node, weight=1.0):
        self.edges[node] = (node, weight)

class WordNode(Node):
    def __init__(self, word, pos):
        super(WordNode, self).__init__(word)
        self.pos = pos
    
    def __str__(self):
        return "'%s'<%s>" % (self.value, self.pos)
    
    def __hash__(self):
        return hash(self.value + str(self.pos))

class SentenceNode(Node):
    def __hash__(self):
        return hash(" ".join(self.value))
    
    def __init__(self, orig, split):
        super(SentenceNode, self).__init__(orig)
        self.stemmed_words = set([porter_stemmer.stem(word.lower()) for word in split])
    
    def similarity(self, other_sentence):
        count = 0.0
        for word in self.stemmed_words:
            if word in other_sentence.stemmed_words:
                count += 1
        return count / (numpy.log(len(self.stemmed_words) + 1) + numpy.log(len(other_sentence.stemmed_words) + 1))

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
        return " ".join([x.value for x in self.nodes])
    
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
        if self.do_debug:
            sys.stderr.write(string + "\n")
    
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
                    node = WordNode(word.lower(), pos)
                    if not word.lower() in node_dict:
                        node_dict[word.lower()] = node
                    else:
                        node_dict[word.lower()].count += 1
                else:
                    uninteresting.add(word.lower() + "/" + str(pos))
                i += 1
        self.debug("Interesting words:\n%s\n" % "\n".join([str(x) for x in sorted(node_dict.values(), key=lambda x: x.value)]))
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
    
    
    def rank(self, node_list):
        for node in node_list:
            node.score = 1.0 / len(node_list)
        
        for x in range(100):  
            for node in node_list:
                node.new_score = 0
                for other, weight in node.edges.values():
                    node.new_score += (other.score * weight) / len(other.edges)
                node.new_score *= 0.85
                node.new_score += 1 - 0.85
            for node in node_list:
                node.score = node.new_score
        return node_list
    
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
    
    def preprocess_split_sentence(self, sentence):
        return map(self._downcase_maybe, sentence)
    
    def extract_keywords(self, text):
        sentences = nltk.sent_tokenize(text)
        split_sentences = [self.preprocess_split_sentence(nltk.word_tokenize(x)) for x in sentences]
        tagged_sentences = [self.tagger.tag(x) for x in split_sentences]
        dictionary = self.build_node_dict(tagged_sentences)
        
        for sentence in tagged_sentences:
            self.build_edges(sentence, dictionary)
        
        ranked_nodes = self.rank(dictionary.values())
        
        freq_sorted_nodes = sorted(ranked_nodes, 
        key=lambda x: x.count, reverse = True)
        rank_sorted_nodes =  sorted(freq_sorted_nodes,
        key=lambda x: x.score, reverse=True)
        final_dict = {}
        count = 0
        if False:
            max_count = len(rank_sorted_nodes) / 3
            for node in rank_sorted_nodes:
                if count > max_count:
                    break
                final_dict[node.value] = node
                count += 1
        else:
            final_dict = dict([[node.value, node] for node in rank_sorted_nodes])
        
        phrases = self.find_ngram_keywords(final_dict, tagged_sentences) 
        phrases = sorted(phrases, key=lambda x: x.score(), reverse=True)
        return phrases
    
    
    def tokenize_text_to_lines(self, text):
        return nltk.tokenize.BlanklineTokenizer().tokenize(text)
    
    def tokenize_lines_to_sentences(self, lines):
        sentence_list = []
        for line in lines:
            sentence_list.extend(nltk.sent_tokenize(line))
        
        return sentence_list 
    
    def node_from_sentence(self, sentence):
        split = self.preprocess_split_sentence(nltk.word_tokenize(sentence))
        return SentenceNode(sentence, split)
    
    def nodes_from_text(self, text):
        lines = self.tokenize_text_to_lines(text)
        sentences = self.tokenize_lines_to_sentences(lines)
        
        nodes = []
        for sentence in sentences:
            nodes.append(self.node_from_sentence(sentence))
        
        return nodes
    
    def extract_sentences(self, text, sentence_count):
        nodes = self.nodes_from_text(text)
        
        for i in range(len(nodes)):
            this_node = nodes[i]
            for j in range(i + 1, len(nodes)):
                that_node = nodes[j]
                similarity = this_node.similarity(that_node)
                if similarity > 0.0:
                    this_node.add_edge(that_node, similarity)
                    that_node.add_edge(this_node, similarity)
        
        ranked = self.rank(nodes)
        rank_sorted_nodes =  sorted(ranked, key=lambda x: x.score, reverse=True)
        for sentence in rank_sorted_nodes: 
            print sentence.value
