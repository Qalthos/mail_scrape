#!/usr/bin/env python2

import htmlentitydefs
import codecs
import csv
import re

from collections import defaultdict

import nltk


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


reader = csv.reader(open('greece.csv'))

mentions = {'names': ['Luis Recio', 'Wesley Helm', 'Brandon Teng', 'Tyler Warren',
                      'Josh Slesak', 'Bryce Helm', 'Wes Helm'],
            'anon': ['pastebin', '4chan', 'reddit'],
            'god': ['god'],
            'angry': ['!!!', 'kill', 'shit', 'fuck', 'douche'],
            'youtube': ['youtube', 'youtu.be'],
            'polite': ['apologize', 'sorry'],
           }
hits = defaultdict(int)
texts = defaultdict(list)

full_text = ''


for row_index, row in enumerate(reader):
    rowtext = unescape(row[1].decode('cp1252'))
    full_text = str.join('\n', [full_text, rowtext])
    #for key, keywords in mentions.items():
    #    #
    #    for word in keywords:
    #        if word.lower() in rowtext.lower():
    #            hits[key] += 1
    #            texts[key].append(rowtext + '\n\n')
    #            break
    #    else:
    #        texts['!' + key].append(rowtext + '\n\n')

tokens = nltk.wordpunct_tokenize(full_text)
text = nltk.Text(tokens)
words = nltk.FreqDist([w.lower() for w in text])
for token in [',', '-', '!', '"', ':', "'",
              'http', '://', 'www', '.', 'com', '/', '?', '=', '&',
              'a', 'i', 's', 't', 'v',
              'am', 'an', 'as', 'at', 'be', 'by', 'do', 'if', 'in', 'is', 'it',
              'my', 'of', 'on', 'to',
              'all', 'and', 'are', 'but', 'for', 'her', 'not', 'the', 'was',
              'who', 'you',
              'from', 'have', 'just', 'them', 'they', 'this', 'that', 'what',
              'will', 'with', 'your',
              'about', 'their', 'these', 'those', 'would',
              'l93waqnpqwk',]:
    words.pop(token)

#text.generate()
words.tabulate(20)
words.plot(20)


#print('Out of %d total emails...' % row_index)
#for key in texts:
#    print('%s was mentioned %d times' % (key, hits[key]))
#    with open(key, 'w') as namefile:
#        for line in texts[key]:
#            namefile.write(line.encode('utf-8'))
