# -*- coding: utf-8 -*-
"""Simple galil file templating and minification

Preforms useful actions on galil encoder files.

  - Substitution of template variables (using jinja2)

  - Whitespace trimming and minification by command packing
"""
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

import re
import logging
logger = logging.getLogger(__name__)

import galil_apci
import jinja2

import collections

from jinja2_apci import RequireExtension, RaiseExtension

import math


axis2idx = { "A": 0, "B": 1, "C": 2, "D": 3,
             "E": 4, "F": 5, "G": 6, "H": 7,
             "X": 0, "Y": 1, "Z": 2, "W": 3
           }
def param_list(params):
    """
    Produces string appropriate for a galil parameter list for a set of axes.

    Setting a number of values at once sometimes requires issuing a command
    with a single positional list of values for each axis. For example::

        JG val1,val2,...

    This can be difficult if the axis numbers are parameters. This function
    will produce a list from a dictionary of axes (numerical or letters)::

        JG{{ param_list({ "A": 60*4096, "B": 60*4096 }) }}
        JG{{ param_list({ "0": 60*4096, "1": 60*4096 }) }}
        JG{{ param_list({ primary.axis: "^a*" ~ primary.counts, secondary.axis:  "^a*" ~ secondary.counts }) }}
    """
    a = [""] * 8
    for (k, v) in params.iteritems():
        a[int(axis2idx.get(k, k))] = str(v)
    i = 7
    while i >= 0:
        if a[i] == '':
            i -= 1
        else:
            break
    if i < 0:
        raise Exception("No values in the parameter list: {}".format(str(params)))

    return ",".join(a[0:i+1])

def build_commander(fmt):
    """
    Convenience method which constructs list of formatted commands when
    passed a list of arguments.

    E.g.,::

       HX = build_commander("HX{}")
       print( HX(1,2,3) )            # prints HX1;HX2;HX3
    """
    def cmd(*args):
        return ";".join([ fmt.format(x) for x in args ])
    return cmd


def sin(theta):
    """sin function taking degree arguments"""
    return math.sin(math.pi * theta/180)

def asin(h):
    """asin function returning degrees"""
    return 180 * math.asin(h) / math.pi

def cos(theta):
    """cos function taking degree arguments"""
    return math.cos(math.pi * theta/180)

def acos(h):
    """acos function returning degrees"""
    return 180 * math.acos(h) / math.pi


