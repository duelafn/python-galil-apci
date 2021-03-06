# -*- coding: utf-8 -*-
"""Core galil package"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2013 APCI, LLC.
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
from __future__ import division, absolute_import, print_function
__version__ = "1.2.0"

from galil_apci.galil      import Galil       # noqa F401
from galil_apci.file       import GalilFile   # noqa F401

from galil_apci.parameters import *           # noqa F401, F403
from galil_apci.config     import *           # noqa F401, F403
