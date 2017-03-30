
class Trans_Type(object):
    """
        This class is meant to represent iloads types, specifically it's used
        to allow for relative sequencing of different iloads based on load order
    """
    _types_list = []

    @classmethod
    def _add_type(cls, type):
        cls._types_list.append(type)
        return

    @classmethod
    def get_type(cls, type_str):
        """ Given a type string, return matching type. Return None if none found """
        ret = None
        for t in cls._types_list:
            if t.has_key(type_str):
                ret = t
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
        return

    def has_key(self, type_str):
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

