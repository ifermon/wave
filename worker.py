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
from enum import Enum

# Log employees allows you to log information about a list of emp ids for debugging
log_employees = ["20230",]

class Status(Enum):
    ON_LEAVE = 1
    ACTIVE = 2
    INACTIVE = 3

ACTIVE = Status.ACTIVE
INACTIVE = Status.INACTIVE
ON_LEAVE = Status.ON_LEAVE

class Worker(object):
    def __init__(self, emp_id):
        self._emp_id = emp_id
        self._tlist = []
        self._invalid_list = []
        self._sorted = False
        return

    def add_transaction(self, transaction):
        self._tlist.append(transaction)
        return

    def validate(self):
        try:
            self._validate()
        except:
            print("Error in validate")
            print(self)
            raise Exception
        return

    def _validate(self):
        """
            Given a transaction, get the "from" position for that transaction
            and validate that we're not missing tranactions as best we can
        """
        # Sort my transaction list
        if self._sorted == False:
            self._tlist.sort()
            self._sorted = True

        last_to_position = None
        last_type = TERM
        worker_status = INACTIVE
        for t in self._tlist: # You should be going in date / type order

            if t.emp_id in log_employees:
                print("Enter with last to: [{}] last type: [{}] worker status [{}]".format(
                        last_to_position, last_type, worker_status))
                print("\tt.to_position: {}".format(t.to_position))
                print("Enter: {}".format(t))

            if t.ttype == HIRE:
                # Check to see if HIRE is valid sequentially
                if last_type != TERM and last_to_position == None:
                    print("For emp {}, HIRE trx out of order".format(
                            self._emp_id))
                    print("Last type = {} last to position = {}".format(
                            last_type, last_to_position))
                    print("Current trx \n\t{}".format(t))
                    print(self)
                    raise Exception
                # This should have a to, and from is PRE_HIRE
                worker_status = ACTIVE
                if t.to_position == None: # Only happens w/ job mgmt orgs
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
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
                if t.to_position == None: # Assume job mgmt
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.ttype

            elif t.ttype == LOA_START:
                # should have position unless job mgmt
                if worker_status == INACTIVE:
                    t.invalidate()
                    self._invalid_list.append(t)
                    self._tlist.remove(t)
                    continue
                # Remove it from our list, and add it to bad list
                if t.to_position == None:
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.ttype
                worker_status = ON_LEAVE

            elif t.ttype == LOA_STOP:
                """
                This is not true right now. There are org changes
                for anyone who was on leave through 6/1 on 6/1
                if last_type != LOA_START:
                    print("For emp {}, LOA STOP trx out of order".format(
                            self._emp_id))
                    print("Current trx {}".format(t))
                    print(self)
                    raise Exception
                """
                if worker_status != ON_LEAVE:
                    t.invalidate()
                    self._invalid_list.append(t)
                    self._tlist.remove(t)
                    continue
                worker_status = ACTIVE
                # should have position unless job mgmt
                if t.to_position == None:
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.ttype

            if t.emp_id in log_employees:
                print("Exit : {}".format(t))
                print("\tt.to_position: {}".format(t.to_position))
                print("Exit with last to: [{}] last type: [{}] worker status {}\n".format(
                        last_to_position, last_type, worker_status))
        return







    def get_to_position(self, transaction):
        pass

    @property
    def transaction_list(self):
        return self._tlist

    @property
    def emp_id(self):
        return self._emp_id

    def __repr__(self):
        tstr = "\n\t".join([ str(t) for t in self._tlist ])
        ret_str = "Emp id {}\nTransactions:\n\t{}".format(
                self._emp_id, tstr)
        return ret_str

