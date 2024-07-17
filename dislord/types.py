class ObjDict(dict):
    def __getattr__(self, name):
        try:
            return self.get(name)
        except KeyError:
            raise AttributeError(f"'ObjDict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __eq__(self, other):
        if isinstance(other, ObjDict):
            for k, v in self.items():
                if v != other.get(k):
                    return False
            return True
        else:
            return False
