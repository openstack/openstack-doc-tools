# retf.py

This script applies a set of regular expressions onto a set of files
to automatically identify and fix typographical errors.

## What does RETF mean?

RETF means RegExTypoFix or Regular Expression Typographical error Fixer
and is a set of regular expressions to find and fix common misspellings
and grammatical errors.

The regular expressions are available at
https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/Typos.

## Usage

There are two ways to define the set of files. First you can simply add
single files using the parameter ```--file```.

```$ ./retf.py --file path/to/file1 path/to/file2 path/to/file3```

Also you can specify paths using the parameter ```--path``` that should be
scanned for files.

```$ ./retf.py --path path/with/files/1 path/with/files/2```

To not use all files inside the specified paths it's possible to filter
by the file extension.

```$ ./retf.py --path path/with/files --extension xml txt rst```

It's possible to use the parameters ```--path``` and ```--file``` together.

By default the script will only check for findings in all specified files.

To automatically write back resolved findings add the parameter
```--write-changes```. Findings will then be written to a copy with
the ending ```.retf```.

To fix findings directly in the files add the parameter
```--in-place```. Findings will than be fixed directly in the files. A backup file
with the ending ```.orig``` will be created. To disable backups add the
paramter ```--no-backup```.

To only check if there are findings inside the defined set of files add

To download the latest RETF rules from Wikipedia use the parameter ```--download```.

## Needed Python modules

* beautifulsoup4 / bs4 (https://pypi.python.org/pypi/beautifulsoup4)
* glob2 (https://pypi.python.org/pypi/glob2)
* pyyaml (https://pypi.python.org/pypi/pyaml)
* regex (https://pypi.python.org/pypi/regex)
* six (https://pypi.python.org/pypi/six)

To install the needed modules you can use pip or the package management system included
in your distribution. When using the package management system maybe the name of the
packages differ. When using pip it's maybe necessary to install some development packages.
For example on Ubuntu 14.04 LTS you have to install ```libyaml-dev``` for ```pyyaml```
and ```python-dev``` for ```regex```.

```
$ pip install beautifulsoup4
$ pip install glob2
$ pip install pyyaml
$ pip install regex
$ pip install six
```
