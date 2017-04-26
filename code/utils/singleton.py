# as suggested in http://stackoverflow.com/a/6798042/3363866
class Singleton(type):
    """
    Implementation of the singleton pattern to be used as a meta class.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            if len(kwargs) > 0:
                print('WARNING: arguments ' + str(kwargs) + ' ignored since existing singleton instance is returned')
        return cls._instances[cls]