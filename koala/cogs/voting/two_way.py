class TwoWay(dict):
    """Makes a dict a bijection"""
    def __init__(self, dict_in=None):
        """
        Constructor method
        :param dict_in: an existing dict to make two-way
        """
        super(TwoWay, self).__init__()
        if dict_in is not None:
            self.update(dict_in)

    def __delitem__(self, key):
        """
        Remove an item from the dict
        :param key: the key of the item
        """
        self.pop(self.pop(key))

    def __setitem__(self, key, value):
        """
        Add an item to the dict. Errors if it already exists
        :param key: the key of the item to add
        :param value: the value of the item to add
        """
        assert key not in self or self[key] == value
        super(TwoWay, self).__setitem__(key, value)
        super(TwoWay, self).__setitem__(value, key)

    def update(self, e, **f):
        """
        Update the dict
        :param e: new dict to integrate into the existing one
        :param f: keyword arguments
        """
        for key, value in e.items():
            assert key not in self or self[key] == value
            self[key] = value
