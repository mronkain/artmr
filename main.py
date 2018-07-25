#!/usr/bin/python
from asciimatics.widgets import Frame, MultiColumnListBox, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent

from time import time, strftime, gmtime, localtime
from datetime import datetime

from sqlobject import *

import os.path
import sys
import logging
import csv
from random import randrange

version = '0.5'

class Competition(SQLObject):
    name = UnicodeCol()
    place = UnicodeCol()
    plannedStartTime = DateTimeCol(default=None)
    startTime = DateTimeCol(default=None)
    finishTime = DateTimeCol(default=None)
    notes = StringCol(default=None)
    active = BoolCol(default=None)
    competitors = MultipleJoin('Competitor')
    splits = MultipleJoin('Split')

class Competitor(SQLObject):
    name = UnicodeCol(default=None)
    contact = StringCol(default=None)

    number = IntCol(default=None)
    starting = BoolCol(default=False)

    category = ForeignKey('Category')
    competition = ForeignKey('Competition')
    splits = MultipleJoin('Split')

class Split(SQLObject):
    split_info = UnicodeCol(default="Finish") # lap
    time = DateTimeCol(default=None)
    competitor = ForeignKey('Competitor', default=None)
    competition = ForeignKey('Competition')

class Category(SQLObject):
    name = UnicodeCol(default=None)
    competitors = MultipleJoin('Competitor')

# global state singleton to keep track of what is being shown / edited
class StateController(object):
    def __init__(self):
        self._current_competition = None
        self._current_competitor = None
        self._current_split = None
        self._current_category = None

    def get_current_competition(self):
        return self._current_competition

    def get_current_competitor(self):
        return self._current_competitor

    def set_current_competition(self, name):
        self._current_competition = Competition.get(1)

    def create_competition(self, name):
        comp = Competition(name=name, place="somewhere", active=True)
        self._current_competition = comp

    def set_current_competitor(self, competitor):
        try:
            self._current_competitor = Competitor.selectBy(id=competitor).getOne()
        except SQLObjectNotFound as e:
            self._current_competitor = None

    def set_current_split(self, split):
        try:
            self._current_split = Split.selectBy(id=split).getOne()
        except SQLObjectNotFound as e:
            self._current_split = None


    def add_competitor(self, competitor, number, category):
        try:
            Competitor.selectBy(name=competitor, number=int(number), competition=self._current_competition).getOne()
        except SQLObjectNotFound as e:
            cat = self.find_or_create_category(category)
            self._current_competitor = Competitor(name=competitor, number=int(number), competition=self._current_competition, category=cat)

    def add_split(self, time):
        s=Split(time=time, competition=self._current_competition, competitor=self._current_competitor)
        return s.id

    def change_number(self, split_id):
        pass

    def get_competitions(self):
        return Competition.select()

    def start_current_competition(self, start_time):
        self._current_competition.startTime = start_time

    def get_competitors(self, sort):
        if sort == "alpha":
            return Competitor.select(Competition.q.id==self._current_competition.id).orderBy('name')
        else:
            return Competitor.select(Competition.q.id==self._current_competition.id).orderBy('number')

    def get_present_competitors(self):
        return Competitor.select(AND(Competition.q.id==self._current_competition.id,Competitor.q.starting==True)).orderBy('number')

    def set_current_split_competitor(self):
        if self._current_competitor and self._current_split:
            self._current_split.competitor = self._current_competitor

    def set_current_category(self, category):
        if category != None:
            cat = Category.get(category)
            self._current_category = cat
        else:
            self._current_category = None


    def find_or_create_category(self, category):
        try:
            cat = Category.selectBy(name=category).getOne()
        except SQLObjectNotFound:
            cat = Category(name=category)

        return cat

    def get_current_category(self):
        return self._current_category

    def get_categories(self):
        return Category.select()

    def get_splits(self):
        return Split.select(Competition.q.id==self._current_competition.id).orderBy('time')

