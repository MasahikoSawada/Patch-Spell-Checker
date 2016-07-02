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
import sys
import os

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dir', help="Specify directory path where stores dictionary files")
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
parser.add_argument('--debug', action='store_true', help='Enable debuggin output')
args = parser.parse_args()
path = args.dir
verbose = args.verbose
debug = args.debug

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
        files = os.listdir(self.dict_dir)
        for file in files:
            fp = open(self.dict_dir + file, 'r')

            # Process each line
            for line in fp:

                if line == '\n':
                    continue

                words = re.sub(r'[,.\n\"\!\;\:]', '', line).split(' ')

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
def check_words(words):
    for word in words:
        if not sp.isCorrect(word):
            print "\"%s\" might be wrong" % word
#
# Main Routine
#
raw_input = sys.stdin.readlines()
pattern_diff_add = r'^\+.*'
pattern_comment = r'\/\*.*\*\/'
pattern_alphabet = r'[a-z\_\-\']+'
p_d_a = re.compile(pattern_diff_add)
p_c = re.compile(pattern_comment)
p_a = re.compile(pattern_alphabet)
in_comment = False

#
# Process each input lines from stdin. We are intereted in only added and
# comment line in patch file. Once we detect it we check if it is correct word
# using dictionary.
#
for line in raw_input:

    # Skip empty line
    if not p_d_a.match(line):
        continue
    line = re.sub(r'\n', '', line).lower()

    # One line comment
    if line.find('/*') > -1 and line.find('*/') > -1:
        words = p_a.findall(line)
        check_words(words)
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
        check_words(words)
