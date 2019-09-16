
def diff_dicts( dct_a, dct_name_a, dct_b, dct_name_b ):
    """ For logging/developement convenience, diffs dicts.
        Called by -- """
    set_a = set( dct_a.items() )
    set_b = set( dct_b.items() )
    in_a_not_b = dict( set_a - set_b )
    in_b_not_a = dict( set_b - set_a )
    log.debug( f'in `{dct_name_a}` but not `{dct_name_b}`, ```{in_a_not_b}```' )
    log.debug( f'in `{dct_name_b}` but not `{dct_name_a}`, ```{in_b_not_a}```' )
    return
