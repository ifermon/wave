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

log_emp_ids= ["19292"]

class Transaction(object):

    # Class variable containing the maximum sequence value
    _max_seq = 0

    def __init__(self, date, ttype, emp, position, lineno):
        self._date = date
        self._ttype = ttype
        self._emp_id = emp
        self._position_id = position
        self._lineno = lineno
        self._to_position = None
        self._worker = None
        self._from_position = None
        self._valid = True
        self._pre_reqs = []
        self._pre_reqs_calcd = False
        self._seq = 0
        if ttype == HIRE:
            self._from_position = PRE_HIRE
        if ttype == TERM:
            self._to_position = TERMED_EMP
        return

    def output(self):
        try:
            str = "{},{},{},{},{},{},{},{},{}".format(
                    self._emp_id, self._date, self._ttype,
                    self._position_id, self._to_position.pos_id, 
                    self._from_position.pos_id, self._lineno, 
                    self._valid, self._seq)
        except Exception as e: 
            print("Error outputting transaction")
            print(self)
            raise e
        return str

    @staticmethod
    def _uniquify(l):
        """ Given a list, return a copy that has only unique values """
        keys = {}
        for i in l:
            keys[i] = 1
        return keys.keys()

    def return_pre_reqs(self):
        """
            Build list of transactions that must be completed before this one.
            Go through each transaction for to_position
            And then for worker
        """
        if not self._pre_reqs_calcd:
            if self._to_position.staffing_model != JOB_MGMT:
                for t in self._to_position.get_transactions():
                    if t < self:
                        self._pre_reqs += t.return_pre_reqs() + [t,]
            for t in self._worker.get_transactions():
                if t < self:
                    self._pre_reqs += t.return_pre_reqs() + [t,]
                if self._emp_id in log_emp_ids:
                    print("In pre-reqs")
                    print(self)
                    print(str("\n".join([str(t) for t in self._pre_reqs])))
                self._pre_reqs = Transaction._uniquify(self._pre_reqs)
                if len(self._pre_reqs) > 0: # Sorting empty list returns None
                    self._pre_reqs.sort()
                self._calc_seq()
                self._pre_reqs_calcd = True
        ret_list = self._pre_reqs
        return ret_list

    def _calc_seq(self):
        """
            For each transaction in _pre_reqs list, assign a sequence
        :return:
        """
        seq = 0
        last_type = None
        for t in self._pre_reqs: # list sorted by date/type
            if t.emp_id in log_emp_ids:
                print(t)
            # It's fine to have 2 in a row or more of change job, org ass or loa
            if not (last_type in [CHANGE_JOB, ORG_ASSN, LOA_START, LOA_STOP] and
                    last_type == t.ttype):
                seq += 1
            t.assign_seq(seq)

    def assign_seq(self, i):
        if self._seq < i:
            self._seq = i
            if Transaction._max_seq < i:
                Transaction._max_seq = i
        return

    def invalidate(self):
        """ 
            This transaction somehow is not valid 
            Tell the worker and positions to remove it
        """
        self._valid = False
        if self._to_position != None:
            self._to_position.remove_transaction(self)
        if self._from_position != None:
            self._from_position.remove_transaction(self)
        if self._worker != None:
            self._worker.remove_transaction(self)
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

    @classmethod
    def max_seq(cls, seq):
        if cls._max_seq < seq:
            cls._max_seq = seq
        return

    @staticmethod
    def header():
        return "Date, Employee ID, Position, Transaction Type, Worker Wave, Position Wave, Original line number"

    def __repr__(self):
        return "{},{},{},{},{} {}".format(
                self.date, self._emp_id, self._position_id, self._ttype,
                self._lineno, self._valid)
