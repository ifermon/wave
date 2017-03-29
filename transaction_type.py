
class Trans_Type(object):
    """
        This class is meant to represent iloads types, specifically it's used
        to allow for relative sequencing of different iloads based on load order
    """
    def __init__(self, trans_type, seq):
        self._ttype = trans_type
        self._seq = seq
        return
    def __lt__(self, other):
        return self.seq < other.seq
    def __gt__(self, other):
        return self.seq > other.seq
    def __ne__(self, other):
        if other is None: ret = True
        else: ret = self.seq != other.seq
        return ret
    def __eq__(self, other):
        if other is None: ret = False
        else: ret = self.seq == other.seq
        return ret
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

