from staffing_model import Staffing_Models
import __init__

class Position(object):
    """
        Represents a Position. Used to keep track of position related
        dependencies between transactions
    """

    # Set this to true if you want it to log transactions
    _log_trans = False
    _anonymize = False

    @classmethod
    def anonymize(cls):
        cls._anonymize = True
        return

    def __init__(self, pos_id, staffing=Staffing_Models.POSITION_MGMT):
        self._pos_id = pos_id
        self._staffing = staffing
        self._tlist = []
        self._invalid_list = []
        self._sorted = False
        self._key = "P{:06d}".format(__init__.position_seq.next())
        return

    def dump(self):
        """ Return formatted string with all position data """
        ret_str = "Position id {}\n".format(self._pos_id)
        ret_str += "\tStaffing Model = {}\tSorted = {}\t\n".format(
                self._staffing, self._sorted)
        ret_str += "\tValid Transaction List:\n"
        for t in self._tlist:
            ret_str += "\t\t{}\t\n".format(t)
        ret_str += "\tInvalid Transaction List:\n"
        for t in self._invalid_list:
            ret_str += "\t\t{}\t\n".format(t)
        ret_str += "\n"
        return ret_str

    def _sort(self):
        if not self._sorted and self._tlist:
            self._tlist.sort()
        self._sorted = True
        return

    def top_of_stack(self):
        """ Return the top of stack transaction """
        if self._tlist:
            self._sort()
            ret = self._tlist[-1]
        else: ret = None
        return ret

    def validate(self):
        """ Validate that the position is available when someone moves into it """
        if self._staffing is not Staffing_Models.JOB_MGMT:
            self._sort()
            w = None
            for t in self._tlist:
                if not w:
                    w = t.worker
                if t.worker is not w:
                    # We have a change in worker, check to see that prior worker moved
                    p = w.pos_as_of(t.date)
                    if p is self:
                        __init__.info("Problem Transaction:\n\t{}".format(t))
                        __init__.info(self.dump())
                    if __init__.stop_on_validation:
                            raise Exception
                    w = t.worker
        return

    def get_prior_transaction(self, t):
        """ Given a transaction t, return the item immediately preceding it from trans list 
            If item not in trans list, return None
            If it is the first item in the list, return None
        """
        if not self._sorted:
            self._sort()
        if t not in self._tlist:
            ret = None
        else:
            i = self._tlist.index(t)
            if i is 0:
                ret = None
            else:
                ret = self._tlist[i-1]
        return ret

    def add_transaction(self, trans):
        """ Add a transaction to the list of transactions that involve this position """
        self._tlist.append(trans)
        self._sorted = False
        return

    def get_transactions(self):
        """ Returns list of transactions, always sorted """
        self._sort()
        return self._tlist

    def remove_transaction(self, trans):
        """ If transaction is in our list, moves it to "invalid" list and out of tlist """
        if trans in self._tlist:
            self._tlist.remove(trans)
            self._invalid_list.append(trans)
        return

    @property
    def staffing_model(self):
        """ Returns the staffing model of this position """
        return self._staffing

    @property
    def pos_id(self):
        """ Returns the ID of this position """
        if Position._anonymize:
            ret = self._key
        else:
            ret = self._pos_id
        return ret


    def __repr__(self):
        if self._staffing == Staffing_Models.POSITION_MGMT:
            tstr = "\n\t".join([str(t) for t in self._tlist])
        else:
            tstr = "Job Management Org, not listing transactions"

        if Position._log_trans:
            ret_str = ("Pos id: [{}] Staffing: [{}]\nTransactions:" 
                       "\n\t[{}]").format(self._pos_id, self._staffing, tstr)
        else:
            ret_str = "Pos id: [{}] Staffing: [{}]\n".format(self._pos_id, self._staffing)
        return ret_str
