# -*- coding: utf-8 -*-

def add(new, previous=None):
    if previous is None:
        return new
    return previous + new


def collect(new, previous=None):
    if previous is None:
        return [new]
    return previous + [new]


def merge(new, previous=None):
    return add(new, previous)
