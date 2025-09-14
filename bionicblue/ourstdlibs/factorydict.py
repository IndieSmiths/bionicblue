"""Special collections for general use."""

class FactoryDict(dict):
    """Produces value in function of missing key."""

    def __init__(self, callable_obj):
        """Store callable used to create missing values.

        Whenever someone tries to access a missing key,
        this dict instance executes the callable with the
        missing key and uses the return value as the
        new value, which is stored in the dict and
        returned.
        """
        self.callable_obj = callable_obj

    def __missing__(self, key):
        value = self[key] = self.callable_obj(key)
        return value
