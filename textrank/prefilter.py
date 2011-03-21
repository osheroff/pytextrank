import re

class Prefilter:
    def __init__(self):
        self.replacement_patterns = [
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
            ( r'https?://\S+\s', ' '),
            ( r'\'(\w+)\'', '\g<1>'),
            ( r'"(\w+)"', '\g<1>')
        ]

        self.patterns = [(re.compile(regex, re.I), repl) 
            for (regex, repl) in self.replacement_patterns]

    def filter(self, text):
        s = text
        for (pattern, repl) in self.patterns:
            (s, count) = re.subn(pattern, repl, s)
        return s

