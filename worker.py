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

class Worker(object):
    def __init__(self, emp_id):
        self._emp_id = emp_id
        self._tlist = []
        self._sorted = False
        return

    def validate(self, transaction):
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
        for t in self._tlist: # You should be going in date / type order

            if t.ttype == HIRE:
                # Check to see if HIRE is valid sequentially
                if last_type != TERM and last_to_position == None:
                    print("For emp {}, HIRE trx out of order".format(
                            self._emp_id))
                    print("Current trx {}".format(t))
                    print(self._tlist)
                    raise Exception
                # This should have a to, and from is PRE_HIRE
                if t.to_position == None: # Only happens w/ job mgmt orgs
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = PRE_HIRE
                last_to_position = t.to_position
                last_type = t.tttype

            elif t.ttype in [ORG_ASSN, CHANGE_JOB]:
                # Should have a to position unless job mgmt
                if t.to_position == None: # Assume job mgmt
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.tttype

            elif t.ttype == LOA_START:
                # should have position unless job mgmt
                if t.to_position == None:
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.tttype

            elif t.ttype == LOA_STOP:
                if last_type != LOA_START:
                    print("For emp {}, LOA STOP trx out of order".format(
                            self._emp_id))
                    print("Current trx {}".format(t))
                    print(self._tlist)
                    raise Exception
                # should have position unless job mgmt
                if t.to_position == None:
                    t.to_position = JOB_MGMT_POS
                if t.from_position == None:
                    t.from_position = last_to_position
                last_to_position = t.to_position
                last_type = t.tttype
        return







    def get_to_position(self, transaction):
        pass

    @property
    def transaction_list(self):
        return self._tlist

    @property
    def emp_id(self):
        return self._emp_id

