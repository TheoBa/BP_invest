def PMT(C, n, t):
    """
    Compute the monthly payment for a given loan
    C: Capital
    n: Number of periods
    t: Interest rate
    """ 
    return (C * t/12)/(1-(1 + t/12)**-n)