class GalilFile(object):

    @classmethod
    def add_globals(cls, g):
        g["string_to_galil_hex"] = galil_apci.Galil.string_to_galil_hex
        g["galil_hex_to_string"] = galil_apci.Galil.galil_hex_to_string
        g["galil_hex_to_binary"] = galil_apci.Galil.galil_hex_to_binary
        g["round_galil"] = galil_apci.Galil.round

        g["axis2idx"]   = axis2idx
        g["param_list"] = param_list
        g["HX"] = build_commander("HX{}")
        g["SB"] = build_commander("SB{}")
        g["CB"] = build_commander("CB{}")

        g["max"] = max
        g["min"] = min
        g["int"] = int

        g["sin"]  = sin
        g["asin"] = asin
        g["cos"]  = cos
        g["acos"] = acos


    def __init__(self, path=None, package=None, line_length=79):
        """
        @param path: If a path (array of directories) is provided, it will
            be prepended to the template search path. The default path is
            the "gal" folder in the apci module directory.

        @param line_length: Galil maximum line length. 79 for most boards,
            but some are capped at 39.
        """
        self.line_length = line_length

        loaders = []
        if path:
            loaders.append(jinja2.FileSystemLoader(path, encoding='utf-8'))
        if package:
            loaders.append(jinja2.PackageLoader(package, 'gal', encoding='utf-8'))

        def finalize(value):
            if value is None:
                print("Use of undefined value in template!")
                return "None"
            else:
                return value

        self.env = jinja2.Environment(
            extensions=[RequireExtension, RaiseExtension],
            loader=jinja2.ChoiceLoader(loaders),
            undefined=jinja2.StrictUndefined,
            finalize=finalize,
        )

        GalilFile.add_globals(self.env.globals)


    def load(self, name, context):
        """Renders and minifies a template"""
        return self.minify( self.render(name, context) )

    def lint(self, content, warnings=False):
        """
        Performs a lint check on the galil code

            - long lines, too-long strings
            - duplicate labels / forgotten C{JS}, C{JS} or C{JP} to non-existant labels
            - C{_JS} or C{()} used in sub argument, inconsistent sub arity
            - Double equals ("=="), Not equals ("!=")
            - presence of "None" anywhere in the code

            - [warning] unused labels

        NOT IMPLEMENTED / TODO:

            - long variable names
            - external JP targets
            - C{SHA}, C{_GRB}, ... (axes outside of braces, should be C{SHE{lb}E{lb}AE{rb}E{rb}} and C{_GRE{lb}E{lb}BE{rb}E{rb}})
            - uninitialized variables (variables not initialized in any #xxINIT)

        """
        content = self.minify(content)
        errors = []

        # WARNING: Any trailing semicolon/EOL checks need to be zero-width assertions
        p_sub_def   = re.compile(r"(?:^|;)(#[a-zA-Z0-9_]{1,7})")
        p_sub_arg   = re.compile(r"""
                         (?:^|;)
                         (?:J[SP]|XQ) (\#[a-zA-Z0-9_]{1,7})      # jump name
                         ((?:\(.*?\))?)                          # optional arguments
                         (?= ; | $                               # endl
                           | , \(                                # complex condition
                           | , (?:\d+|\^[a-h]|\w{1,8}) (?:;|$)   # thread number
                         )
                      """, re.X)
        p_bad_ops   = re.compile(r"(?:==|!=)")
        p_JS        = re.compile(r"_JS")

        p_if_js     = re.compile(r"(?:^|;)IF\([^;\n]+\)[;\n](J[SP]#[a-zA-Z]+)[^;\n]*[;\n]ENDIF", re.M)

        # Dangerous to have any calculation in an argument. Only want variables.
        # warning: won't catch @ABS[foo]
        p_danger_arg = re.compile(r"(?:.(?:\(|\)).|[^a-zA-Z0-9.,@\[\]_\(\)\^\&\"\-]|(?<![\(,])\-)")
        pc_MG       = re.compile(r"^MG")
        subs        = set()
        sub_line    = {}
        sub_arity   = {}
        sub_neg1_dflt = set(("#ok", "#error"))
        AUTO_subs   = set(["#AUTO", "#MCTIME", "#AMPERR", "#AUTOERR", "#POSERR", "#CMDERR"])
        JSP_sub     = set()
        JSP_line    = collections.defaultdict(list)

        if warnings:
            for jump in p_if_js.findall(content):
                errors.append( "IF(...);{} better written as {},(...)".format(jump, jump) )

        lineno = 0
        for line in content.split("\n"):
            lineno += 1

            # presence of None
            if "None" in line:
                errors.append( "line {}, Contains 'None', check template vars: {}".format(lineno, line) )

            # long lines
            if len(line) > self.line_length:
                errors.append( "line {}, Line too long: {}".format(lineno, line) )

            # Bad operators
            if p_bad_ops.search(line):
                errors.append( "line {}, bad operator: {}".format(lineno, line) )

            # for duplicate labels
            for name in p_sub_def.findall(line):
                if name in subs:
                    errors.append( "line {}, Duplicate label: {}".format(lineno, name) )
                else:
                    subs.add(name)
                    sub_line[name] = lineno

            # examine subroutine arguments (JS, JP)
            # also for unused labels and jumps to non-existant labels
            for name, arg in p_sub_arg.findall(line):
                # Note: arg includes "()"
                JSP_sub.add(name)
                JSP_line[name].append(lineno)
                args = [] if len(arg) < 3 else arg.split(',')

                if name in sub_neg1_dflt and arg == "(-1)":
                    # Make exception for #ok and #error
                    pass
                elif name in sub_arity:
                    if len(args) != sub_arity[name]:
                        errors.append( "line {}, inconsistent sub arity for {}. Was {} now {}".format(lineno, name, sub_arity[name], len(args)) )
                else:
                    sub_arity[name] = len(args)

                if p_JS.search(arg):
                    errors.append( "line {}, _JS used in subroutine argument: {}".format(lineno, line) )
                if p_danger_arg.search(arg):
                    errors.append( "line {}, Dangerous value (calculation) used in argument: {}".format(lineno, line) )

            for cmd in line.split(";"):
                # long strings
                if not pc_MG.search(cmd):
                    strings = cmd.split('"')
                    for idx in (x for x in xrange(1, len(strings), 2) if len(strings[x]) > 5):
                        errors.append( "line {}, Long string '{}' in command: {}".format(lineno, strings[idx], cmd) )

        # jumps to non-existant labels
        for sub in JSP_sub - subs:
            errors.append( "line(s) {}, J[SP]{} found but label {} not defined".format(JSP_line[sub], sub, sub) )

        if warnings:
            # unused labels
            for sub in subs - JSP_sub - AUTO_subs:
                errors.append( "line {}, Label {} defined but never used".format(sub_line[sub], sub) )

        return errors

    def minify(self, content):
        """
        Performs minification on a galil file. Actions performed:

           - Strips all comments
           - trims space after semicolon and before/after various ops (" = ", "IF (...)")
           - Merges "simple" lines (up to line_length)
        """
        lines = []

        double_semi = re.compile(r';(\s*)(?=;)')
        line_end_semi = re.compile(r';$')

        # Comments: ', NO, REM. Do NOT need to check for word boundaries ("NOTE" is a comment)
        #
        # WARNING: This is INCORRECT! In galil a semicolon ends a comment
        # - this is crazy so I explicitly choose to have a comment kill
        # the rest of the line
        comment = re.compile(r"(?:^|;)\s*(?:'|NO|REM).*")

        # Operators with wrapped space. Match will be replaced with \1.
        operator_spaces = re.compile(r"\s*([,;=\+\-*/%<>\(\)\[\]&|]|<>|>=|<=)\s*")

        # A line containing just a label
        label_line = re.compile(r"^#[a-zA-Z0-9]{1,7}$")

        # A line that starts with a label
        label_start = re.compile(r"^#")

        # Joinable Lines (combinations of the following):
        #    - Simple Assignments: assignments to our variables or arrays (start with lower)
        #    - ENDIF, ELSE
        # NOTE: a joinable line never ends in a semicolon - this provides a way to force a line break
        joinable_line = re.compile(r"""
            ^(?: (?:^|;) \s*
                 (?:
                     (?:[~^][a-z]|[a-z][a-zA-Z0-9]{0,7}(?:\[[^\];]+\])?)
                         \s* = \s* [^\;]+
                   | ENDIF
                   | ELSE
                 )
            \s*)+$
        """, re.X)

        _lines1 = []
        # Start with simple compaction (removes extra garbage and makes
        # later length calculations more reliable
        for line in content.split("\n"):
            line = re.sub(comment, '', line)
            line = re.sub(operator_spaces, '\\1', line)
            line = line.strip()
            if len(line):
                _lines1.append(line)

        # The more advanced stuff: line merging, etc
        i = 0
        _lines2 = []
        while i < len(_lines1):
            line = _lines1[i]

            while ( i < len(_lines1) - 1
                    and joinable_line.match(_lines1[i+1])
                    and self.line_length > len(line + ";" + _lines1[i+1])
                    ):
                line = line + ";" + _lines1[i+1]
                i += 1

            if len(line):
                _lines2.append(line)
            i += 1

        # Squash label into next line (assuming it isn't itself a label)
        i = 0
        while i < len(_lines2):
            line = _lines2[i]

            if ( i < len(_lines2) - 1
                 and label_line.match(line)
                 and not label_start.match(_lines2[i+1])
                 and self.line_length > len(line + ";" + _lines2[i+1])
               ):
                line = line + ";" + _lines2[i+1]
                i += 1

                if ( i < len(_lines2) - 1
                     and _lines2[i+1] == 'EN'
                     and self.line_length > len(line + ";" + _lines2[i+1])
                     ):
                    line = line + ";" + _lines2[i+1]
                    i += 1

            # double semicolons confuse galil but are somewhat easy to
            # introduce when templating and doing strange minification.
            # Strip them out again just to be sure:
            line = line_end_semi.sub('',(double_semi.sub(r'\1',line)))

            if len(line):
                lines.append(line)
            i += 1

        for i, line in enumerate(lines):
            if (len(line) > self.line_length):
                logger.error("Long line '%s' in minified galil output", line)

        return "\n".join(lines)


    def trim(self, content):
        """
        Performs whitespace trimming on a galil file.
        """
        lines = []
        for line in content.split("\n"):
            line = line.strip()
            if len(line):
                lines.append(line)
        return "\n".join(lines)


    def render(self, name, context):
        """
        Renders a galil template file (substitutes variables and expands
        inclusions), but does not perform whitespace trimming or
        minification.
        """
        content = self.env.get_template(name).render(context)
        # double semicolons confuse galil but are somewhat easy to
        # introduce when templating. Strip them out here:
        return re.sub(r';(\s*)(?=;)', r'\1', content).encode('utf-8')

    def get_template(self, name):
        """
        Gets the jinja template object for a template file.
        """
        return self.env.get_template(name)
