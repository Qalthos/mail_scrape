#!/usr/bin/env python2

import htmlentitydefs
import codecs
import csv
import json
import re
import string
import sys

from collections import defaultdict

import nltk
from nltk.tag.simplify import simplify_tag
from nltk.tokenize import WhitespaceTokenizer, WordPunctTokenizer, TreebankWordTokenizer

token_keys = ['whitespace', 'wordpunct', 'treebank']

def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def open_and_tokenize():
    reader = csv.reader(open('greece.csv'))

    full_text = ''
    for row_index, row in enumerate(reader):
        rowtext = unescape(row[1].decode('cp1252'))
        full_text = str.join('\n', [full_text, rowtext])

    tokenizers = {'whitespace': WhitespaceTokenizer(),
                  'wordpunct': WordPunctTokenizer(),
                  'treebank': TreebankWordTokenizer(),
                 }

    token_dict = dict()
    for filename, tokenizer in tokenizers.items():
        token_dict[filename] = tokenizer.tokenize(full_text)
        with open(filename + '.json', 'w') as file_:
            json.dump(token_dict[filename], file_)


def parse_and_simplify():
    for filename in token_keys:
        with open(filename + '.json') as file_:
            tokens = json.load(file_)
        tagged = nltk.pos_tag(tokens)
        print("Tagged")
        simplified = [(word, simplify_tag(tag)) for word, tag in tagged]
        print("Simplified")

        with open(filename + '_parsed.json', 'w') as file_:
            json.dump(tagged, file_)
        with open(filename + '_simple.json', 'w') as file_:
            json.dump(simplified, file_)

        print(filename + ' has been parsed')


def pull_from_json(parse_type, simple=False):
    filename = parse_type + ('_simple' if simple else '_parsed') + '.json'
    with open(filename) as file_:
        return json.load(file_)


def clean_up_tokens(tokens):
    desired_tags = ['J', 'N', 'V']
    words = nltk.FreqDist([w[0].lower().rstrip(string.punctuation) for w in tokens
                           if w[1] in desired_tags and len(w[0]) >= 7])

    return words


if __name__ == '__main__':
    if 'retoken' in sys.argv:
        open_and_tokenize()
        print("Tokenized")

    if 'reparse' in sys.argv:
        parse_and_simplify()

    for parse_type in token_keys:
        print(parse_type)
        words = clean_up_tokens(pull_from_json(parse_type, True))
        words.tabulate(30)
        words.plot(30)
