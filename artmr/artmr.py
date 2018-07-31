#!/usr/bin/python
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

from sqlobject import connectionForURI, sqlhub, SQLObjectNotFound, AND

from .models import Competition, Competitor, Split, Category

from .views import SplitListView, MenuListView, StartListView, CategorySelectListView, LoadStartListView

import os.path
import sys
import logging
import csv
from os.path import expanduser
import argparse

VERSION = '1.0-BETA'

DESCRIPTION = 'artmr %ss' % VERSION

SCHEMA_VERSION = '1'
DB_PATH = expanduser("~") + '/.artmr/'
DB_FILE = 'results_%s.db' % SCHEMA_VERSION

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
        s = Split(time=time, competition=self._current_competition, competitor=self._current_competitor)
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
    
    def load_competitors(self, filename):
        def unicode_csv_reader(utf8_data, **kwargs):
            # csv.py doesn't do Unicode; encode temporarily as UTF-8:
            csv_reader = csv.reader(utf8_data, **kwargs)

            for row in csv_reader:
                yield [unicode(cell, 'utf-8') for cell in row]

        tsvin = unicode_csv_reader(open(filename), delimiter=',')
        for row in tsvin:
            try:
                if len(row) > 2:
                    self.add_competitor(row[1], row[0], row[2])
                elif len(row) > 1:
                    self.add_competitor(row[1], row[0], "")
            except:
                pass


def demo(screen, scene, default_to_start_list, controller):
    scenes = [
        Scene([SplitListView(screen, controller)], -1, name="Main"),
        Scene([MenuListView(screen, controller)], -1, name="Main Menu"),
        Scene([StartListView(screen, controller)], -1, name="StartList"),
        Scene([CategorySelectListView(screen, controller)], -1, name="CategorySelect"),
        Scene([LoadStartListView(screen, controller)], -1, name="LoadStartList")
    ]

    if scene == None and default_to_start_list:
        scene = scenes[2]
    
    screen.play(scenes, stop_on_resize=True, start_scene=scene)


def main():
    if not os.path.isdir(DB_PATH):
        os.mkdir(DB_PATH)

    create_tables = not os.path.isfile(os.path.join(DB_PATH, DB_FILE))

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--reset", help="Reset current competition", action="store_true")
    parser.add_argument("-c", "--competitors", help="Read competitors from file. File should be a csv with '[number],[competitor name],[competitor category]'. See homepage for an example file.")
    args = parser.parse_args()

    if args.reset:
        confirm = raw_input("Delete existing competitions? All data will removed. [y/N] ")
        if confirm == 'y' and os.path.exists(os.path.join(DB_PATH, DB_FILE)):
            os.remove(os.path.join(DB_PATH, DB_FILE))
            create_tables = True

    sqlhub.processConnection = connectionForURI("sqlite://" + os.path.join(DB_PATH, DB_FILE))

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
        new = True

    else:
        controller.set_current_competition(None)
        new = False

    if args.competitors:
        controller.load_competitors(args.competitors)

    default_to_start_list = (controller.get_current_competition().startTime == None)
    last_scene = None

    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene, default_to_start_list, controller])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
