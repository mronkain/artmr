# Timer2

Timer2 is a simple text-only, fully off-line timing application designed for
small-scale manual competition timing. Heavily based (i.e. shamelessly copied)
on asciimatics contact list demo and inspired by classic DOS utilities.

## Usage

You should have a start list in  `competitors.txt`, format is `bib,name,category`,
one per line. This can be edited while the timer is running, application restart
is needed to refresh the names. See `competitors.txt.example`. Catogries will be 
added automatically.

Use the Start List view to mark actually starting competitors and then continue on
to the Timing screen.

Start the race with the Start (`space` or `s`) button from the Timing screen
and add a new split/finish time with Split (`space` or `s`). Add a competitor bib number
with Edit (`e`). Jump between start list and splits with Tab. Category filter can be
accessed with F2. You can still add competitors while the race is running from the 
start list. Per-competitor start times are not supported though.

Start time and splits are saved on disk so you can quit the tapplication and data
is kept. Times are kept only in whole seconds, more accuracy does not make much
sense in manual timing.

You can export the results with `x`. This creates `[competition name]_[category]_[time].csv` file in
the current directory in format `rank,elapsed time,difference,number,name,category`. Export will 
contain the selected category.

To start a new race, use `--reset` command line option. Previous data is destroyed.
Alternatively, you can take a backup of the `results.db` file and keep a safe copy
of the results.


## Requirements
Tested with python 2.7. Requires asciimatics and sqlalchemy libraries, install
with `pip install -r requirements.txt`.

## TODO
- make a UI for multiple competitions, database already supports this
- change competitor model to be many-to-many via a Participation table
- automatic data export/sync to other services
