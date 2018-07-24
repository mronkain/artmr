#!/usr/bin/python
from asciimatics.widgets import Frame, MultiColumnListBox, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent

from time import time, strftime, gmtime, localtime
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

import os.path
import sys
import logging
import csv
from random import randrange

version = '0.4'
Base = declarative_base()

class Competition(Base):
    __tablename__ = 'competitions'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    place = Column(String)
    planned_start_time = Column(DateTime)
    start_time = Column(DateTime)
    finish_time = Column(DateTime)
    notes = Column(String)
    active = Column(Boolean)
    competitors = relationship("Participation", back_populates="competition")
    splits = relationship("Split", back_populates="competition")

class Competitor(Base):
    __tablename__ = 'competitors'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    contact = Column(String)
    competitions = relationship("Participation", back_populates="competitor")
    splits = relationship("Split", back_populates="competitor")

class Participation(Base):
    __tablename__ = 'participations'
    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id'))
    competition_id = Column(Integer, ForeignKey('competitions.id'))
    number = Column(String)
    starting = Column(Boolean, default=False)
    competitor = relationship("Competitor", back_populates="competitions")
    competition = relationship("Competition", back_populates="competitors")

class Split(Base):
    __tablename__ = 'splits'
    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id'))
    competition_id = Column(Integer, ForeignKey('competitions.id'))
    split_info = Column(String, default="Finish") # lap
    time = Column(DateTime)
    competitor = relationship("Competitor", back_populates="splits")
    competition = relationship("Competition", back_populates="splits")

# global state singleton to keep track of what is being shown / edited
class StateController(object):
    def __init__(self, session):
        self._session = session
        self._current_competition = None
        self._current_competitor = None

    def get_current_competition(self):
        return self._current_competition

    def get_current_competitor(self):
        return self._current_competitor

    def set_current_competition(self, name):
        comp = Competition(name=name, place="somewhere", active=True)
        self._session.add(comp)
        self._session.commit()
        self._current_competition = comp

    def set_current_competitor(self):
        pass

    def add_competitor(self, competitor, number):
        c = Competitor(name=competitor)
        p = Participation(number=number)
        p.competitor = c
        self._current_competition.competitors.append(p)
        self._session.commit()

    def add_split(self, time):
        s=Split(time=time, competition=self.get_current_competition)
        self._session.add(s)
        self._session.commit()
        
    def change_number(self, split_id):
        pass

    def get_competitions(self):
        return self._session.query(Competition)

    def start_current_competition(self, start_time):
        self._current_competition.start_time = start_time
        self._session.commit()

