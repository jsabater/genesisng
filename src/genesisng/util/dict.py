# -*- coding: utf-8 -*-
# from bunch import Bunch


def del_empty_strings(d):
    """
    Extend Bunch with a new method to remove all keys whose values are
    empty strings.
    """

    for k in d.keys():
        if d.get(k) == '':
            del(d[k])
