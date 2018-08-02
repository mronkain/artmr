# artmr

artmr is a simple text-only, fully off-line timing application designed for
small-scale manual competition timing. Heavily based (i.e. shamelessly copied)
on asciimatics contact list demo and inspired by classic DOS utilities.

## Installation

Install with `pip install artmr`. Currently tested only on Linux and Mac.
Start the program with `artmr`. If you encounter errors about "Unknown locale: UTF-8, add 
these lines to `~/.bash_profile`:
```
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

A (colour, UTF-8) terminal window of > 100 columns is recommended.

## Usage

Load a start list with the command line option `-c`, format is `number,name,category,team`,
one per line. You can also load a start list with F3 from the start list screen.
Names and numbers should be unique and categories are optional but free-form. See
`competitors.example.txt` for an example file.

Use the Start List view to mark actually starting competitors and then continue on
to the Timing screen.

Start the race with the Start (`space` or `s`) button from the Timing screen
and add a new split/finish time with Split (`space` or `s`). Add a competitor bib number
with Edit (`e`). Jump between start list and splits with Tab. Category filter can be
accessed with F2. You can still add competitors while the race is running from the 
start list. All competitors will have the same start time.

Start time and splits are saved on disk so you can quit the application and data
is kept. Times are rounded to whole seconds.

You can export the results with `x`. This creates `[competition name]_[category]_[time].csv` file in
the current directory in format `rank,elapsed time,difference,number,name,category,team`. Export will 
contain the selected category.

To start a new race, use `--reset` command line option. Previous data is destroyed.
Alternatively, you can take a backup of the `~/.artmr/results_1.db` file and keep a safe copy
of the results.

## Screenshots

![Start list](https://flexer.430am.fi/artmr/start_list.png)

![splits](https://flexer.430am.fi/artmr/splits.png)


## TODO
- splash screen
- make a UI for multiple competitions, database already supports this
- support for lap timing
- change competitor model to be many-to-many via a Participation table
- Windows support
- automatic data export/sync to other services

