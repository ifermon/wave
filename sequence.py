
class Sequence(object):
    """
        Generates sequences used for unique object ids. 
        Not yet implemented to be used in a multi-threaded env - would need to add locks
        Not yet implemneted to be used across program runs - would probably need hashing
        Not implemented to generate id based on object data (see hash)
    """

    def __init__(self, seq_name, seed=0, hashable=False):
        """ Set up the name and counter """
        self.__name = seq_name
        self.__cur_value = seed
        return

    def next(self):
        ret = self.__cur_value
        self.__cur_value += 1
        return ret
