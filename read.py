#!/usr/bin/env python2.7
"""
This script reads a CSV file containing a large number of emails and parses
each for common language and tone.
"""

import htmlentitydefs
import codecs
import argparse
import csv
import json
import re
import string
import sys

from collections import defaultdict

import nltk
from nltk.tag.simplify import simplify_tag
from nltk.tokenize import TreebankWordTokenizer

tokenizer = {
    'name': 'treebank',
    'obj': TreebankWordTokenizer(),
}

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
    """
    Open the CSV file and tokenize the texts according to a number of
    possible tokenizers.
    """

    reader = csv.reader(open('greece.csv'))

    full_text = ''
    for row in reader:
        rowtext = unescape(row[1].decode('cp1252'))
        full_text = str.join('\n', [full_text, rowtext])

    tokens = tokenizer['obj'].tokenize(full_text)
    with open(tokenizer['name'] + '.json', 'w') as file_:
        json.dump(tokens, file_, indent=2)


def open_and_store():
    """Dump the csv to rows of email bodies."""

    reader = csv.DictReader(open('greece.csv'))
    rows = []
    for row in reader:
        rows.append((row['id'], unescape(row['comments'].decode('cp1252'))))

    p, n = 0, 0
    trained = {}
    while not (p >= 5 and n >= 5):
        id_, line = random.choice(rows)
        if id_ in trained:
            continue

        print(line)

        key = ''
        while key not in ['p', 'n', 's']:
            key = raw_input('(p/n/s)? ')

        if not key == 's':
            trained[id_] = (line, key)
            if key == 'p':
                p += 1
            else:
                n += 1

    with open('training.json', 'w') as train_file:
        json.dump(trained, train_file, indent=2)

    return trained


def parse_and_simplify():
    """
    Take the tokenized text and tag each word according to what purpose it
    fills in the sentence.  This is done both in a detailed and simplified
    manner, for comparison.
    """

    with open(tokenizer['name'] + '.json') as file_:
        tokens = json.load(file_)
    tagged = nltk.pos_tag(tokens)
    print("Tagged")
    simplified = [(word, simplify_tag(tag)) for word, tag in tagged]
    print("Simplified")

    with open(tokenizer['name'] + '_parsed.json', 'w') as file_:
        json.dump(tagged, file_, indent=2)
    with open(tokenizer['name'] + '_simple.json', 'w') as file_:
        json.dump(simplified, file_, indent=2)

    print(tokenizer['name'] + ' has been parsed')


def pull_from_json(parse_type, simple=False):
    """Re-read stored tagged information."""
    filename = parse_type + ('_simple' if simple else '_parsed') + '.json'
    with open(filename) as file_:
        return json.load(file_)


def clean_up_tokens(tokens):
    """Take tagged words and filter out nonessential or common words,"""
    desired_tags = ['J', 'N', 'V']
    words = nltk.FreqDist([w[0].lower().rstrip(string.punctuation) for w in tokens
                           if w[1] in desired_tags and len(w[0]) >= 7])

    return words


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perfom analysis on a ' + \
        'collection of text emails')
    parser.add_argument('-g', dest='token', action='store_true',
                       help='(re)generate the token set')
    parser.add_argument('-p', dest='parse', action='store_true',
                       help='(re)parse the token set')
    parser.add_argument('-t', dest='train', action='store_true',
                       help='(re)train the machine learner on the parsed tokens')

    args = parser.parse_args()

    if args.token:
        open_and_tokenize()
        print("Tokenized")
    if args.parse:
        parse_and_simplify()
        print("Parsed")
    if args.train:
        print("Trained")
        trained = open_and_store()
    else:
        with open('training.json') as train_file:
            trained = json.load(train_file)

    texts = []
    for (words, sentiment) in trained.values():
        words_filtered = [e.lower().strip(string.punctuation)
                          for e in words.split() if len(e) >= 5]
        texts.append((words_filtered, sentiment))

    features = set()
    for words, sentiment in texts:
        features.update(words)

    def extract_features(document):
        words = set(document)
        feature_dict = {}
        for word in features:
            feature_dict['contains(%s)' % word] = (word in words)
        return feature_dict

    training_set = nltk.classify.util.apply_features(extract_features, texts)
    classifier = nltk.NaiveBayesClassifier.train(training_set)
    classifier.show_most_informative_features(10)

    reader = csv.DictReader(open('greece.csv'))
    p, n = 0, 0
    for row in reader:
        if row['id'] in trained:
            continue

        row_text = unescape(row['comments'].decode('cp1252'))
        row_list = [e.lower().strip(string.punctuation)
                    for e in row_text.split() if len(e) >= 5]
        class_ = classifier.classify(extract_features(row_list))
        if class_ == 'p':
            p += 1
            class_ = 'polite'
            #if p % 20 == 0:
            #    print('\n' + row['id'] + ' ' + class_ + ' v')
            #    print(row_text)
        else:
            n += 1
            class_ = 'aggressive'

    print((p, n))
