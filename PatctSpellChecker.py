#!/bin/env python

#
# spell_check.py
#
# Simple spell checker for diff(patch) file written in C language.
#
# Usage:
# $ cat *.diff | python spell_check.py -d wlist.d/
#  or
# $ git diff | python spell_check.py -d wlist.d/
#
import argparse
import re
import collections
import glob
import sys
import os

# Const values
WLIST_DIR = os.getenv("WLIST_DIR", default="wlist.d")
WRONG_WORD = '\033[92m' # Light green
ENDC = '\033[0m'

pattern_diff_add = r'^\+.*'
pattern_comment = r'\/\*.*\*\/'
pattern_alphabet = r'[a-z][a-z\_\-\']+[a-z]'
p_d_a = re.compile(pattern_diff_add)
p_c = re.compile(pattern_comment)
p_a = re.compile(pattern_alphabet)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dir',
                    help="Specify directory path where stores dictionary files. WLIST_DIR environemnt variable by default.",
                    default=WLIST_DIR)
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose output.')
parser.add_argument('-f', '--file',
                    help="Spell checking target file. \'-\' by default means input from stdin.",
                    default='-')
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debuggin output')
parser.add_argument('-s', '--source-file',
                    action='store_true',
                    help='Focus on whole source file written in C or C++. False by default.',
                    default=False)
parser.add_argument('-w', '--show-word',
                    action='store_true',
                    help='Show only wrong word without line.',
                    default=False)
args = parser.parse_args()
path = args.dir
verbose = args.verbose
debug = args.debug
file = args.file
source_file = args.source_file
show_word = args.show_word

class SpellChecker():
    #
    # Initialize SpellChecker instanse.
    # dict_dir : Directory patch where stores dictionary files.
    # keyID : Unique word ID.
    # td : trgm dictionary that is hash map between trgm and keyID.
    # wd : word dictionary that is hash map between keyID and word.
    # known_word : pure word dictionary that word are defined in.
    #
    def __init__(self, path):
        self.dict_dir = path
        self.keyID = 0
        self.td = collections.defaultdict(lambda: set()) # Dictionary for trgm.  { "trgm" : "keyID" }
        self.wd = {} # Dictionary for keyID, { "keyID" : "word" }
        self.known_word = set()

    #
    # Loading dictionary files and store each word into my dictionary.
    # Following formats of dictionary file are allowed;
    #   - Normal sentence (e.g. "This is a pen," generates 4 words without period)
    #   - One word in one line
    #
    def prepare(self):
        files = glob.glob(self.dict_dir + "/*.dict")
        for file in files:
            fp = open(file, 'r')

            # Process each line
            for line in fp:

                if line == '\n':
                    continue

                # Find all words from line.
                words = p_a.findall(line)

                # Consider each wrod
                for w in words:
                    w = w.lower()
                    n = len(w)

                    # Register word to wd dictionary.
                    # Note that keyID is unique the primary key, so it's not duplicated.
                    self.wd[self.keyID] = w

                    # Register word to known_word.
                    self.known_word.add(w)

                    # word that length < 3
                    if n < 3:
                        self.td[w].add(str(self.keyID))

                        # Extract each word into trgm
                    else:
                        ww = ' ' + w + ' '
                        trgms = [ ww[i] + ww[i+1] + ww[i+2] for i in range(n) ]
                        for elem in trgms:
                            self.td[elem].add(str(self.keyID))

                            # Increment keyID
                            self.keyID += 1
    #
    # Show dictionary information.
    #
    def print_dict_info(self):
        print "------ Dictonary Information -------"
        print "knows_word %d words" % len(self.known_word)
        print "wd %d words" % len(self.wd)
        print "td %d words" % len(self.td)
        print "------------------------------------"

    #
    # Show known_words for debugging
    def show_known_words(self):
        print self.known_word

    #
    # Judge if given word is correct.
    #
    # We judge word with following steps.
    # 1. Check if given word is in known_words.
    # ....
    #
    def isCorrect(self, word):
        if word in self.known_word:
            return True
        else:
            return False

# Create SpellChecker intanse
sp = SpellChecker(path)
sp.prepare()
if verbose:
    sp.print_dict_info()
if debug:
    sp.show_known_words()

# Function definition
def check_words(words, line, lineno):
    for word in words:
        if not sp.isCorrect(word):
            # If -w (--show-word) is specified, we show only the suspicious word.
            if show_word:
                print "%s%s%s" % (WRONG_WORD, word, ENDC)
            else:
                print "\"%s%s%s\" might be wrong at line %d." % (WRONG_WORD, word, ENDC, lineno)
                print "\t\"%s\"" % line
#
# Check multiple lines if each word is correct.
# If doubtful word is detected, we check it using some approaches in
# check_words() function.
#
def check_lines(lines):
    in_comment = False
    lineno = 0

    for line in lines:
        lineno += 1

        # Skip not-interested-in line
        if not source_file and not p_d_a.match(line):
            continue

        # 'line' variable is the line removed new line(\n).
        line = re.sub(r'[\n\"]', ' ', line).lower()

        # One line comment
        if line.find('/*') > -1 and line.find('*/') > -1:
            words = p_a.findall(line)
            check_words(words, line, lineno)
            continue

        if line.find('/*') > -1:
            in_comment = True
            continue

        if line.find('*/') > -1:
            in_comment = False
            continue

        # Multi line comment
        if in_comment:
            words = p_a.findall(line)
            check_words(words, line, lineno)

#
# Main Routine
#

#
# Process each input lines from stdin or specified file. We are intereted in
# only added and comment line in patch file. Once we detect it we check if it
# is correct word using dictionary.
#
if file == '-':
    lines = sys.stdin.readlines()
else:
    lines = open(file, 'r')
check_lines(lines)
