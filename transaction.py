"""
    The foundational class for this module. Transaction represents
    a transactoin and must have the basic elements
    of:
        employee id
        event date
        event type (TERM, HIRE, etc)
        position (if applicable)

"""
from __init__ import *

log_emp_ids = ["xx27059"]

class Transaction(object):

    _max_seq = 0
    _max_seq_t = None
    # Class method to track the longest sequence
    @classmethod
    def max_seq(cls, seq, t):
        if seq > cls._max_seq:
            cls._max_seq = seq
            cls._max_seq_t = t
        elif seq == cls._max_seq and cls._max_seq_t < t:
            cls._max_seq_t = t
        return

    _invalid_list = {}
    @classmethod
    def add_to_invalid_list(cls, t, msg):
        cls._invalid_list[t] = msg
        return

    @classmethod
    def get_invalid_transactions(cls,t):
        return cls._invalid_list


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
        """ 
            Given a list, return a copy that has only unique values 
            Keep order intact
        """
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
        if not self._valid:
            return []
        if not self._pre_reqs_calcd:
            # If my to_position is JOB_MGMT then we don't
            # have any dependencies on transactions from
            # position being a dependency
            if self._to_position.staffing_model != JOB_MGMT:
                for t in self._to_position.get_transactions():
                    if t < self:
                        self._pre_reqs += t.return_pre_reqs() + [t,]
            for t in self._worker.get_transactions():
                if t < self:
                    self._pre_reqs += t.return_pre_reqs() + [t,]
                else:
                    # Worker transactions are guaranteed to be sorted
                    # So once a transaction is > t, all will be
                    break
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
        """
        seq = 0
        last_type = None
        last_t = None
        for t in self._pre_reqs + [self]: # list sorted by date/type
            # It's fine to have 2 in a row or more of change job, org ass or loa
            # Break out logic for each type to be clear
            if t.ttype == CHANGE_JOB and last_type != CHANGE_JOB:
                seq += 1
            elif t.ttype == ORG_ASSN and last_type != ORG_ASSN:
                seq += 1
            elif t.ttype in [LOA_START, LOA_STOP] and last_type not in [LOA_START, LOA_STOP]:
                seq += 1
            elif t.ttype in [HIRE, TERM]:
                if t.ttype != last_type or last_t.emp_id == t.emp_id:
                    seq += 1
            t.assign_seq(seq)
            if seq < t.seq:
                seq = t.seq 
            last_type = t.ttype
            last_t = t

    def assign_seq(self, i):
        if self._seq < i:
            self._seq = i
            Transaction.max_seq(i, self)
        return

    def invalidate(self, msg):
        """ 
            This transaction somehow is not valid 
            Tell the worker and positions to remove it
        """
        self._valid = False
        if self._to_position is not None:
            self._to_position.remove_transaction(self)
        if self._from_position is not None:
            self._from_position.remove_transaction(self)
        if self._worker is not None:
            self._worker.remove_transaction(self)
        Transaction.add_to_invalid_list(self, msg)
        return

    @property
    def valid(self):
        return self._valid

    @property
    def from_position(self):
        return self._from_position
    @from_position.setter
    def from_position(self, position):
        if self._from_position is not None:
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
    @property
    def seq(self):
        return self._seq

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
        return "{},{},{},{},{} {} {}".format(
                self.date, self._emp_id, self._position_id, self._ttype,
                self._lineno, self._valid, self._seq)
