from __init__ import *
from sets import Set

log_emp_ids = ["xx27059"]

class Transaction(object):
    """
        The foundational class for this module. Transaction represents
        a transaction and must have the basic elements
        of:
            employee id
            event date
            event type (TERM, HIRE, etc)
            position (if applicable)

    """

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
    def get_invalid_transactions(cls):
        return cls._invalid_list

    def __init__(self, date, ttype, emp, position_id, lineno, rec_number=None):
        self._date = date
        self._ttype = ttype
        self._emp_id = emp
        self._position_id = position_id
        self._lineno = lineno
        self._rec_number = rec_number
        self._to_position = None
        self._worker = None
        self._from_position = None
        self._valid = True
        self._pre_reqs = []
        self._pre_reqs_calcd = False
        self._seq_change_notification_list = Set()
        self._seq = 0
        self._top_of_stack = False
        self.__sequence_calc_in_progress = False
        if ttype == HIRE:
            self._from_position = PRE_HIRE
        if ttype == TERM:
            self._to_position = TERMED_EMP
        return

    def dump(self):
        """ Generates formatted text string of all transaction attributes """
        ret_str = "Transaction lineno {}\n".format(self._lineno)
        ret_str += "\tDate = {}\tTtype = {}\tEmp ID = {}\n".format(
                self._date, self._ttype, self._emp_id)
        ret_str += "\tPosition ID = {}\tRecord Number = {}\tSeq = {}\n".format(
                self.position_id, self._rec_number, self._seq)
        ret_str += "\tValid = {}\tPre-Reqs-Calcd = {}\tTop of Stack = {}\n".format(
                self._valid, self._pre_reqs_calcd, self._top_of_stack)
        ret_str += "\tWorker:\n\t\t{}\n".format(self.worker)
        ret_str += "\tTo Position:\n\t\t{}\n".format(self._to_position)
        ret_str += "\tFrom Position:\n\t\t{}\n".format(self._from_position)
        ret_str += "\tPre-reqs:\n"
        for t in self._pre_reqs:
            ret_str += "\t\t{}\n".format(t)
        ret_str += "\tSequence Change Notification List:\n"
        for t in self._seq_change_notification_list:
            ret_str += "\t\t{}\n".format(t)
        ret_str += "\n"
        return ret_str

    def output(self):
        """ Generates output string for comma delimited output files """
        try:
            output = "{},{},{},{},{},{},{},{},{}".format(
                    self._emp_id, self._date, self._ttype,
                    self._position_id, self._to_position.pos_id, 
                    self._from_position.pos_id, self._lineno, 
                    self._valid, self._seq)
        except Exception as e: 
            print("Error outputting transaction")
            print(self)
            raise e
        return output

    def validate_sequencing(self):
        if self._pre_reqs_calcd:
            for t in self._pre_reqs:
                if t.seq > self._seq:
                    print("Invalid sequencing")
                    print("Trans: ")
                    print("\t{}".format(self))
                    print("Conflict:")
                    print("\t{}".format(t))
        else:
            error("Trying to validate sequencing prior to validation")
            raise Exception
        return

    @staticmethod
    def _uniquify(my_list):
        """ 
            Given a list, return a copy that has only unique values 
            Keep order intact
        """
        keys = {}
        for i in my_list:
            keys[i] = 1
        return keys.keys()

    def notify_seq_change(self):
        """ Process notification that one of our pre-req transactions have changed their sequence """
        if not self._pre_reqs_calcd:
            self.return_pre_reqs()
        else:
            self._calc_seq()

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
                    if not t.valid:
                        continue
                    if t < self:
                        self._pre_reqs += t.return_pre_reqs() + [t, ]
            for t in self._worker.get_transactions():
                if not t.valid:
                    continue
                if t < self:
                    self._pre_reqs += t.return_pre_reqs() + [t, ]
                else:
                    # Worker transactions are guaranteed to be sorted
                    # So once a transaction is > t, all will be
                    break
            self._pre_reqs = Transaction._uniquify(self._pre_reqs)
            if self._pre_reqs:  # Sorting empty list returns None
                self._pre_reqs.sort()
            if self._top_of_stack:
                self._calc_seq()
            self._pre_reqs_calcd = True
        ret_list = self._pre_reqs
        if self._top_of_stack:
            for t in self._pre_reqs:
                t.sub_seq_change(self)
        return ret_list

    def sub_seq_change(self, sub):
        """ Register other transactions to notify if you change seq """
        if sub is not self:
            self._seq_change_notification_list.add(sub)
        return

    def _calc_seq(self):
        """
            For each transaction in _pre_reqs list, assign a sequence
        """
        if not self.__sequence_calc_in_progress:
            seq = 0
            self.__sequence_calc_in_progress = True
            last_type = None
            last_trans = None
            for t in self._pre_reqs + [self]:  # list sorted by date/type
                # It's fine to have 2 in a row or more of change job, org ass or loa
                # Break out logic for each type to be clear
                if t.ttype is CHANGE_JOB and last_type is not CHANGE_JOB:
                    seq += 1
                elif t.ttype is ORG_ASSN and last_type is not ORG_ASSN:
                    seq += 1
                elif t.ttype is LOA_START and last_type is not LOA_STOP:
                    seq += 1
                elif t.ttype is LOA_STOP and last_type is not LOA_START:
                    # This should never happen, but increment sequence
                    seq += 1
                elif t.ttype is HIRE:
                    # Assuming that we always start with hire- no actions before hire
                    #  If last_type isn't none we always increment sequence
                    if last_type and (last_type is not HIRE or last_trans.worker is t.worker):
                        seq += 1
                elif t.ttype is TERM:
                    seq += 1
                seq = t.assign_seq(seq)
                last_type = t.ttype
                last_trans = t
            self.__sequence_calc_in_progress = False
        return

    def assign_seq(self, i):
        """ Assign a sequence. """
        if self._seq < i:
            self._seq = i
            Transaction.max_seq(i, self)
            for t in self._seq_change_notification_list:
                t.notify_seq_change()
        return self._seq

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
        self._ttype.add_to_invalid_list(self)
        Transaction.add_to_invalid_list(self, msg)
        return

    @property
    def valid(self):
        return self._valid

    @property
    def from_position(self):
        return self._from_position
    @from_position.setter
    def from_position(self, position_obj):
        if self._from_position is not None:
            print("Trying to set from_position when it already exists")
            print("Trying to set it to: {}".format(position))
            print("Current value: {}".format(self._from_position))
            print(self)
            raise Exception
        self._from_position = position_obj
        return
    @property
    def to_position(self):
        return self._to_position
    @to_position.setter
    def to_position(self, pos):
        self._to_position = pos
        # If there is no position id, probably job mgmt
        if not self._position_id:
            self._position_id = pos.pos_id
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
    @property
    def rec_sort_id(self):
        """ Return record # if exists, otherwise lineno"""
        if self._rec_number is not None:
            ret = self._rec_number
        else:
            ret = self._lineno
        return ret
    @property
    def top_of_stack(self):
        return self._top_of_stack
    @top_of_stack.setter
    def top_of_stack(self, flag):
        self._top_of_stack = flag
        return
    @property
    def lineno(self):
        return self._lineno

    """ Allows us to compare transactions for > < """
    def __lt__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                ret = self.lineno < other.lineno
            else: ret = self.ttype < other.ttype
        else: ret =  self.date < other.date
        return ret
    def __gt__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                ret = self.lineno > other.lineno
            else: ret = self.ttype > other.ttype
        else: ret =  self.date > other.date
        return ret
    def __ne__(self, other):
        if self.date == other.date and self.ttype == other.ttype and self.lineno == other.lineno:
            ret = False
        else: ret =  True
        return ret
    def __eq__(self, other):
        if self.date == other.date and self.ttype == other.ttype and self.lineno == other.lineno:
            ret = True
        else: ret =  False
        return ret
    def __le__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                ret = self.lineno <= other.lineno
            else: ret = self.ttype < other.ttype
        else: ret =  self.date <= other.date
        return ret
    def __ge__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                ret = self.lineno >= other.lineno
            else:
                ret = self.ttype >= other.ttype
        else: ret =  self.date >= other.date
        return ret

    @staticmethod
    def header():
        return "Date, Employee ID, To Position, Transaction Type, Line Number, Valid?, Sequence"

    def test_str(self):
        return "Employee id: {}\nPosition id: {}\nTransaction Type: {}\nDate: {}\n".format(
                self._emp_id, self._position_id, self._ttype, self._date)

    def __repr__(self):
        return "{}, {}, {}, {}, {}, {}, {}, {}".format(
                self._date, self._emp_id, self._position_id,
                self._ttype, self._lineno, self._valid, self._seq, self._top_of_stack)
