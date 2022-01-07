class Anand(MemoryOnePlayer):
    """
    Uses a zero-determinant strategy for extortion.
    """

    # These are various properties for the strategy
    name = 'Anand'
    classifier = {
        'memory_depth': 1,  # Four-Vector = (1.,0.,1.,0.)
        'stochastic': True,
        'inspects_source': False,
        'manipulates_source': False,
        'manipulates_state': False
    }
    
    def __init__(self) -> None:
        super().__init__()

    def set_initial_four_vector(self, four_vector):
        pass

    def receive_match_attributes(self):
        p1 = 7/9
        p2 = 0
        p3 = 8/9
        p4 = 0

        four_vector = [p1, p2, p3, p4]
        self.set_four_vector(four_vector)
