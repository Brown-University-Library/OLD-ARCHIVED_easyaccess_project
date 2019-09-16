import logging, pprint


log = logging.getLogger('access')


def run_diff( d1, d2, NO_KEY='<KEYNOTFOUND>' ):
    """ Actual differ.
        Credit: <http://code.activestate.com/recipes/576644-diff-two-dictionaries/#c9>
        Called by diff_dicts() """
    both = d1.keys() & d2.keys()
    diff = {k:(d1[k], d2[k]) for k in both if d1[k] != d2[k]}
    diff.update({k:(d1[k], NO_KEY) for k in d1.keys() - both})
    diff.update({k:(NO_KEY, d2[k]) for k in d2.keys() - both})
    return diff


def diff_dicts( dct_a, dct_name_a, dct_b, dct_name_b ) :
    """ For logging/developement convenience, diffs dicts.

        Called by -- """
    diff = run_diff( dct_a, dct_b )
    # reverse_diff = run_diff( dct_b, dct_a )
    log.debug( "dct differences, read as {'key': ('%s-value', %s-value)}, ```%s```" % (dct_name_a, dct_name_b, pprint.pformat(diff)) )
    # log.debug( f'in `{dct_name_b}` but not `{dct_name_a}`, ```{reverse_diff}```' )
    return

