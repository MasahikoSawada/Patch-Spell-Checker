# Patch-Spell-Checker
Customizable simple spell checker for patch file written in C or C++ language.

# Usage
```
$ ./PatchSpellChecker.py --help
usage: PatctSpellChecker.py [-h] [-d DIR] [-v] [-f FILE] [--debug]
optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     Specify directory path where stores dictionary files.
                        WLIST_DIR environemnt variable by default.
  -v, --verbose         Verbose output.
  -f FILE, --file FILE  Spell checking target file. '-' by default means input
                        from stdin.
  --debug               Enable debuggin output
  -s, --source-file     Focus on whole source file written in C or C++. False
                        by default.
  -w, --show-word       Show only wrong word without line.
```

# How to use
PatchSpellChecker can spell check from stdin or specified file.
If patch file has doubtful word, PathSpellChecker emit suspicious word, the line number and line that has it.

```
-- Set up
$ export WLIST_DIR=/path/to/dictionary_dir
-- From stdin
$ git diff | python PatchSpellChecker.py
"privent" might be wrong at line 10. May be "prevent" ?
"tulpe" might be wrong at line 12. May be "tuple" ?
"relaesing" might be wrong at line 13. May be "releasing" ?
"xl_heap_lock" might be wrong at line 13. May be "headlock" ?
"pupose" might be wrong at line 14. May be "purpose" ?
"appaer" might be wrong at line 16. May be "appear" ?
"celar" might be wrong at line 28. May be "clear" ?
-- Or from spcified file
$ python PatchSpellChecker.py -f new_feature.patch
```

The above "xl_heap_lock" is appeared as suspicious word. To solved it, you can define this word in dictionary file. (see below)

# Dictionary file
Dictionary file is the file having ".dict" type suffix that is used for spell checking.
The correctness of spell checking is depend on the amount of words in dictionary files.
PatchSpellChecker can handle multiple dictionary files must be stored in a directory.
The dictionary directory storing dictionary file is found by following priority.

1. Directory spcified by -d option
2. WLIST_DIR environment variable.
3. './wlist.d' directory.

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
