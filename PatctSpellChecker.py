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
LINE_WORD = '\033[91m'
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
parser.add_argument('-D', '--docs',
                    action='store_true',
                    help='Focus on document rather than C or C++ file. False by default.',
                    default=False)
args = parser.parse_args()
path = args.dir
verbose = args.verbose
debug = args.debug
file = args.file
source_file = args.source_file
show_word = args.show_word
docs = args.docs

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
                        trgms = self.extract_trgm(w)
                        for elem in trgms:
                            self.td[elem].add(str(self.keyID))

                    # Increment keyID
                    self.keyID += 1

    #
    # Extract it into trigram, and return trigram list.
    #
    def extract_trgm(self, word):
        n = len(word)
        ww = ' '  + word + ' '
        trgms = [ ww[i] + ww[i+1] + ww[i+2] for i in range(n) ]
        return trgms

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
            return None
        else:
            # Prepare for judgement.
            alphabet = 'abcdefghijklmnopqrstuvwxyz'
            n = len(word)
            edit_set = set(
                [word[0:i]+word[i+1:] for i in range(n)] +
                [word[0:i]+word[i+1]+word[i]+word[i+2:] for i in range(n-1)] +
                [word[0:i]+c+word[i+1:] for i in range(n) for c in alphabet] +
                [word[0:i]+c+word[i:] for i in range(n+1) for c in alphabet])

            #
            # If this word is not listed in known_word, we next search it
            # using trgm similarity.
            #
            trgms = self.extract_trgm(word)

            #
            # We assumed that first 2 char might be correct in most cases.
            # keyid_set stored the id for key that has same trgm part.
            #
            keyid_set = set()
            for elem in trgms:
                #keyid_set = keyid_set | (self.td[trgms[0]] & self.td[elem])
                keyid_set = keyid_set | self.td[elem]

            #
            # First, we try to judge this word using distance between
            # this word and other word. Using ids in keyid_set, we try to
            # compare between id's key and word having 1 distence such as
            # 'think' <-> 'thank', 'think' <-> 'htink'...
            #
            for elem in keyid_set:
                if self.wd[int(elem)] in edit_set:
                    return self.wd[int(elem)]

            #
            # Second, we judge this word using word similarity. calc_similarity
            # function returns similarity value between word and candidate word.
            # The word having maximum value will be selected as similar_word.
            #
            similarity_set = []
            tmp_sim = 0
            similar_word = ""
            for elem in keyid_set:
                similarity = float(self.calc_similarity(word, self.wd[int(elem)]))
                if tmp_sim < similarity:
                    tmp_sim = similarity
                    similar_word = self.wd[int(elem)]

            return similar_word

    # Calculate similarity between w1, w2.
    def calc_similarity(self, w1, w2):
        t1 = self.extract_trgm(w1)
        t2 = self.extract_trgm(w2)
        len_t1 = len(t1)
        len_t2 = len(t2)
        matched = 0
        ret = 0.0

        for e1 in t1:
            for e2 in t2:
                if e1 == e2:
                   matched += 1

        ret = float(matched) / float((len_t1 + len_t2))
        return ret

##########################
# Function definition
##########################
def check_words(words, line, lineno):
    for word in words:
        correct_word = sp.isCorrect(word)
        if not correct_word is None:
            # If -w (--show-word) is specified, we show only the suspicious word.
            if show_word:
                print "%s" % (word)
            else:
                print "\"%s%s%s\" might be wrong at line %s%d%s. May be \"%s%s%s\" ?" % (WRONG_WORD, word, ENDC, LINE_WORD, lineno, ENDC, WRONG_WORD, correct_word, ENDC)
                if verbose:
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

        if not docs:
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
        else: # Parsing doc file
            # Skip no-interested-in line
            if not source_file and not p_d_a.match(line):
                continue

            # 'line' variable is the line removed new line(\n).
            line = re.sub(r'[\n\"]', ' ', line).lower()

            words = p_a.findall(line)
            check_words(words, line, lineno)

###########################
# Main Routine
###########################

#
# Process each input lines from stdin or specified file. We are intereted in
# only added and comment line in patch file. Once we detect it we check if it
# is correct word using dictionary.

#
# Create SpellChecker intanse
#
sp = SpellChecker(path)
sp.prepare()
if verbose:
    sp.print_dict_info()
if debug:
    sp.show_known_words()

if file == '-':
    lines = sys.stdin.readlines()
else:
    lines = open(file, 'r')
check_lines(lines)
