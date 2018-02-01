from __init__ import *

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

    _max_seq = -1
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
    def get_invalid_list_msg(cls):
        return cls._invalid_list.items()

    @classmethod
    def get_invalid_transactions(cls):
        return cls._invalid_list

    @classmethod
    def header(cls):
        return "Record #, Emp ID, Seq, Date, Type, To Pos, To Pos Staffing, From Pos, From Pos Staffing, Line no, Valid Flag"


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
        self._invalid_msg = "Valid Transaction"
        self._pre_reqs = []
        self.__pos_pre_reqs = []
        self.__worker_pre_reqs = []
        self._pre_reqs_calcd = False
        self.__seq_calcd = False
        self._seq = 0
        self._top_of_stack = False
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
        ret_str += "\n"
        return ret_str

    def output(self):
        """ Generates output string for comma delimited output files """
        try:
            """
            output = "{},{},{},{},{},{},{},{},{},{}".format(
                    self._rec_number, self._emp_id, self._seq, self._date,
                    self._ttype, self._position_id, self._to_position.pos_id,
                    self._from_position.pos_id, self._lineno, 
                    self._valid)
            """
            output = "{},{},{},{},{},{},{},{},{},{},{}".format(
                self._rec_number, self._worker.emp_id, self._seq, self._date,
                self._ttype, self._to_position.pos_id, self._to_position.staffing_model,
                self._from_position.pos_id, self._from_position.staffing_model, self._lineno,
                self._valid)
        except Exception as e:
            print("Error outputting transaction")
            print(self)
            raise e
        return output

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

    def return_pre_reqs(self):
        """
            Build list of transactions that must be completed before this one.
            Go through each transaction for to_position
            And then for worker
            If you think of the dependencies as a graph, with a transaction as a node,
            each node can only have two edges to the next transaction. One is the worker edge,
            the other is the position edge
        """
        if not self._valid:
            return []

        if not self._pre_reqs_calcd:
            # Get the position based pre-reqs (pt)
            if self._to_position.staffing_model != JOB_MGMT:
                pt = self._to_position.get_prior_transaction(self)
                if pt:
                    self.__pos_pre_reqs += pt.return_pre_reqs() + [pt, ]
            # Get the worker based pre-reqs (wt)
            wt = self._worker.get_prior_transaction(self)
            if wt:
                self.__worker_pre_reqs += wt.return_pre_reqs() + [wt, ]
            self._pre_reqs = self.__pos_pre_reqs + self.__worker_pre_reqs
            self._pre_reqs = Transaction._uniquify(self._pre_reqs)
            self._pre_reqs.sort()
        self._pre_reqs_calcd = True
        return self._pre_reqs

    def set_final_term_seq(self):
        """ Used to set the sequence when we want final terms in a final file """
        # Made this less generic so it would not be used incorrectly as the
        # sequence logic is very complicated
        if self._ttype is TERM:
            self._seq = Transaction._max_seq
        return


    def get_seq(self):
        """ Return seq, perform needed functions """
        if not self._pre_reqs_calcd:
            error("Called get_seq with no pre-reqs calcd")
            self.return_pre_reqs()
        if self.__seq_calcd:
            ret = self._seq
        else:
            ret = self._calc_seq()
        return ret

    def __derive_seq(self, t):
        """ Given a transaction, return the next seq value which will always 
            be equal or +1
        """
        t_seq = t.get_seq()
        if t.ttype > self.ttype:
            # LOA start and stop are a special case
            if t.ttype not in [LOA_START, LOA_STOP] or self.ttype not in [LOA_START, LOA_STOP]:
                t_seq += 1
        elif t.ttype == self.ttype:
            # Trans types that can't have more than one row per file
            # Job change can't have more than one because we expect a matching
            # assign org
            if self.ttype in [HIRE, TERM, CHANGE_JOB]:
                t_seq += 1
        return t_seq

    def _calc_seq(self):
        """
            For each transaction in _pre_reqs list, assign a sequence
            For each edge, look at the last seq and calc accordingly
        """
        if not self._pre_reqs_calcd:
            self.return_pre_reqs()
        if not self.__worker_pre_reqs:
            w_seq = 0
        else:
            # get the seq of the previous trans on the worker edge
            # get_seq causes seq to be calculated (vs. just property seq)
            w_t =  self.__worker_pre_reqs[-1]
            w_seq = self.__derive_seq(w_t)
        if not self.__pos_pre_reqs:
            p_seq = 0
        else:
            # get seq of previous trans on position edge
            p_t = self.__pos_pre_reqs[-1]
            p_seq = self.__derive_seq(p_t)
        self._seq = max(w_seq, p_seq)
        Transaction.max_seq(self._seq, self)
        self.__seq_calcd = True
        return self._seq

    def invalidate(self, msg):
        """ 
            This transaction somehow is not valid 
            Tell the worker and positions to remove it
        """
        self._valid = False
        if self._to_position: self._to_position.remove_transaction(self)
        else: self._to_position = DUMMY

        if self._from_position: self._from_position.remove_transaction(self)
        else: self._from_position = DUMMY

        if self._worker: self._worker.remove_transaction(self)

        self._ttype.add_to_invalid_list(self)
        Transaction.add_to_invalid_list(self, msg)
        self._invalid_msg = msg
        self._seq = -1
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
        position_obj.add_transaction(self)
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
        if self._rec_number:
            ret = int(self._rec_number)
        else:
            ret = int(self._lineno)
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
                if self.from_position == other.to_position:
                    ret = True
                else:
                    ret = False
            else: ret = self.ttype < other.ttype
        else: ret =  self.date < other.date
        return ret
    def __gt__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                if self.from_position == other.to_position:
                    ret = False
                else:
                    ret = True
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
                if self.from_position == other.to_position:
                    ret = True
                else:
                    ret = self.lineno <= other.lineno
            else: ret = self.ttype < other.ttype
        else: ret =  self.date <= other.date
        return ret
    def __ge__(self, other):
        if self.date == other.date:
            if self.ttype == other.ttype:
                if self.from_position == other.to_position:
                    ret = False
                else:
                    ret = self.lineno >= other.lineno
            else:
                ret = self.ttype >= other.ttype
        else: ret =  self.date >= other.date
        return ret

    def test_str(self):
        return "Employee id: {}\nPosition id: {}\nTransaction Type: {}\nDate: {}\n".format(
                self._emp_id, self._position_id, self._ttype, self._date)

    def __repr__(self):
        return "{}, {}, {}, {}, {}, {}, {}, {}".format(
                self._date, self._emp_id, self._position_id,
                self._ttype, self._lineno, self._valid, self._seq, self._top_of_stack)