class SplitListView(Frame):
    def __init__(self, screen, controller):
        super(SplitListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version + " - RESULTS for " + controller.get_current_competition().name)

        logging.basicConfig(filename='example.log',level=logging.INFO)

        self._controller = controller

        self._last_frame = 0
        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['5%', '12%', '8%', '10%', '35%', '20%'],
            self._get_summary(),
            name="splits",
            on_change=self._on_pick,
            titles=['Rank', 'Finishing time', 'Diff', 'Number', 'Name', 'Category'])

        self._start_list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['50%','50%'],
            self._get_competitor_summary(),
            name="competitors",
            on_change=self._on_comp_pick,
            titles=['Number', 'Name'])


        self._edit_button = Button("Edit", self._match_split)
        self._start_button = Button("Start", self._start)
        self._quit_button = Button("Quit", self._quit)
        self._split_button = Button("Split", self._add)
        self._start_list_button = Button("Start list", self._start_list)

        self._start_button.disabled = (self._controller.get_current_competition().startTime != None)
        self._split_button.disabled = (self._controller.get_current_competition().startTime == None)

        layout0 = Layout([100])
        layout1 = Layout([75,25], fill_frame=True)
        layout2 = Layout([100])
        self.add_layout(layout0)
        self.add_layout(layout1)
        self.add_layout(layout2)

        self._time_label = Text("Elapsed Time:")
        self._time_label.value = "NOT STARTED"
        self._time_label.disabled = True


        self._cat_label = Text("Selected Category [F2]:")
        self._cat_label.value = "All"
        self._cat_label.disabled = True

        layout0.add_widget(self._time_label)
        layout0.add_widget(self._cat_label)
        layout1.add_widget(self._list_view, 0)
        layout1.add_widget(self._start_list_view, 1)
        layout0.add_widget(Divider())
        layout2.add_widget(Divider())
        layout3 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout3)
        layout3.add_widget(self._start_list_button, 0)
        layout3.add_widget(self._start_button, 1)
        layout3.add_widget(self._split_button, 2)
        layout3.add_widget(self._edit_button, 3)
        layout3.add_widget(self._quit_button, 4)

        self.fix()
        self._on_pick()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == ord('s') or key == 32:
                self._add()
            elif key == ord('e'):
                self._match_split()
            elif key == ord('x'):
                self._export()
            elif key == ord('m') or key == -2:
                raise NextScene("Main Menu")
            elif key == -3:
                raise NextScene("CategorySelect")

            else:
                super(SplitListView, self).process_event(event)
        else:
            super(SplitListView, self).process_event(event)


    def _get_summary(self):
        rows = []
        i=1
        leader = None
        for split in self._controller.get_splits():
            if split.competitor:
                if self._controller.get_current_category() != None and split.competitor.category != self._controller.get_current_category():
                    continue

                name = split.competitor.name
                number = str(split.competitor.number)
                cat = split.competitor.category.name
            else:
                name = ""
                number = ""
                cat = ""

            if leader == None:
                leader = split.time

            option = (
                [   str(i),
                    str(split.time.replace(microsecond=0) - self._controller.get_current_competition().startTime.replace(microsecond=0)),
                    str(split.time.replace(microsecond=0) - leader.replace(microsecond=0)),
                    number,
                    name,
                    cat
                    ],
                split.id
            )
            i=i+1
            rows.append(option)

        return rows

    def _get_competitor_summary(self):
        rows = []
        for competitor in self._controller.get_present_competitors():
            if len(competitor.splits) == 0:
                option = (
                    [   str(competitor.number),
                        competitor.name
                    ],
                    competitor.id
                )
                rows.append(option)

        return rows


    def _on_pick(self):
        self._controller.set_current_split(self._list_view.value)
        self._edit_button.disabled = self._list_view.value is None

    def _on_comp_pick(self):
        self._controller.set_current_competitor(self._start_list_view.value)

    def _reload_list(self):
        val = self._list_view.value
        self._list_view.options = self._get_summary()
        self._list_view.value = val

        self._start_list_view.options = self._get_competitor_summary()

    def _add(self):
        if self._controller.get_current_competition().startTime == None:
            self._start()
        else:
            split = datetime.now()
            split_id = self._controller.add_split(split)

            self._reload_list()
            self._list_view.value = split_id
            self._on_pick

    def _edit(self):
        self.save()
        raise NextScene("Edit competitor")

    def _start_list(self):
        raise NextScene("StartList")

    def _delete(self):
        self.save()
        self._reload_list()

    def _start(self):
        if self._controller.get_current_competition().startTime == None:
            self._controller.start_current_competition(datetime.now())

        self._start_button.disabled = True
        self._split_button.disabled = False

    def _update(self, frame_no):
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            if self._controller.get_current_competition().startTime != None:
                self._time_label.value = str(datetime.now().replace(microsecond=0) - self._controller.get_current_competition().startTime.replace(microsecond=0))
            else:
                self._time_label.value = "NOT STARTED"
    
            if self._controller.get_current_category() == None:
                self._cat_label.value = "All"
            else:
                self._cat_label.value = self._controller.get_current_category().name

        super(SplitListView, self)._update(frame_no)

    def _match_split(self):
        self._controller.set_current_split_competitor()
        self._reload_list()

    def _export(self):
        list = self._controller.get_splits()

        if self._controller.get_current_category() == None:
            name = 'results_' + str(datetime.now()) + '.csv'
        else:
            name = 'results_' + self._controller.get_current_category().name + '_' + str(datetime.now()) + '.csv'

        keepcharacters = (' ','.','_', '-')
        name = "".join(c for c in name if c.isalnum() or c in keepcharacters).rstrip()

        with open(name, 'wb') as f:
            writer = csv.writer(f)

            writer.writerow(['rank', 'time elapsed', 'difference', 'number', 'name', 'category'])
            rank = 1
            leader = None
            for split in list:
                if split.competitor:
                    if self._controller.get_current_category() != None and split.competitor.category != self._controller.get_current_category():
                        continue

                    name = split.competitor.name
                    number = str(split.competitor.number)
                    cat = split.competitor.category.name
                else:
                    name = ""
                    number = ""
                    cat = ""

                if leader == None:
                    leader = split.time

                writer.writerow([
                    rank,
                    str(split.time.replace(microsecond=0) - self._controller.get_current_competition().startTime.replace(microsecond=0)),
                    str(split.time.replace(microsecond=0) - leader.replace(microsecond=0)),
                    number,
                    name.encode('utf-8'),
                    cat
                ])
                rank += 1

    @property
    def frame_update_count(self):
        # Refresh once every 2 seconds by default.
        return 20

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

