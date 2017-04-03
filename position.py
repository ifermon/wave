from staffing_model import Staffing_Models

class Position(object):
    """
        Represents a Position. Used to keep track of position related
        dependencies between transactions
    """

    # Set this to true if you want it to log transactions
    _log_trans = False

    def __init__(self, pos_id, staffing=Staffing_Models.POSITION_MGMT):
        self._pos_id = pos_id
        self._staffing = staffing
        self._tlist = []
        self._invalid_list = []
        self._sorted = False
        return

    def add_transaction(self, trans):
        """ Add a transaction to the list of transactions that involve this position """
        self._tlist.append(trans)
        self._sorted = False
        return

    def get_transactions(self):
        """ Returns list of transactions, always sorted """
        if not self._sorted:
            self._tlist.sort()
            self._sorted = True
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
        return self._pos_id


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
