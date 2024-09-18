def PMT(C, n, t):
    """
    Compute the monthly payment for a given loan
    C: Capital
    n: Number of periods
    t: Yearly Interest rate
    """ 
    return (C * t/12)/(1-(1 + t/12)**-n)


def compute_remaining_capital_after_y_years(C, M, t, y):
    """
    Compute the capital remaining after y years of a loan
    C: Capital
    M: Monthly payment
    t: Yearly Interest rate
    y: Number of years
    """
    return (C-M/(t/12))*(1+t/12)**(y*12) + M/(t/12)