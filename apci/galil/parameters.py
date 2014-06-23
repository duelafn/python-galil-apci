# -*- coding: utf-8 -*-
"""

"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC. All rights reserved.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = '''
Parameter
CmdParameter OutputBitParameter
BasicParameter BasicQueryParameter EqParameter
AxisParameter AxisMaskParameter
IndexedParameter VectorParameter NetworkParameter
'''.split()

import struct


class Parameter(object):
    def __init__(self, galil, name, value=None, axes=None):
        self.galil = galil
        self.name  = name
        self.value = value

    def __str__(self):
        if self.value is not None:
            return self.set_cmd(self.value)
        else:
            raise Exception("Value not defined for parameter {} of type {}".format(self.name, type(self)))

    def check(self, value=None):
        value = self.value if value is None else value
        curr_value = self.get(refresh=False)

        # String equality is great!
        if str(value) == str(curr_value):
            return True

        # Else, try to interpret as numbers
        try:
            return apci.galil.Galil.round(value) == apci.galil.Galil.round(curr_value)
        except ValueError:
            return False

    def get(self, refresh=True):
        value = self.galil.command(self.get_cmd())
        if refresh:
            self.value = value
        return value

    def set(self, value, refresh=True):
        if refresh:
            self.value = str(value)
        self.galil.command(self.set_cmd(value))


class CmdParameter(Parameter):
    def __init__(self, galil, name, cmd=None, **kwargs):
        super(CmdParameter,self).__init__(galil, name, **kwargs)
        self.cmd   = name if cmd is None else cmd
        self.value = 1

    def get_cmd(self):
        return "MG1"

    def set_cmd(self, value):
        return self.cmd


class BasicParameter(Parameter):
    def __init__(self, galil, name, cmd=None, **kwargs):
        super(BasicParameter,self).__init__(galil, name, **kwargs)
        self.cmd   = name if cmd is None else cmd

    def get_cmd(self):
        return "MG_" + self.cmd

    def set_cmd(self, value):
        return "{} {}".format(self.cmd, value)


class BasicQueryParameter(BasicParameter):
    def get_cmd(self):
        return "{} ?".format(self.cmd)


class EqParameter(BasicParameter):
    def set_cmd(self, value):
        return "{}={}".format(self.cmd, value)


class AxisParameter(EqParameter):
    def __init__(self, galil, name, axis, **kwargs):
        super(AxisParameter,self).__init__(galil, name, cmd=(name + axis), **kwargs)


class AxisMaskParameter(BasicParameter):
    def __init__(self, galil, name, axes, **kwargs):
        super(AxisMaskParameter,self).__init__(galil, name, **kwargs)

    def get(self, refresh=True):
        axes = [ a for a in self.axes if self.galil.commandValue(self.get_cmd(a)) ]
        axes = self.join(axes)
        if refresh:
            self.value = axes
        return axes

    def get_cmd(self, axis):
        return "MG_" + self.cmd + axis

    def join(self, items):
        return "".join(items) if items else "N"


class VectorParameter(AxisMaskParameter):
    def __init__(self, galil, name, length, **kwargs):
        kwargs['axes'] = range(length)
        super(VectorParameter,self).__init__(galil, name, **kwargs)

    def join(self, items):
        return ",".join(items)


class NetworkParameter(BasicParameter):
    @staticmethod
    def int_to_csip(val):
        ",".join([ str(x) for x in reversed(struct.unpack_from("BBBB", struct.pack("i", val))) ])

    def get(self, refresh=True):
        value = self.int_to_csip(self.galil.commandValue(self.get_cmd()))
        if refresh:
            self.value = value
        return value

    def get_cmd(self, axis):
        return "MG_" + self.name + "0"


class IndexedParameter(Parameter):
    def __init__(self, galil, name, index, **kwargs):
        super(IndexedParameter,self).__init__(galil, name, **kwargs)
        self.index = index

    def get_cmd(self):
        return "MG_" + self.name + str(self.index)

    def set_cmd(self, value):
        return "{} {},{}".format(self.name, self.index, value)


class OutputBitParameter(Parameter):
    def __init__(self, galil, name, index, **kwargs):
        kwargs.setdefault("value", (1 if name == 'SB' else 0))
        super(OutputBitParameter,self).__init__(galil, name, **kwargs)
        self.index = index

    def get_cmd(self):
        return "@OUT[{}]".format(self.index)

    def set_cmd(self, value):
        return ("SB{}" if int(float(value)) else "CB{}").format(self.index)
