# -*- coding: utf-8 -*-
"""

"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = '''
Parameter
CmdParameter OutputBitParameter
BasicParameter BasicQueryParameter EqParameter
SSIParameter
AxisParameter AxisQueryParameter AxisMaskParameter
IndexedParameter VectorParameter NetworkParameter
'''.split()

import struct

from .galil import Galil

class Parameter(object):
    def __init__(self, galil, name, value=None, axes=None, filename=None, lineno=None):
        self.galil = galil
        self.name  = name
        self.value = value
        self.axes  = axes
        self.filename = filename
        self.lineno   = lineno

    def __str__(self):
        if self.value is not None:
            return self.set_cmd(self.value)
        else:
            raise Exception("Value not defined for parameter {} of type {}".format(self.name, type(self)))

    def check(self, value=None):
        value = self.value if value is None else value
        curr_value = self.get(refresh=False)
        return self.cmp(curr_value, value)

    def cmp(self, curr_value, value):
        # String equality is great!
        if str(value) == str(curr_value):
            return True

        # Else, try to interpret as numbers
        try:
            return Galil.round(value) == Galil.round(curr_value)
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


class AxisQueryParameter(AxisParameter):
    def get_cmd(self):
        return "{}=?".format(self.cmd)


class SSIParameter(AxisQueryParameter):
    def get(self, refresh=True):
        try:
            value = self.galil.command(self.get_cmd())
            value = [ x.strip() for x in value.split(',') ]
            value = "{},{},{},{}<{}>{}".format(*value)
        except ExternalGalil.CommandError:
            value = 0
        if refresh:
            self.value = value
        return value


class AxisMaskParameter(BasicParameter):
    def __init__(self, galil, name, axes, **kwargs):
        super(AxisMaskParameter,self).__init__(galil, name, axes=axes, **kwargs)

    def get(self, refresh=True):
        axes = [ a for a in self.axes if self.galil.commandValue(self.get_cmd(a)) ]
        axes = self.join(axes)
        if refresh:
            self.value = axes
        return axes

    def get_cmd(self, axis):
        return "MG_" + self.cmd + str(axis)

    def join(self, items):
        return "".join(str(x) for x in items) if items else "N"


class VectorParameter(AxisMaskParameter):
    def __init__(self, galil, name, length, **kwargs):
        kwargs['axes'] = range(length)
        super(VectorParameter,self).__init__(galil, name, **kwargs)

    def get(self, refresh=True):
        axes = [ self.galil.commandValue(self.get_cmd(a)) for a in self.axes ]
        axes = self.join(axes)
        if refresh:
            self.value = axes
        return axes

    def cmp(self, curr_value, value):
        curr_value = curr_value.split(',')
        value = value.split(',')

        if len(curr_value) != len(value):
            return False

        for i in xrange(len(value)):
            if not super(VectorParameter,self).cmp(curr_value[i], value[i]):
                return False

        return True

    def join(self, items):
        return ",".join(str(x) for x in items)


class NetworkParameter(BasicParameter):
    @staticmethod
    def int_to_csip(val):
        return ",".join([ str(x) for x in reversed(struct.unpack_from(b"BBBB", struct.pack(b"i", val))) ])

    def get(self, refresh=True):
        value = self.int_to_csip(self.galil.commandValue(self.get_cmd()))
        if refresh:
            self.value = value
        return value

    def get_cmd(self):
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
        return "MG@OUT[{}]".format(self.index)

    def set_cmd(self, value):
        return ("SB{}" if int(float(value)) else "CB{}").format(self.index)
