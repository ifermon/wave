
class Trans_Type(object):
    """
        This class is meant to represent iloads types, specifically it's used
        to allow for relative sequencing of different iloads based on load order
    """
    _types_list = []
    _seq_list = []

    @classmethod
    def _add_type(cls, ttype):
        cls._types_list.append(ttype)
        if ttype.seq in cls._seq_list:
            print("Trying to add duplicate sequenced for type {}".format(ttype))
            raise
        else:
            cls._seq_list.append(ttype.seq)
        return

    @classmethod
    def all_types(cls):
        """ Returns an iterable of all defined types """
        return sorted(cls._types_list)

    @classmethod
    def get_type(cls, type_str):
        """ Given a type string, return matching type. Return None if none found """
        ret = None
        for tt in cls._types_list:
            if type_str in tt:
                ret = tt
                break
        return ret

    def __init__(self, trans_type, seq, keywords):
        self._keywords = []
        if isinstance(keywords, basestring):
            self._keywords.append(keywords)
        else:
            for e in keywords:
                self._keywords.append(e)
        self._ttype = trans_type
        self._seq = seq
        Trans_Type._add_type(self)
        self._transaction_list = []
        self._invalid_list = []
        self._record_sorted_list = []
        return

    def get_ordered_transactions(self, include_bad=True):
        """ Return a list of transactions sorted by record number """
        if len(self._record_sorted_list) == 0:
            self._record_sorted_list = sorted(self._transaction_list, key= lambda t: t.rec_sort_id)
        return self._record_sorted_list

    def add_to_invalid_list(self, t):
        """ Add to a list of invalid transactions """
        self._invalid_list.append(t)
        return

    def add_transaction(self, t):
        """ keep a list of all transactions of this type """
        self._transaction_list.append(t)
        return

    @property
    def total_count(self):
        """ Return the number of transactions of this type """
        return len(self._transaction_list)

    @property
    def good_count(self):
        return len(self._transaction_list) - len(self._invalid_list)

    @property
    def bad_count(self):
        return len(self._invalid_list)

    def __contains__(self, type_str):
        """ Return true if this type has key of type_str """
        ret = False
        if type_str in self._keywords:
            ret = True
        return ret

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
    def __repr__(self):
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

