# Timer2

Timer2 is a simple text-only, fully off-line timing application designed for
small-scale manual competition timing. Heavily based (i.e. shamelessly copied)
on asciimatics contact list demo and inspired by classic DOS utilities.

## Usage

Use the Start List view on call-up to get an actual start list.

Start the race with the Start (`space` or `s`) button from the Timing screen
and add a new split/finish time with Split (`space` or `s`). Add a competitor bib number
with Edit (`e`).

Start time and splits are saved on disk so you can quit the application and data
is kept. Times are kept only in whole seconds, more accuracy does not make much
sense in manual timing.

Competitor names should be added in advance from `competitors.txt`, format is `bib,name`,
one per line. This can be edited while the timer is running, application restart
is needed to refresh the names. See `competitors.txt.example`.

Data can be export to a csv file with `x`. This creates `export.csv` file in
the current directory in format `rank,bib,name,elapsed time,real time`. Make sure
you've set the bibs and names correctly as otherwise the data is not very good.

To start a new race, use `--reset` command line option. Previous data is destroyed.
Alternatively, you can take a backup of the `competitors.db` file and keep a safe copy
of the results.

## Requirements
Tested with python 2.7. Requires asciimatics and sqlalchemy libraries, install
with `pip install -r requirements.txt`.

## TODO
- fix export
- make a UI for multiple competitions, database already supports this
- change competitor model to be many-to-many via a Participation table
- automatic data export/sync to other services
