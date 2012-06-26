#!/usr/bin/env python2

import htmlentitydefs
import codecs
import csv
import re

from collections import defaultdict


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

mentions = ['Luis Recio', 'Wesley Helm', 'Brandon Teng', 'Tyler Warren',
            'Josh Slesak', 'Bryce Helm', 'pastebin', 'youtube', '4chan', 'god',
            '!!!', 'kill', 'reddit']
hits = [0] * len(mentions)
texts = defaultdict(list)


for row_index, row in enumerate(reader):
    for index, name in enumerate(mentions):
        rowtext = unescape(row[1].decode('cp1252'))
        if name.lower() in rowtext.lower():
            hits[index] += 1
            texts[name].append(rowtext + '\n\n')

print('Out of %d total emails...' % row_index)
for index, name in enumerate(mentions):
    print('%s was mentioned %d times' % (name, hits[index]))
    with open(name, 'w') as namefile:
        for line in texts[name]:
            namefile.write(line.encode('utf-8'))
