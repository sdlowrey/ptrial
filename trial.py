class Trial(object):
    """
    The context, systems, and observations associated with a trial.
    """
    def __init__(self, begin, end, purpose):
        self.begin = begin
        self.end = end
        self.purpose = purpose
        self.nodes = None
        self.observations = None
