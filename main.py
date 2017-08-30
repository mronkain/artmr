from asciimatics.widgets import Frame, MultiColumnListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from time import time, strftime, gmtime

import sys
import sqlite3

class CompetitorModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row

        # Create the basic competitor table.
        self._db.cursor().execute('''
            CREATE TABLE competitors(
                id INTEGER PRIMARY KEY,
                name TEXT DEFAULT "nn",
                bib TEXT DEFAULT "0",
                finish_time TEXT)
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
            "SELECT finish_time, bib, name, id from competitors").fetchall()
        r = []
        for finish, bib, name, id in list:
            r.append([{finish, bib, name}, id])

        return r

    def get_competitor(self, competitor_id):
        return self._db.cursor().execute(
            "SELECT * from competitors where id=?", str(competitor_id)).fetchone()

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


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="Competitor List")
        # Save off the model that accesses the competitors database.
        self._model = model
        self._start_time = None
        self._last_frame = 0

        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['30%','30%', '30%'],
            model.get_summary(),
            name="competitors",
            on_change=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Start", self._start)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self._time_label = Text("Time: ", '00:00:00')
        self._time_label.disabled = True
        layout.add_widget(self._time_label)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Start", self._start), 0)
        layout2.add_widget(Button("Split", self._add), 1)
        layout2.add_widget(self._edit_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        #self._delete_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._model.get_summary()
        self._model.current_id = None

    def _add(self):
        self._model.current_id = None
        details = {'finish_time': str(time() - self._start_time)}

        self._model.update_current_competitor(details)
        self._reload_list()
        #self._model.save()
        #raise NextScene("Edit competitor")

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

        self._time_label.value = strftime('%H:%M:%S', gmtime(time() - self._start_time))

    def _update(self, frame_no):
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            if self._start_time != None:
                self._time_label.value = strftime('%H:%M:%S', gmtime(time() - self._start_time))

        super(ListView, self)._update(frame_no)

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
        layout.add_widget(Text("Name:", "name"))
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

    @staticmethod
    def _cancel():
        raise NextScene("Main")


def demo(screen, scene):
    scenes = [
        Scene([ListView(screen, competitors)], -1, name="Main"),
        Scene([CompetitorView(screen, competitors)], -1, name="Edit competitor")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene)

competitors = CompetitorModel()
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
