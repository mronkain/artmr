from sqlobject import SQLObject, UnicodeCol, DateTimeCol, StringCol, BoolCol, MultipleJoin, \
    IntCol, ForeignKey, connectionForURI, sqlhub, AND, SQLObjectNotFound

class Competition(SQLObject):
    name = UnicodeCol()
    place = UnicodeCol()
    plannedStartTime = DateTimeCol(default=None)
    startTime = DateTimeCol(default=None)
    finishTime = DateTimeCol(default=None)
    notes = UnicodeCol(default=None)
    active = BoolCol(default=None)
    competitors = MultipleJoin('Competitor')
    splits = MultipleJoin('Split')

class Competitor(SQLObject):
    name = UnicodeCol(default=None)
    contact = UnicodeCol(default=None)

    team = UnicodeCol(default=None)

    number = IntCol(default=None)
    starting = BoolCol(default=False)

    category = ForeignKey('Category')
    competition = ForeignKey('Competition')
    splits = MultipleJoin('Split')

class Split(SQLObject):
    split_info = UnicodeCol(default="Finish") # lap
    lap = IntCol(default=None)
    time = DateTimeCol(default=None)
    competitor = ForeignKey('Competitor', default=None)
    competition = ForeignKey('Competition')

class Category(SQLObject):
    name = UnicodeCol(default=None)
    competitors = MultipleJoin('Competitor')
