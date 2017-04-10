# -*- coding: utf-8 -*-

def add(next_, previous=None):
    if previous is None:
        return next_
    return previous + next_


def collect(next_, previous=None):
    if previous is None:
        return [next_]
    return previous + [next_]


def merge(next_, previous=None):
    return add(next_, previous)
