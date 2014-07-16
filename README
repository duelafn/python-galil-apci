

Packages Required
-----------------

* jinja2
* jinja2_apci
* Galil Tools (see below)



Galil Tools
-----------

The galil-provided .deb files (http://www.galilmc.com/) work fine. However,
Debian's new multi-arch infrastructure does away with lib64/, so if you are
using the 64-bit version, you will need to move or symlink the libraries
into lib/:

    pushd /usr/lib/
    sudo ln -s ../lib64/libgalil.so* ../lib64/libGalil.so* ./

This is handled for you in a `postint` script if you install from a .deb
generated from the included debian control files.


LICENSE
=======

This software is Copyright (c) 2013 APCI, LLC.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
