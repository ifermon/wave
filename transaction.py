"""
    This program reads a simple csv files containing the following fields:
        date, employee id, type, position id

    Types are the following:
        Job Change
        Org Assignment
        Hire
        LOA Start
        LOA Return
        Terminate

    It is assumed that all transactions MUST occurr between an 
    Hire and Termination event for any given employee

    If position id does not exist the program will look up the last 
    position for that employee and raise an exception if no position is found

    Go through file
    sort by date
    for each record
    if employee doesn't exist, create it
    if position doesn't exist, create it

"""
from __init__ import *

class Transaction(object):
    def __init__(self, date, ttype, emp, position, lineno):
        self._date = date
        self._ttype = ttype
        self._emp_id = emp
        self._position_id = position
        self._lineno = lineno
        self._pre_requisites = []
        self._to_position = None
        self._worker = None
        self._from_position = None
        self._valid = True
        if ttype == HIRE:
            self._from_position = PRE_HIRE
        if ttype == TERM:
            self._to_position = TERMED_EMP
        return

    def build_pre_req_list(self):
        return

    def invalidate(self):
        """ This transaction somehow is not valid """
        self._valid = False
        return

    @property
    def valid(self):
        return self._valid

    @property
    def from_position(self):
        return self._from_position
    @from_position.setter
    def from_position(self, position):
        if self._from_position != None:
            print("Trying to set from_position when it already exists")
            print("Trying to set it to: {}".format(position))
            print("Current value: {}".format(self._from_position))
            print(self)
            raise Exception
        self._from_position = position
    @property
    def to_position(self):
        return self._to_position
    @to_position.setter
    def to_position(self, pos):
        self._to_position = pos
        return
    @property
    def position_id(self):
        return self._position_id
    @property
    def worker(self):
        return self._worker
    @worker.setter
    def worker(self, worker):
        self._worker = worker
        return
    @property
    def emp_id(self):
        return self._emp_id
    @property
    def ttype(self):
        return self._ttype
    @property
    def date(self):
        return self._date

    """ Allows us to compare transactions for > < """
    def __lt__(self, other):
        if self.date == other.date: ret = self.ttype < other.ttype
        else: ret =  self.date < other.date
        return ret
    def __gt__(self, other):
        if self.date == other.date: ret = self.ttype > other.ttype
        else: ret =  self.date > other.date
        return ret
    def __ne__(self, other):
        if self.date != other.date: ret = self.ttype != other.ttype
        else: ret =  self.date != other.date
        return ret
    def __eq__(self, other):
        if self.date == other.date: ret = self.ttype == other.ttype
        else: ret =  self.date == other.date
        return ret
    def __le__(self, other):
        if self.date == other.date: ret = self.ttype <= other.ttype
        else: ret =  self.date <= other.date
        return ret
    def __ge__(self, other):
        if self.date == other.date: ret = self.ttype >= other.ttype
        else: ret =  self.date >= other.date
        return ret

    @staticmethod
    def header():
        return "Date, Employee ID, Position, Transaction Type, Worker Wave, Position Wave, Original line number"

    def __repr__(self):
        return "{},{},{},{},{} {}".format(
                self.date, self._emp_id, self._position_id, self._ttype,
                self._lineno, self._valid)