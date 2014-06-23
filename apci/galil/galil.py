# -*- coding: utf-8 -*-
"""
APCI Galil Wrapper

Inherits from Galil.Galil which is a swig-generated library. This wrapper
includes various helpful tools and also some integration into the rest of
the APCI toolchain.
"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2010,2013 APCI, LLC. All rights reserved.
from __future__ import division, absolute_import, print_function


import os, re, hashlib, platform, time
import gzip as _gzip
from binascii import b2a_hex
from contextlib import closing

if 'Windows' == platform.system():
    class ExternalGalil(object):
        Galil = object
else:
    import Galil as ExternalGalil

from apci.util import flatten, short_stacktrace

import logging
logger = logging.getLogger('apci.galil')
GALIL_TRACE = int(os.environ.get('APCI_GALIL_TRACE', 0))


def _hex2str(match):
    return chr(int(match.group(0), 16))


class Galil(ExternalGalil.Galil):
    def __init__(self, address=""):
        super(Galil,self).__init__(str(address))
        self.max_line_length = 80
        self.nr_digital_inputs = 8
        self.nr_digital_outputs = 8
        self.nr_analog_inputs = 8
        self.nr_analog_outputs = 8
        self.nr_threads = 8


    def commandValue(self,command,retry=1):
        try:
            return super(Galil,self).commandValue(str(command))
        except ExternalGalil.TimeoutError:
            logger.warning("Galil timeout (retrying...)" if retry > 0 else "Galil timeout (no retry)")
            if retry > 0:
                return self.commandValue(self,command,retry-1)
        return None

    def command(self,command,retry=1):
        try:
            return super(Galil,self).command(str(command))
        except ExternalGalil.TimeoutError:
            if retry > 0:
                return self.command(command,retry-1)
        return None

    def __getitem__(self, key):
#         logger.debug("galil.__getitem__, getting '%s' for %s", key, short_stacktrace(1))
        if GALIL_TRACE: logger.debug("galil.__getitem__, getting '%s'", key)
        return self.commandValue("MG{}".format(key))

    def __setitem__(self, key, value):
        if GALIL_TRACE: logger.debug("galil.__setitem__, setting '%s' = '%s'", key, value)
        self.command("{}={}".format(key, value))

    @classmethod
    def string_to_galil_hex(self, string):
        """
        On a Galil board, even strings are stored in Galil4,2 format. This
        method will return a hex string as Galil would store the string.

        E.g.: '12345' -> '$31323334.3500'
        """
        if (len(string) > 6):
            raise ValueError("Galil strings may have at most 6 characters")
        hexstring = b2a_hex(string.ljust(6, "\0"))
        return ('$' + hexstring[0:8] + '.' + hexstring[8:12]).upper()

    @classmethod
    def galil_hex_to_string(self, ghex):
        """
        On a Galil board, even strings are stored in Galil4,2 format. This
        method will return a readable string from a Galil hex string.

        E.g.: '$31323334.3500' -> '12345'
        """
        return re.sub('[a-zA-Z0-9]{2}', _hex2str, ghex.translate(None, '$.')).rstrip("\0")

    @classmethod
    def galil_hex_to_binary(self, ghex):
        """
        Just like galil_hex_to_string but does not strip trailing null bytes.

        E.g.: '$31323334.3500' -> '12345\\x00'
        """
        return re.sub('[a-zA-Z0-9]{2}', _hex2str, ghex.translate(None, '$.'))

    @classmethod
    def computeProgramHash(self, program):
        """
        Computes a hash of the program. Returns a Galil string.
        """
        m = hashlib.md5()
        m.update(program)
        return self.string_to_galil_hex(m.hexdigest()[0:6])

    @classmethod
    def round(self, val):
        """
        Rounds a value to galiul precision. If the value then is an
        integral value, will return a python int so that its
        stringification is correct.
        """
        val = round(float(val), 4)
        return int(val) if val == int(val) else val

    def get(self, key, dflt=None, stash=None):
        """
        Get the result from a single galil command.

        @param key: The command to execute.
        @param dflt: Default to return upon receiving a CommandError
        @param stash: Stash to read / populate. If command is present in
            stash, no galil code will be executed. If galil code is
            executed, the return value will be stored in the stash. If the
            default is returned, the stash will not be altered.
        """
        if stash is not None and key in stash:
            return stash[key]

        try:
            val = self[key]
            if stash is not None:
                stash[key] = val
            return val
        except ExternalGalil.CommandError:
            return dflt

    def get_list(self, exprs, stash=None):
        cmd = "MG" + ",".join(exprs)
        if stash is not None and cmd in stash:
            return stash[cmd]

        res = self.command(cmd)
        if GALIL_TRACE: logger.debug("galil.get_list('%s') -> %s", cmd, res)
        if res is None:
            return None

        ret = [ float(x) for x in res.split() ]
        if stash is not None:
            stash[cmd] = ret
            for key, val in zip(exprs, ret):
                stash[key] = val
        return ret

    def get_string(self, name, dflt=None, stash=None):
        """
        Executes an expression (usually just a variable name) and
        interprets the result as a galil string.

        E.g.: galil.get_string("xPrgName") -> "Homing"
        (by issuing the command "MG {$8.4}, xPrgName" and decoding the result)

        @param name: The variable name to read.
        @param dflt: Default to return upon receiving a CommandError
        @param stash: Stash to read / populate. If command is present in
            stash, no galil code will be executed. If galil code is
            executed, the return value will be stored in the stash. If the
            default is returned, the stash will not be altered.
        """
        stash_key = u"«get_string» " + name
        if stash is not None and stash_key in stash:
            return stash[stash_key]

        try:
            coded = self.command("MG {{$8.4}}, {}".format(name))
            val = self.galil_hex_to_string(coded)
            if GALIL_TRACE: logger.debug("galil.get_string(%s) -> '%s'", name, val)
            if stash is not None:
                stash[stash_key] = val
            return val
        except ExternalGalil.CommandError:
            return dflt

    def get_string_list(self, exprs, stash=None):
        # XXX: TODO: handle problem of long commands (execute multiple commands then join arrays)
        cmd = 'MG{$8.4}' + '," "'.join(exprs)
        if stash is not None and cmd in stash:
            return stash[cmd]

        res = self.command(cmd)
        if GALIL_TRACE: logger.debug("galil.get_string_list('%s') -> %s", cmd, res)
        if res is None:
            return None

        ret = [ self.galil_hex_to_string(x) for x in res.split() ]
        if stash is not None:
            stash[cmd] = ret
            for key, val in zip(exprs, ret):
                stash[u"«get_string» " + key] = val
        return ret

    def IN(self, port, stash=None):
        """
        Reads a galil @IN[] value. Returns 0, 1, or None on error.
        """
        return self.get("@IN[{}]".format(int(port)), None, stash)

    def AN(self, port, stash=None):
        """
        Reads a galil @AN[] value. Returns a float, or None on error.
        """
        return self.get("@AN[{}]".format(int(port)), None, stash)

    def OUT(self, port, stash=None):
        """
        Reads a galil @OUT[] value. Returns 0, 1, or None on error.
        """
        return self.get("@OUT[{}]".format(int(port)), None, stash)

    def TB(self, port, value):
        """
        Sets or clear a galil output bit. Returns None on error.
        """
        cmd = "SB" if value else "CB"

        try:
            if GALIL_TRACE: logger.debug("galil.TB: %s%s", cmd, int(port))
            return self.command("{}{}".format(cmd, int(port)))
        except ExternalGalil.CommandError:
            return None

    def SB(self, *ports):
        """
        Sets bits on output ports. Return None on error (but may have partial setting!)
        """
        cmd = ";".join( "SB{}".format(port) for port in ports )

        try:
            if GALIL_TRACE: logger.debug("galil.SB: %s", cmd)
            return self.command(cmd)
        except ExternalGalil.CommandError:
            return None

    def CB(self, *ports):
        """
        Clears bits on output ports. Return None on error (but may have partial setting!)
        """
        cmd = ";".join( "CB{}".format(port) for port in ports )

        try:
            if GALIL_TRACE: logger.debug("galil.CB: %s", cmd)
            return self.command(cmd)
        except ExternalGalil.CommandError:
            return None

    def get_all_IN(self, stash=None):
        """Returns array of all input values. Populates stash with individual values"""
        return self.get_list([ "@IN[{}]".format(1+i) for i in range(self.nr_digital_inputs) ], stash)

    def get_all_OUT(self, stash=None):
        """Returns array of all output values. Populates stash with individual values"""
        return self.get_list([ "@OUT[{}]".format(1+i) for i in range(self.nr_digital_outputs) ], stash)

    def get_all_AN(self, stash=None):
        """Returns array of all analog input values. Populates stash with individual values"""
        return self.get_list([ "@AN[{}]".format(1+i) for i in range(self.nr_analog_inputs) ], stash)

    def get_running_threads(self, stash=None):
        """Returns a set of all currently running thread IDs (0..7)."""
        running = set()
        running_threads = self.get_list([ "_XQ{}".format(i) for i in range(self.nr_threads) ], stash)
        for thr in range(self.nr_threads):
            if running_threads[thr] >= 0:
                running.add(thr)
        return running

    def join(self, *commands):
        """
        Joins commands up to the maximum line length. Returns a (shorter)
        array of commands to run.
        """
        code = [""]
        for s in flatten(commands):
            if len(code[-1]) > 0 and len(code[-1]) + len(s) < self.max_line_length - 2:
                code[-1] += ";" + s
            elif len(code[-1]) == 0:
                code[-1] = s
            else:
                code.append(s)
        return code

    def _get_variables_code(self, **kwargs):
        """Internal helper function for .set() and .run()"""
        code = []
        for name, val in kwargs.iteritems():
            if isinstance(val, basestring):
                code.append('{}="{}"'.format(name, val))
            else:
                code.append('{}={}'.format(name, val))

        return code

    def set(self, **kwargs):
        """
        Set one or more variables at once.

        Example:

            self.galil.set( xPressP=3, xPressD=C_FLAG_NO_CHANGE_PRESSURE )

        @attention: Strings will be automatically wrapped in "", be sure
            that any numbers passed are properly int() or float().
        """
        code = self._get_variables_code(**kwargs)
        if GALIL_TRACE: logger.info("Setting variables: %s", " ".join(code))

        for line in self.join(code):
            self.command(line)

    def run(self, command, **kwargs):
        """
        Run an APCI "program" on the galil board.

        Sets the variables passed in kwargs then sets the special C{xRun}
        variable to the command name.

        Examples:

            self.galil.run( "press", xPressP=3, xPressD=C_FLAG_NO_CHANGE_PRESSURE )
            self.galil.run( "fhome" )

        @attention: Setting string values via kwargs will rewuire wrapping
        the value in quotes (e.g., C{xName='"Foo"'})
        """
        code = self._get_variables_code(**kwargs)
        if GALIL_TRACE: logger.info("Running galil program '%s' with arguments: %s", command, " ".join(code))

        # Be sure to set this last!
        code.append('xRun="{}"'.format(command))
        for line in self.join(code):
            self.command(line)

    def getBoardProgramHash(self):
        """
        Returns a Galil string hash of the current program on the board.

        If no hash is defined on the board, catches the exception and
        returns None.
        """
        try:
            return self.command("MG {$8.4}, xPrgHash")
        except ExternalGalil.CommandError:
            return None

    def getBoardProgramName(self):
        """
        Returns name of the program currently present on the board.

        If no known program is defined on the board, catches the exception
        and returns None.
        """
        try:
            return self.get_string("xPrgName")
        except ExternalGalil.CommandError:
            return None

    def add_xAPI(self, program, name, hash):
        """
        Returns a modified program with required xAPI support functions.

        Replaces any empty #xINIT and #xAPIOk functions (must be only thing
        on line) in the program with correct implementations which set the
        program name/hash and which implement the xAPI verification.

        This action WILL change the length of the lines defining these
        functions so the functions definitions should be the only thing on
        the line. (shouldn't be a problem since any otimizer will leave the
        #XXXX at the beginning of a line). This action, however, will not
        alter the function count or line count of the program.
        """
        return program.replace(
            "#xINIT;EN\n", '#xINIT;xPrgName="{}";xPrgHash={};xAPIOk=0;EN\n'.format(name, hash)
        ).replace(
            "#xAPIOk;EN\n", '#xAPIOk;xAPIOk=xAPIOk+1;EN\n'
        )

    def check_xAPI(self):
        """
        Check that loaded controller code properly supports xAPI
        (thus xPrgName and xPrgHash are reliable)
        """
        try:
            xAPIOk = self["xAPIOk"]

            if self["_XQ0"] < 0:
                self.command('XQ#xAPIOk')
                time.sleep(0.020)
            else:
                self.run("xAPI")
                time.sleep(0.100)

            return (self["xAPIOk"] == xAPIOk + 1)

        except ExternalGalil.CommandError:
            return False

    def boardProgramNeedsUpdate(self, name, check):
        """
        Returns True if program needs to be loaded onto controller.
        Returns False if the prorgam is already installed there.
        """
        if "\n" in check:
            program_str = str(check)
            new_hash = self.computeProgramHash(program_str)
        else:
            new_hash = check

        if not self.check_xAPI():
            logger.debug("xAPI check failed, controller reload required")
            return True

        if not self.get("xPrgOK"):
            logger.debug("Not xPrgOK, controller reload required")
            return True

        if self.getBoardProgramName() != name:
            logger.debug("Wrong program running ({} != {}), controller reload required".format(self.getBoardProgramName(), name))
            return True

        if self.getBoardProgramHash() != new_hash:
            logger.debug("Wrong program version running ({} != {}), controller reload required".format(self.getBoardProgramHash(), new_hash))
            return True

        return False

    def ensureBoardProgram(self, name, program, run_auto=True, force=False):
        """
        Examines the hash of the current program on the galil board. If it
        matches the hash of the parameter, nothing is done. Otherwise, the
        program will be loaded onto the board and its #AUTO routine will be
        executed (unless "run_auto=False" is passed to this method).

        Returns True if program was freshly downloaded to the board.
        Returns False if the prorgam was already there.
        """
        program_str = str(program)
        new_hash    = self.computeProgramHash(program_str)

        if force or self.boardProgramNeedsUpdate(name, new_hash):
            logger.info("Downloading program %s (%s)", name, new_hash)
            self.command('RS')
            self["xPrgOK"] = 0
            self.programDownload(self.add_xAPI(program_str, name, new_hash))
            if run_auto:
                logger.info("Starting program %s (%s)", name, new_hash)
                self.command('XQ#AUTO')
                time.sleep(0.5)
            else:
                # Ensure name/hash are correct even if we don't run #AUTO
                self['xPrgName'] = self.string_to_galil_hex(name)
                self['xPrgHash'] = new_hash
            self["xPrgOK"] = 1
            return True

        if run_auto and self["_XQ0"] < 0:
            logger.info("Restarting program %s (%s)", name, new_hash)
            try:
                self.command('XQ#AUTO')
                time.sleep(0.5)
            except:
                self["xPrgOK"] = 0
                return self.ensureBoardProgram(name, program, run_auto, force=True)

        return False

    def saveBoardProgram(self, fname, gzip=False):
        """
        Saves the current program to a compressed file.
        """

        fh = _gzip.open(fname, 'wb') if gzip else open(fname, 'wb')
        with closing(fh):
            fh.write(self.programUpload())
