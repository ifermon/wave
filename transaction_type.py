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

class Trans_Type(object):
    def __init__(self, trans_type, seq):
        self.ttype = trans_type
        self._seq = seq
        return
    def __lt__(self, other):
        return self.seq < other.seq
    def __gt__(self, other):
        return self.seq > other.seq
    def __ne__(self, other):
        return self.seq != other.seq
    def __eq__(self, other):
        return self.seq == other.seq
    def __le__(self, other):
        return self.seq <= other.seq
    def __ge__(self, other):
        return self.seq >= other.seq

    def __str__(self):
        return self.ttype

    @property
    def ttype(self):
        return self._ttype
    @ttype.setter
    def ttype(self, ttype):
        self._ttype = ttype
        return

    @property
    def seq(self):
        return self._seq

