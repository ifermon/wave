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
from staffing_model import Staffing_Models


class Position(object):

    def __init__(self, pos_id, staffing=Staffing_Models.POSITION_MGMT):
        self._pos_id = pos_id
        self._staffing = staffing
        self._tlist = []
        self._sorted = False
        return

    def add_transaction(self, trans):
        self._tlist.append(trans)
        self._sorted = False
        return

    @property
    def staffing_model(self):
        return self._staffing
    @property
    def pos_id(self):
        return self._pos

    def __repr__(self):
        if self._staffing == Staffing_Models.POSITION_MGMT:
            tstr = "\n\t".join([ str(t) for t in self._tlist ])
        else:
            tstr = "Job Management Org, not listing transactions"
        ret_str = "Pos id: [{}] Staffing: [{}]\nTransactions:\n\t[{}]".format(
                self._pos_id, self._staffing, tstr)
        return ret_str