class StartListView(Frame):
    def __init__(self, screen, controller):
        super(StartListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="TIMER2 v" + version + " - START LIST for " + controller.get_current_competition().name)
        self._controller = controller
        self._last_frame = 0
        self._sort = "123"

        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['15%', '15%','55%', '15%'],
            self._get_summary(),
            name="start list",
            on_change=self._on_pick,
            titles=['Number', 'Call-up', 'Name', 'Category'])
        self._splits_button = Button("Timing", self._splits)
        self._edit_button = Button("Sort ABC", self._toggle_sort)
        self._present_button = Button("Present", self._starting)
        self._quit_button = Button("Quit", self._quit)
        self._start_time = None

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._splits_button, 0)
        layout2.add_widget(self._present_button, 1)
        layout2.add_widget(self._edit_button, 2)
        layout2.add_widget(self._quit_button, 3)

        self.fix()
        self._on_pick()

    def _get_summary(self):
        rows = []
        for competitor in self._controller.get_competitors(self._sort):
            if competitor.starting:
                present = "[X]"
            else:
                present = "[O]"

            if self._sort == "123":
                option = (
                    [   str(competitor.number),
                        present,
                        competitor.name,
                        competitor.category.name
                    ],
                    competitor.id
                )
            else:
                option = (
                    [   competitor.name,
                        present,
                        str(competitor.number),
                        competitor.category.name

                    ],
                    competitor.id
                )

            rows.append(option)

        return rows

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._controller.set_current_competitor(self._list_view.value)

    def _reload_list(self):
        val = self._list_view.value
        self._list_view.options = self._get_summary()
        self._list_view.value = val

    def _toggle_sort(self):
        if self._sort == "alpha":
            self._sort = "123"
        else:
            self._sort = "alpha"

        self._reload_list()

    def _starting(self):
        self._controller.get_current_competitor().starting = not self._controller.get_current_competitor().starting
        self._reload_list()

    def _splits(self):
        raise NextScene("Main")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == ord('s'):
                self._toggle_sort()
            elif key == ord('p') or key == 32:
                self._starting()
            elif key == ord('m') or key == -2:
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
            ("Timing", 1),
            ("Start list", 2)
        ]
        return opts

    def _ok(self):
        if self._list_view.value == 1:
            raise NextScene("Main")
        elif self._list_view.value == 2:
            raise NextScene("StartList")

    def process_event(self, event):
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

class CategorySelectListView(Frame):
    def __init__(self, screen, controller):
        super(CategorySelectListView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Select Category",
                                          reduce_cpu=True)
        self._controller = controller
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
        items = self._controller.get_categories()
        opts = [('All', -1)]
        for cat in items:
            opts.append([cat.name, cat.id])

        return opts

    def _ok(self):
        if self._list_view.value == -1:
            self._controller.set_current_category(None)
        else: 
            self._controller.set_current_category(self._list_view.value)
        
        raise NextScene("Main")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == 10 or key == 32:
                self._ok()
            else:
                super(CategorySelectListView, self).process_event(event)
        else:
            super(CategorySelectListView, self).process_event(event)


    @staticmethod
    def _cancel():
        raise NextScene("Main")

def demo(screen, id):
    scenes = [
        Scene([SplitListView(screen, controller)], -1, name="Main"),
        Scene([MenuListView(screen, controller)], -1, name="Main Menu"),
        Scene([StartListView(screen, controller)], -1, name="StartList"),
        Scene([CategorySelectListView(screen, controller)], -1, name="CategorySelect")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scenes[id])

def unicode_csv_reader(utf8_data, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf8_data, **kwargs)

    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

encoding = sys.getfilesystemencoding()
argv = [unicode(x, encoding, 'ignore') for x in sys.argv[1:]]

create_tables = not os.path.isfile('competitors.db')

while argv:
    arg = argv.pop()
    if arg == '--reset':
        confirm = raw_input("Delete existing competitions? All data will removed. [y/N] ")
        if confirm == 'y' and os.path.exists("competitors.db"):
            os.remove("competitors.db")
            create_tables = True

sqlhub.processConnection = connectionForURI("sqlite://" + os.path.abspath('competitors.db'))

if create_tables:
    Competition.createTable()
    Competitor.createTable()
    Split.createTable()
    Category.createTable()

controller = StateController()

comps = controller.get_competitions()

if comps.count() == 0:
    name = raw_input("Enter your competition name: [blank] ") or "~~You really should have a name for these things~~"
    controller.create_competition(name)

else:
    controller.set_current_competition(None)

if os.path.isfile('competitors.txt'):
    tsvin = unicode_csv_reader(open('competitors.txt'), delimiter=',')
    for row in tsvin:
        controller.add_competitor(row[1], row[0], row[2])


if controller.get_current_competition().startTime == None:
    last_scene = 2
else:
    last_scene = 0

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        pass
