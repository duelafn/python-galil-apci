# -*- coding: utf-8 -*-
"""

"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC. All rights reserved.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'GalilConfig'.split()


import re
import apci.galil

from functools import partial
from .parameters import *

CONFIG_PARSERS = [
    (re.compile(r'^\s*#'), None),
    (re.compile(r'^\s*$'), None),
    (re.compile(r"^\s*(?:REM|NO|EN|')"), None),
    (re.compile(r'^\s*(?P<name>SI)(?P<axis>[A-Z])=(?P<value>.*)$'), SSIParameter),
    (re.compile(r'^\s*(?P<name>[A-Z]{2})(?P<axis>[A-Z])=(?P<value>.*)$'), AxisQueryParameter),
    (re.compile(r'^\s*(?P<name>[A-Z]{2})=(?P<value>.*)$'), EqParameter),
    (re.compile(r'^\s*(?P<name>[A-Z]{2})$'), CmdParameter),
    (re.compile(r'^\s*(?P<name>(?:SH)(?:[A-Z]))$'), CmdParameter),
    (re.compile(r'^\s*(?P<name>LZ|CO|LB|LU)\s+(?P<value>.*)$'), BasicParameter),
    (re.compile(r'^\s*(?P<name>RC|DH|VF|PF|IK|TM|MW|EI)\s+(?P<value>.*)$'), BasicQueryParameter),
    (re.compile(r'^\s*(?P<name>[CS]B)\s*(?P<index>\d+)$'), OutputBitParameter),
    (re.compile(r'^\s*(?P<name>CW)\s+(?P<value>[\d.]+)$'), BasicParameter),
    (re.compile(r'^\s*(?P<name>AQ)\s*(?P<index>\d+),(?P<value>.*)$'), IndexedParameter),
    (re.compile(r'^\s*(?P<name>BA)\s+(?P<value>.*)$'), AxisMaskParameter),
    (re.compile(r'^\s*(?P<name>SM|IA)\s+(?P<value>.*)$'), NetworkParameter),
    (re.compile(r'^\s*(?P<name>CN)\s+(?P<value>.*)$'), partial(VectorParameter, length=5)),
]

class Foo(object):
    def __init__(self, bar, baz):
        self.bar = bar
        self.baz = baz

class GalilConfig(object):
    _parser_classes_ = dict()
    @classmethod
    def lookup_class(self, cls):
        if cls in self._parser_classes_:
            return self._parser_classes_[cls]
        self._parser_classes_[cls] = globals().get(cls, cls)
        return self._parser_classes_[cls]

    def __init__(self, galil, axes='ABCDEFGH'):
        self.galil   = galil
        self.axes    = axes

    def refresh(self):
        for item in self.lines:
            if isinstance(item, Parameter):
                item.get(refresh=True)

    def check(self):
        changes = []
        for item in self.lines:
            if isinstance(item, Parameter):
                if not item.check():
                    changes.append("{} command on {} line {} changed from {} to {}".format(
                            item.cmd,
                            item.filename or 'Unknown', item.lineno or 'Unknown',
                            item.value, item.get(refresh=False)
                    ))
        return changes

    def load(self, filename):
        with open(filename, 'r') as fh:
            lines = []
            for lineno, line in enumerate(fh, start=1):
                line = line.rstrip()
                for pat, cls in CONFIG_PARSERS:
                    match = pat.match(line)
                    if match:
                        cls = GalilConfig.lookup_class(cls)
                        if cls is None:
                            lines.append(line.rstrip())
                            break
                        elif callable(cls):
                            kwargs = match.groupdict()
                            kwargs.setdefault("axes", self.axes)
                            kwargs.setdefault("filename", filename)
                            kwargs.setdefault("lineno", lineno)
                            lines.append(cls(galil=self.galil, **kwargs))
                            break
                        else:
                            raise Exception("Unexpected class {} matched in {} line {}: '{}'".format(cls, filename, lineno, line))
                else:
                    raise Exception("Unparsable setting in {} line {}: '{}'".format(filename, lineno, line))
        self.lines = lines


    def save(self, filename):
        with open(filename, 'w') as fh:
            for line in self.lines:
                fh.write(str(line) + "\n")
