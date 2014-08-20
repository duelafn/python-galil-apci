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

SHELL   = /bin/bash

GENERATED_FILES += _*
GENERATED_FILES += Galil.py

# Python
#-------
PKGNAME = galil-apci
PKG_VERSION = $(shell perl -ne 'print $$1 if /^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"/' galil_apci/__init__.py)
PY_SWIG += _Galil.cpp


.PHONY: all sdist dist debbuild clean build test


all: test build

zip: test ${PY_SWIG}
	python setup.py sdist --format=zip

sdist: test ${PY_SWIG}
	python setup.py sdist

dist: test debbuild ${PY_SWIG}
	mv -f debbuild/${PKGNAME}_* debbuild/*.deb dist/
	rm -rf debbuild

debbuild: test sdist
	rm -rf debbuild
	mkdir -p debbuild
	grep "(${PKG_VERSION}-1)" debian/changelog || (echo "** debian/changelog requires update **" && false)
	mv -f dist/${PKGNAME}-${PKG_VERSION}.tar.gz debbuild/${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cd debbuild && tar -xzf ${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cp -r debian debbuild/${PKGNAME}-${PKG_VERSION}/
	cd debbuild/${PKGNAME}-${PKG_VERSION} && dpkg-buildpackage -rfakeroot -uc -us -tc -i

build: ${PY_SWIG}
	python setup.py build_ext --inplace

_%.cpp: swig/%.i
	swig -c++ -python -o $@ $<

test: build
	unit2 discover -s test

clean:
	pyclean .
	rm -f ${GENERATED_FILES}
	rm -rf build dist
	rm -f MANIFEST swig/Galil.py swig/Galil_wrap.cpp