class SplitListView(Frame):
    def __init__(self, screen, controller):
        super(SplitListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version + " - SPLITS " + controller.get_current_competition().name)
        # Save off the model that accesses the competitors database.
        logging.basicConfig(filename='example.log',level=logging.INFO)

        self._controller = controller
        
        self._last_frame = 0
        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['10%', '25%','25%', '30%'],
            self._get_summary(),
            name="competitors",
            on_change=self._on_pick,
            titles=['Rank', 'Finishing time', 'Number', 'Name'])
        self._edit_button = Button("Edit", self._edit)
        self._start_button = Button("Start", self._start)
        self._quit_button = Button("Quit", self._quit)
        self._split_button = Button("Split", self._add)

        self._start_button.disabled = (self._controller.get_current_competition().start_time != None)
        self._split_button.disabled = (self._controller.get_current_competition().start_time == None)

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
            elif key == ord('m'):
                raise NextScene("Main Menu")

            else:
                super(SplitListView, self).process_event(event)
        else:
            super(SplitListView, self).process_event(event)


    def _get_summary(self):
        rows = []
        i=0
        for x in self._controller.get_current_competition().competitors:
            option = (
                [   str(i),
                    "00:00",
                    x.number,
                    x.competitor.name
                    ],
            x.id
            )
            i=i+1
            rows.append(option)

        return rows

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._get_summary()

    def _add(self):
        self._reload_list()

    def _edit(self):
        self.save()
        raise NextScene("Edit competitor")

    def _delete(self):
        self.save()
        self._reload_list()

    def _start(self):
        if self._controller.get_current_competition().start_time == None:
            self._controller.start_current_competition(datetime.now())

        self._start_button.disabled = True
        self._split_button.disabled = False

    def _update(self, frame_no):
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            if self._controller.get_current_competition().start_time != None:
                self._time_label.value = str(datetime.now().replace(microsecond=0) - self._controller.get_current_competition().start_time.replace(microsecond=0))
            else:
                self._time_label.value = "NOT STARTED"

        super(SplitListView, self)._update(frame_no)

    def _get_export_data(self):
        pass

    def _export(self):
        list = self._get_export_data()

        with open('export.csv', 'wb') as f:
            writer = csv.writer(f)

            writer.writerow(['rank', 'bib', '(((Start time)))',
                '00:00:00',
                strftime("%Y-%m-%d %H:%M:%S %Z", localtime(self._controller.get_current_competition().start_time))])
            rank = 1
            for l in list:
                writer.writerow([
                    rank,
                    l['bib'],
                    #get_name(l['bib']).encode('utf-8'),
                    (l['bib']).encode('utf-8'),
                    strftime('%H:%M:%S', gmtime(l['finish_time'])),
                    strftime("%Y-%m-%d %H:%M:%S %Z", localtime(self._controller.get_current_competition().start_time + l['finish_time']))
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
    def __init__(self, screen, controller):
        super(CompetitorView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Competitor Details",
                                          reduce_cpu=True)
        # Save off the model that accesses the competitors database.
        self._controller = controller

        # Create the form for displaying the list of competitors.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        #layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Number:", "bib"))
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(CompetitorView, self).reset()
        # self.data = self._model.get_current_competitor()

    def _ok(self):
        self.save()
        # self._model.update_current_competitor(self.data)
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

class StartListView(Frame):
    def __init__(self, screen, controller):
        super(StartListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version + " - START LIST " + controller.get_current_competition().name)
        # Save off the model that accesses the competitors database.

        self._controller = controller
        self._last_frame = 0
        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['15%', '15%','70%'],
            self._get_summary(),
            name="start list",
            on_change=self._on_pick,
            titles=['Number', 'Call-up', 'Name'])
        self._add_button = Button("Add", self._add)
        self._edit_button = Button("Edit", self._edit)
        self._present_button = Button("Present", self._present)
        self._quit_button = Button("Quit", self._quit)
        self._start_time = None

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._add_button, 0)
        layout2.add_widget(self._present_button, 1)
        layout2.add_widget(self._edit_button, 2)
        layout2.add_widget(self._quit_button, 3)

        self.fix()
        self._on_pick()

    def _get_summary(self):
        rows = []
        i=0
        for x in self._controller.get_current_competition().competitors:
            if x.starting:
                present = "[X]"
            else:
                present = "[O]"

            option = (
                [   x.number,
                    present,
                    x.competitor.name
                ],
                x.id
            )
            i=i+1
            rows.append(option)

        return rows

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._get_summary()

    def _add(self):
        raise NextScene("Edit competitor")

    def _edit(self):
        raise NextScene("Edit competitor")

    def _present(self):
        self._reload_list()

    def process_event(self, event):
        logging.info(event)
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == ord('a'):
                self._add()
            elif key == ord('e') or key == 10:
                self._edit()
            elif key == ord('p') or key == 32:
                self._present()
            elif key == ord('m'):
                raise NextScene("Main Menu")

            else:
                super(StartListView, self).process_event(event)
        else:
            super(StartListView, self).process_event(event)



    def _get_export_data(self):
        pass

    def _export(self):
        list = self._get_export_data()

        with open('start_list.csv', 'wb') as f:
            writer = csv.writer(f)

            writer.writerow(['rank', 'bib', '(((Start time)))',
                '00:00:00',
                strftime("%Y-%m-%d %H:%M:%S %Z", localtime(self._start_time))])
            rank = 1
            for l in list:
                writer.writerow([
                    rank,
                    l['bib'],
                    (l['bib']).encode('utf-8'),
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

class MenuListView(Frame):
    def __init__(self, screen, model):
        super(MenuListView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Main Menu",
                                          reduce_cpu=True)

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            self._get_items(),
            name="menu")
        self._ok_button = Button("Ok", self._ok)
        self._cancel_button = Button("Cancel", self._cancel)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)

        self.fix()

    def _get_items(self):
        opts = [
            ("Splits", 1),
            ("Start list", 2),
            ("Select competititon", 3)
        ]
        return opts

    def _ok(self):
        if self._list_view.value == 1:
            raise NextScene("Main")
        elif self._list_view.value == 2:
            raise NextScene("StartList")
        else:
            raise NextScene("CompetitionList")

    def process_event(self, event):
        logging.info(event)
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == 10 or key == 32:
                self._ok()
            else:
                super(MenuListView, self).process_event(event)
        else:
            super(MenuListView, self).process_event(event)


    @staticmethod
    def _cancel():
        raise NextScene("Main")


class CompetitionListView(Frame):
    def __init__(self, screen, controller):
        super(CompetitionListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version + " - COMPETITIONS")
        # Save off the model that accesses the competitors database.
        logging.basicConfig(filename='example.log',level=logging.INFO)

        self._controller = controller
        self._last_frame = 0
        # Create the form for displaying the list of competitions.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['10%', '25%','25%', '30%'],
            self._get_summary(),
            name="competitions",
            titles=['id', 'Name', 'Date', 'Place'])
        # self._edit_button = Button("Edit")
        # self._start_button = Button("Start")
        # self._quit_button = Button("Quit")

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
        # layout2.add_widget(self._start_button, 0)
        # layout2.add_widget(self._edit_button, 1)
        # layout2.add_widget(self._quit_button, 4)

        self.fix()

    def _get_summary(self):
        rows = []
        i=0
        if self._controller.get_competitions() != None:
            for x in self._controller.get_competitions():
                option = (
                    [   str(i),
                        x.name,
                        x.place,
                        ""
                        ],
                x.id
                )
                i=i+1
                rows.append(option)

        return rows

    def _reload_list(self):
        self._list_view.options = self._get_summary()


    def process_event(self, event):
        logging.info(event)
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == ord('m'):
                raise NextScene("Main Menu")
            else:
                super(CompetitionListView, self).process_event(event)
        else:
            super(CompetitionListView, self).process_event(event)




def demo(screen, id):
    scenes = [
        Scene([SplitListView(screen, controller)], -1, name="Main"),
        Scene([CompetitorView(screen, controller)], -1, name="Edit competitor"),
        Scene([MenuListView(screen, controller)], -1, name="Main Menu"),
        Scene([StartListView(screen, controller)], -1, name="StartList"),
        Scene([CompetitionListView(screen, controller)], -1, name="CompetitionList")
        # CompetitionListView
        # CompetitionView
        # CompetitionStartListView
        # PopUpMenuListView
        # Scene([])
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scenes[id])

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
        confirm = raw_input("Delete existing competitions? All data will removed. [y/N]")
        if confirm == 'y':
            os.remove("competitors.db") if os.path.exists("competitors.db") else None

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

controller = StateController(session)
controller.set_current_competition("HARK Kore kilpa")

if os.path.isfile('competitors.txt'):
    tsvin = unicode_csv_reader(open('competitors.txt'), delimiter=',')
    for row in tsvin:
        controller.add_competitor(row[1], row[0])


last_scene = 0
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
