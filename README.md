# Timer2

Timer2 is a simple text-only, filly offline timing application designed for
small-scale manual competition timing. Heavily based (i.e. shamelessly copied)
on asciimatics contact list demo and inspired by classic DOS utilities.

## Usage

Start the race with the Start (`space` or `s`) button and add a new split/finish time with Split
(`space` or `s`). Add a competitor bib number with Edit (`e`).

Start time and splits are saved on disk so you can quit the application and data
is kept.

Competitors can be added in advance from `competitors.txt`, format is `bib,name`,
one per line.

To start a new race, use `--reset` command line option. Previous data is destroyed.

## Requirements
Tested with python 2.7. Requires asciimatics library, install with `pip install asciimatics`


## TODO
- make a competition model that start time can be saved to database
- read names better into database
- data export to csv
- automatic data export/sync to other services
