# Patch-Spell-Checker
Spell checker for patch file written in C language.

# Usage
```
$ python PatchSpellChecker.py --help
usage: PatctSpellChecker.py [-h] [-d DIR] [-v] [-f FILE] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     Specify directory path where stores dictionary files.
                        "wlist.d" by default.
  -v, --verbose         Verbose output.
  -f FILE, --file FILE  Spell checking target file. '-' by default means input
                        from stdin.
  --debug               Enable debuggin output
```

# How to use
PatchSpellChecker can spell check from stdin or spcified file.

```
-- From stdin
$ git diff | python PatchSpellChecker.py
-- From spcified file
$ python PatchSpellChecker.py -f new_feature.patch
```

# Dictionary file
Dictionary file is the file having ".dict" type suffix that is used for spell checking.
The correctness of spell checking is depend on the amount of words in dictionary files.
PatchSpellChecker can handle multiple dictionary files must be stored in a directory where is specified by -d option. ('wlist.d' by default)
If you want to add some new word (e.g., terminology) you can customise existing dictionary file or add new dictionary file into directory.

The two types of format of dictionary file can be handled by PatchSpellChecker; plain sentence format, one word in one line format.
You can get same dictionary data from following two example.
- plain sentence format
```
PostgreSQL is a powerful, open source object-relational database system. 
```

- One word in one line
```
PostgreSQL
is
a
powerful
open
source
object-relational
database
system
```
