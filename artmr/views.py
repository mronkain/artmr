from asciimatics.widgets import Frame, MultiColumnListBox, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label, FileBrowser
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent

from time import time, strftime, gmtime, localtime
from datetime import datetime

from sqlobject import connectionForURI, sqlhub, SQLObjectNotFound, AND

from models import Competition, Competitor, Split, Category

import os.path
import sys
import logging
import csv

VERSION = '1.0-BETA'

class SplitListView(Frame):
    def __init__(self, screen, controller):
        super(SplitListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       reduce_cpu=True,
                                       title="artmr v" + VERSION + " - RESULTS for " + controller.get_current_competition().name)

        #logging.basicConfig(filename='example.log',level=logging.INFO)

        self._controller = controller

        self._last_frame = 0
        # Create the form for displaying the list of competitors.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['5%', '12%', '12%', '10%', '35%', '16%'],
            self._get_summary(),
            name="splits",
            on_change=self._on_pick,
            titles=['Rank', 'Time', 'Diff', 'Number', 'Name', 'Category'])

        self._start_list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['25%','75%'],
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

        layout = Layout([20, 10, 70])
        layout0 = Layout([100])
        layout1 = Layout([75,25], fill_frame=True)
        layout2 = Layout([100])
        self.add_layout(layout)
        self.add_layout(layout0)
        self.add_layout(layout1)
        self.add_layout(layout2)

        self._time_label = Label("Elapsed Time:")
        self._time_label_value = Label("NOT STARTED")

        self._cat_label = Label("Selected Category [F2]:")
        self._cat_label_value = Label("All")
        self._cat_label.disabled = True

        layout.add_widget(self._time_label,0)
        layout.add_widget(self._time_label_value, 1)
        layout.add_widget(self._cat_label, 0)
        layout.add_widget(self._cat_label_value, 1)
        layout1.add_widget(Label("Start list"), 1)
        layout1.add_widget(self._list_view, 0)
        layout1.add_widget(self._start_list_view, 1)
        layout0.add_widget(Divider())
        layout2.add_widget(Divider())

        if self._controller.get_current_competition().startTime == None:
            self._info_label_text = "Press Space / Start to begin timing. Press F2 for category filter."
        else: 
            self._info_label_text = "Create new splits with S / Space. Select competitor first or add a competitor to a split with Edit / E. Press F2 for category filter. Export with X."

        self._info_label = Label(self._info_label_text)
        self._info_label_reset = None

        layout2.add_widget(self._info_label)

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
        self._start_list_view.value = None

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
        self._info_label_text = "Create new splits with S / Space. Select competitor first or add a competitor to a split with Edit / E. Press F2 for category filter. Export with X."
        self._info_label.text = self._info_label_text

        if self._controller.get_current_competition().startTime == None:
            self._controller.start_current_competition(datetime.now())

        self._start_button.disabled = True
        self._split_button.disabled = False

    def _update(self, frame_no):
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            if self._controller.get_current_competition().startTime != None:
                self._time_label_value.text = str(datetime.now().replace(microsecond=0) - self._controller.get_current_competition().startTime.replace(microsecond=0))
            else:
                self._time_label_value.text = "NOT STARTED"
    
            if self._controller.get_current_category() == None:
                self._cat_label_value.text = "All"
            else:
                self._cat_label_value.text = self._controller.get_current_category().name

            if self._info_label_reset == 0:
                self._info_label.text = self._info_label_text
                self._info_label_reset = None
            elif self._info_label_reset != None:
                self._info_label_reset = self._info_label_reset -1

        super(SplitListView, self)._update(frame_no)

    def _match_split(self):
        self._controller.set_current_split_competitor()
        self._reload_list()

    def _export(self):
        list = self._controller.get_splits()

        if self._controller.get_current_category() == None:
            fname = self._controller.get_current_competition().name + '_' + str(datetime.now()) + '.csv'
        else:
            fname = self._controller.get_current_competition().name + '_' + self._controller.get_current_category().name + '_' + str(datetime.now()) + '.csv'

        keepcharacters = (' ','.','_', '-')
        fname = "".join(c for c in fname if c.isalnum() or c in keepcharacters).rstrip()

        with open(fname, 'wb') as f:
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
    
        self._info_label.text = "Exported to '" + fname + "'."
        self._info_label_reset = 20

    @property
    def frame_update_count(self):
        return 40

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
                                       title="artmr v" + VERSION + " - START LIST for " + controller.get_current_competition().name)
        self._controller = controller
        self._last_frame = 0
        self._sort = "alpha"

        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['15%', '55%','15%', '15%'],
            self._get_summary(),
            name="start list",
            on_change=self._on_pick,
            titles=['Number', 'Name', 'Category', 'Starting'])
        self._splits_button = Button("Timing", self._splits)
        self._edit_button = Button("Tgl Sort", self._toggle_sort)
        self._present_button = Button("Tgl Starting", self._starting)
        self._quit_button = Button("Quit", self._quit)
        self._start_time = None

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self._info_label = Label("Press F2 to load a starting list. Use Space / Present to confirm starting competitors. Go to Timing page to start the race.")
        layout.add_widget(self._list_view)
        layout.add_widget(self._info_label)
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

            option = (
                [   str(competitor.number),
                    competitor.name,
                    competitor.category.name,
                    present
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
            elif key == -3:
                raise NextScene("LoadStartList")
            else:
                super(StartListView, self).process_event(event)
        else:
            super(StartListView, self).process_event(event)


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

class LoadStartListView(Frame):
    def __init__(self, screen, controller):
        super(LoadStartListView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Load Start List",
                                          reduce_cpu=True)

        self._file_browser = FileBrowser(
            Widget.FILL_FRAME,
            ".",
            name="fileBrowser",
            on_select=self._ok)
        self._ok_button = Button("Ok", self._ok)
        self._cancel_button = Button("Cancel", self._cancel)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Label("Start list should be in a UTF-8 text file with the format '[number],[competitor name],[competitor category]'"))
        layout.add_widget(Divider())
        layout.add_widget(self._file_browser)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self._controller = controller
        self.fix()

    def _ok(self):
        self._controller.load_competitors(self._file_browser.value)
        raise NextScene("StartList")

    def process_event(self, event):
        super(LoadStartListView, self).process_event(event)


    @staticmethod
    def _cancel():
        raise NextScene("StartList")

