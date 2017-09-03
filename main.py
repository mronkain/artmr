#!/usr/bin/python
from asciimatics.widgets import Frame, MultiColumnListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent

from time import time, strftime, gmtime, localtime

import os.path
import sys
import sqlite3
import logging
import csv

version = '0.3'

class CompetitorModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect('competitors.db')
        self._db.row_factory = sqlite3.Row

        # Create the basic competitor table.
        self._db.cursor().execute('''
            CREATE TABLE if not exists competitors(
                id INTEGER PRIMARY KEY,
                name TEXT DEFAULT "",
                bib TEXT DEFAULT "",
                finish_time REAL)
        ''')
        self._db.commit()

        # Current competitor when editing.
        self.current_id = None

    def add(self, competitor):
        self._db.cursor().execute('''
            INSERT INTO competitors(finish_time)
            VALUES(:finish_time)''',
                                  competitor)
        self._db.commit()

    def get_summary(self):
        list = self._db.cursor().execute(
            "SELECT finish_time, bib, name, id from competitors ORDER BY finish_time").fetchall()
        rows = []
        for x in list:
            option = (
                [
                    strftime('%H:%M:%S', gmtime(x['finish_time'])),
                    x['bib'],
                    get_name(x['bib'])
                ],
                x['id']
            )

            rows.append(option)

        return rows

    def get_competitor(self, competitor_id):
        return self._db.cursor().execute(
            "SELECT * from competitors where id=?", [str(competitor_id)]).fetchone()

    def get_current_competitor(self):
        if self.current_id is None:
            return {}
        else:
            return self.get_competitor(self.current_id)

    def update_current_competitor(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            self._db.cursor().execute('''
                UPDATE competitors SET name=:name, bib=:bib WHERE id=:id''',
                                      details)
            self._db.commit()

    def delete_competitor(self, competitor_id):
        self._db.cursor().execute('''
            DELETE FROM competitors WHERE id=:id''', {"id": competitor_id})
        self._db.commit()

    def get_export(self):
        list = self._db.cursor().execute(
                "SELECT finish_time, bib from competitors ORDER BY finish_time").fetchall()
        return list

class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version)
        # Save off the model that accesses the competitors database.
        # logging.basicConfig(filename='example.log',level=logging.INFO)

        self._model = model
        self._start_time = None
        self._last_frame = 0
        self.read_state()
        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['30%','30%', '30%'],
            model.get_summary(),
            name="competitors",
            on_change=self._on_pick,
            titles=['Finishing time', 'Bib', 'Name'])
        self._edit_button = Button("Edit", self._edit)
        self._start_button = Button("Start", self._start)
        self._quit_button = Button("Quit", self._quit)
        self._split_button = Button("Split", self._add)

        self._start_button.disabled = (self._start_time != None)
        self._split_button.disabled = (self._start_time == None)

        layout = Layout([100], fill_frame=True)

        self.add_layout(layout)
        self._time_label = Text("Time:")
        self._time_label.value = "NOT STARTED"
        self._time_label.disabled = True

        layout.add_widget(self._time_label)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._start_button, 0)
        layout2.add_widget(self._split_button, 1)
        layout2.add_widget(self._edit_button, 2)
        layout2.add_widget(self._quit_button, 3)

        self.fix()
        self._on_pick()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code

            if key == ord('s') or key == 32:
                self._add()
            elif key == ord('e'):
                self._edit()
            elif key == ord('x'):
                self._export()

            else:
                super(ListView, self).process_event(event)
        else:
            super(ListView, self).process_event(event)

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._model.get_summary()
        self._model.current_id = None

    def _add(self):
        if self._start_time == None:
            self._start()
            return

        self._model.current_id = None
        details = {'finish_time': time() - self._start_time}

        self._model.update_current_competitor(details)
        self._reload_list()

    def _edit(self):
        self.save()
        self._model.current_id = self.data["competitors"]
        raise NextScene("Edit competitor")

    def _delete(self):
        self.save()
        self._model.delete_competitor(self.data["competitors"])
        self._reload_list()

    def _start(self):
        if self._start_time == None:
            self._start_time = time()
            self.save_state()

        self._start_button.disabled = True
        self._split_button.disabled = False

    def _update(self, frame_no):
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            if self._start_time != None:
                self._time_label.value = strftime('%H:%M:%S', gmtime(time() - self._start_time))

        super(ListView, self)._update(frame_no)

    def read_state(self):
        if os.path.isfile('state.dat'):
            f = open('state.dat', 'r')
            self._start_time = float(f.read())
            f.close()

    def save_state(self):
        f = open('state.dat', 'w')
        f.write(str(self._start_time))
        f.close()

    def _export(self):
        list = self._model.get_export()

        with open('export.csv', 'wb') as f:
            writer = csv.writer(f)

            writer.writerow(['rank', 'bib', '(((Start time)))',
                '00:00:00',
                strftime("%Y-%m-%d %H:%M:%S %Z", localtime(self._start_time))])
            rank = 1
            for l in list:
                writer.writerow([
                    rank,
                    l['bib'],
                    get_name(l['bib']).encode('utf-8'),
                    strftime('%H:%M:%S', gmtime(l['finish_time'])),
                    strftime("%Y-%m-%d %H:%M:%S %Z", localtime(self._start_time + l['finish_time']))
                ])
                rank += 1

    @property
    def frame_update_count(self):
        # Refresh once every 2 seconds by default.
        return 20

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


class CompetitorView(Frame):
    def __init__(self, screen, model):
        super(CompetitorView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Competitor Details",
                                          reduce_cpu=True)
        # Save off the model that accesses the competitors database.
        self._model = model

        # Create the form for displaying the list of competitors.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        #layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Bib:", "bib"))
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(CompetitorView, self).reset()
        self.data = self._model.get_current_competitor()

    def _ok(self):
        self.save()
        self._model.update_current_competitor(self.data)
        raise NextScene("Main")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == 10:
                self._ok()
            else:
                super(CompetitorView, self).process_event(event)
        else:
            super(CompetitorView, self).process_event(event)


    @staticmethod
    def _cancel():
        raise NextScene("Main")


def demo(screen, scene):
    scenes = [
        Scene([ListView(screen, competitors)], -1, name="Main"),
        Scene([CompetitorView(screen, competitors)], -1, name="Edit competitor")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene)

def get_name(bib):
    if names.has_key(bib):
        return names[bib]
    else:
        return ""

def unicode_csv_reader(utf8_data, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf8_data, **kwargs)

    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

encoding = sys.getfilesystemencoding()
argv = [unicode(x, encoding, 'ignore') for x in sys.argv[1:]]

while argv:
    arg = argv.pop()
    if arg == '--reset':
        confirm = raw_input("Delete existing competition? All data will removed. [y/N]")
        if confirm == 'y':
            os.remove("state.dat") if os.path.exists("state.dat") else None
            os.remove("competitors.db") if os.path.exists("competitors.db") else None

names = {}
if os.path.isfile('competitors.txt'):
    tsvin = unicode_csv_reader(open('competitors.txt'), delimiter=',')
    for row in tsvin:
        names[row[0]] = row[1]

competitors = CompetitorModel()
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
