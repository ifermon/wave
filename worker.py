"""
    Worker object representing a worker.

    TODO: Integrate logging
"""
from __init__ import *
from enum import Enum

# Log employees allows you to log information about a list of emp ids for debugging
log_employees = ["x62883"]

class Status(Enum):
    ON_LEAVE = 1
    ACTIVE = 2
    INACTIVE = 3

ACTIVE = Status.ACTIVE
INACTIVE = Status.INACTIVE
ON_LEAVE = Status.ON_LEAVE

class Worker(object):
    # Set to true if you want the worker to log all it's transactions
    _log_trans = False

    def __init__(self, emp_id):
        self._emp_id = emp_id
        self._tlist = []
        self._invalid_list = []
        self._sorted = False
        self._validated = False
        self._valid = True
        self.flag = False
        return

    def dump(self):
        """ Return a formatted string that contains all the info for this worker """
        ret_str = "Worker id {}\n".format(self._emp_id)
        ret_str += "\tValid = {}\tValidated = {}\tSorted = {}\tFlag = {}\n".format(
                self._valid, self._validated, self._sorted, self.flag)
        ret_str += "\tValid Transaction List:\n"
        for t in self._tlist:
            ret_str += "\t\t{}\n".format(t)
        ret_str += "\tInvalid Transaction List\n"
        for t in self._invalid_list:
            ret_str += "\t\t{}\n".format(t)
        ret_str += "\n"
        return ret_str


    def top_of_stack(self):
        """ 
            If the is a transaction list, return the last (greatest date
            / transaction type 
        """
        if self._tlist:
            self._sort()
            ret = self._tlist[-1]
        else:
            error("Worker with no valid transactions {}".format(self))
            ret = None
        return ret

    def ret_pre_reqs(self, trans):
        ret_list = []
        for t in self._tlist:
            ret_list += t.ret_pre_reqs(trans)
        return ret_list

    def add_transaction(self, transaction):
        self._tlist.append(transaction)
        self._sorted = False
        return

    def pos_as_of(self, as_of_date):
        """ Return the workers position as of the given date """
        self._sort()
        last_t = None
        ret = None
        for t in self._tlist:
            if t.date <= as_of_date:
                last_t = t
            else:
                # We need the position in the last transaction (last_t)
                if last_t is None:
                    ret = None
                else:
                    ret = last_t.to_position
                    break
        return ret


    def validate(self):
        try:
            self._validate()
        except Exception as e:
            print("Error in validate")
            print(self)
            raise e
        self._validated = True
        return

    def _validate(self):
        """
            Given a transaction, get the "from" position for that transaction
            and validate that we're not missing transactions as best we can
        """
        # Sort my transaction list
        self._sort()

        last_to_position = None
        last_type = TERM
        worker_status = INACTIVE
        if self._emp_id in log_employees:
            print("Worker: {} transactions:".format(self._emp_id))
            for t in self._tlist:
                print(t)
            print("\n")

        if self._tlist[0].ttype != HIRE:
            error("Invalid worker. First transaction is not hire")
            error("Worker {}".format(self))
            self._valid = False

        for t in self._tlist: # You should be going in date / type order

            if t.emp_id in log_employees:
                print("Enter: {}\n Worker status: {}".format(t,
                        worker_status))

            if t.ttype == HIRE:
                # Check to see if HIRE is valid sequentially
                if last_type != TERM and last_to_position is None:
                    print("For emp {}, HIRE trx out of order".format(
                            self._emp_id))
                    print("Last type = {} last to position = {}".format(
                            last_type, last_to_position))
                    print("Current trx \n\t{}".format(t))
                    print(self)
                    raise Exception
                # This should have a to, and from is PRE_HIRE
                worker_status = ACTIVE
                if t.to_position is None: # Only happens w/ job mgmt orgs
                    t.to_position = JOB_MGMT_POS
                if t.from_position is None:
                    t.from_position = PRE_HIRE
                last_to_position = t.to_position
                last_type = t.ttype

            elif t.ttype == TERM:
                # Term has no positions, use last position
                t.to_position = TERMED_EMP
                t.from_position = last_to_position
                last_to_position = TERMED_EMP
                worker_status = INACTIVE

            elif t.ttype in [ORG_ASSN, CHANGE_JOB]:
                # Should have a to position unless job mgmt
                if t.to_position is None: # Assume job mgmt
                    t.to_position = JOB_MGMT_POS
                if t.from_position is None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.ttype

            elif t.ttype == LOA_START:
                # should have position unless job mgmt
                if worker_status != ACTIVE:
                    t.invalidate("Start of LOA but worker is not active")
                else:
                    if not t.to_position:
                        if last_to_position:
                            t.to_position = last_to_position
                        else:
                            t.to_position = JOB_MGMT_POS
                    if not t.from_position:
                        t.from_position = last_to_position
                    last_to_position = t.to_position
                    last_type = t.ttype
                    worker_status = ON_LEAVE

            elif t.ttype == LOA_STOP:
                if worker_status != ON_LEAVE:
                    t.invalidate("End of LOA but worker was not on LOA")
                else:
                    worker_status = ACTIVE
                    # should have position unless job mgmt
                    if not t.to_position:
                        if last_to_position:
                            t.to_position = last_to_position
                        else:
                            t.to_position = JOB_MGMT_POS
                    if not t.from_position:
                        t.from_position = last_to_position
                    last_to_position = t.to_position
                    last_type = t.ttype

            if t.emp_id in log_employees:
                print("Exit : {}\n {}\n".format(t, worker_status))

            if not self._tlist:
                self._valid = False

        return # END _validate

    def remove_transaction(self, trans):
        if trans in self._tlist:
            # Need a new list in case we are iterating through old one
            self._tlist = list(self._tlist)
            self._tlist.remove(trans)
            self._invalid_list.append(trans)
        return

    def _sort(self):
        if not self._sorted and len(self._tlist) != 0:
                self._tlist.sort()
                self._tlist[-1].top_of_stack = True
        self._sorted = True
        return

    def get_transactions(self):
        self._sort()
        return self._tlist

    @property
    def emp_id(self):
        return self._emp_id
    @property
    def valid(self):
        return self._valid

    @property
    def max_seq(self):
        self._sort()
        if len(self._tlist) == 0:
            ret = 0
        else:
            ret = self._tlist[-1].seq
        return ret

    def __repr__(self):
        if Worker._log_trans:
            tstr = "\n\t".join([ str(t) for t in self._tlist ])
            ret_str = "Emp id {}\nTransactions:\n\t{}".format(
                self._emp_id, tstr)
        else:
            ret_str = "Emp id {} {}".format(self._emp_id, self._valid)

        return ret_str

