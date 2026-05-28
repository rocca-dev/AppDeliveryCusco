class Serializable:
    def to_dict(self):
        if hasattr(self, '_campos'):
            return self._campos()
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
