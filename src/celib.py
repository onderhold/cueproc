# -*- coding: utf-8 -*-

"""
    CueProc standard library.

    Copyright (c) 2006-2008 by Nyaochi, 2010 by onderhold

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA, or visit
http://www.gnu.org/copyleft/gpl.html .
"""

from __future__ import print_function

# Program version and author
global VERSION
global AUTHOR
VERSION = '1.11 mod onderhold'
AUTHOR = 'Nyaochi & onderhold'

import sys
import codecs
import exceptions
import optparse
import os
import locale
import subprocess
import string

def get_file_encoding(f):
     if hasattr(f, "encoding"):
         return f.encoding
     else:
         return None

def set_writer(charset):
    # Wrap IO streams.
    global fo
    global fe    
    if not charset is None:
        sys.stdout = codecs.lookup(charset)[-1](sys.stdout)
        sys.stderr = codecs.lookup(charset)[-1](sys.stderr)
    fo = sys.stdout
    fe = sys.stderr

orig_stdout = sys.stdout
orig_stderr = sys.stderr

set_writer(sys.stdout.encoding)
options = unicode('')
args = []

default_encoding = sys.getdefaultencoding()
stdin_encoding = get_file_encoding(sys.stdin)
stdout_encoding = get_file_encoding(sys.stdout) or sys.getfilesystemencoding()
stderr_encoding = get_file_encoding(sys.stderr)
lp_encoding = locale.getpreferredencoding(False)
fs_encoding = sys.getfilesystemencoding()

if 1 == 2:
    # Debug encoding 
    fo.write(unicode('sys.getdefaultencoding()=%s\n', 'utf-8') % default_encoding)
    fo.write(unicode('sys.stdin.encoding=%s\n', 'utf-8') % stdin_encoding)
    fo.write(unicode('sys.stdout.encoding=%s\n', 'utf-8') % stdout_encoding)
    fo.write(unicode('sys.stderr.encoding=%s\n', 'utf-8') % stderr_encoding)
    # lc_encoding = locale.setlocale(locale.LC_ALL, unicode('.'+options.syscharset))
    fo.write(unicode('locale.getpreferredencoding()=%s\n', 'utf-8') % lp_encoding)
    fo.write(unicode('sys.getfilesystemencoding()=%s\n', 'utf-8') % fs_encoding)
    fo.write(unicode('repr() sys.argv=%s %s\n', 'utf-8') % (type(sys.argv[:]), repr(sys.argv[:])))
    # fo.write(unicode('repr() options.syscharset=%s %s\n' % (type(options.syscharset), repr(options.syscharset)))



def win32_argv(pcodec=None):                                                                                               
    """Uses shell32.GetCommandLineArgvW to get sys.argv as a list of UTF-8                                           
    strings.                                                                                                         
                                                                                                                     
    Versions 2.5 and older of Python don't support Unicode in sys.argv on                                            
    Windows, with the underlying Windows API instead replacing multi-byte                                            
    characters with '?'.                                                                                             
                                                                                                                     
    Returns None on failure.                                                                                         
                                                                                                                     
    Example usage:                                                                                                   
                                                                                                                     
    >>> def main(argv=None):                                                                                         
    ...    if argv is None:                                                                                          
    ...        argv = win32_utf8_argv() or sys.argv                                                                  
    ...                                                                                                              
    """                                                                                                              
                                                                                                                     
    try:                                                                                                             
        from ctypes import POINTER, byref, cdll, c_int, windll                                                       
        from ctypes.wintypes import LPCWSTR, LPWSTR                                                                  
                                                                                                                     
        GetCommandLineW = cdll.kernel32.GetCommandLineW                                                              
        GetCommandLineW.argtypes = []                                                                                
        GetCommandLineW.restype = LPCWSTR                                                                            
                                                                                                                     
        CommandLineToArgvW = windll.shell32.CommandLineToArgvW                                                       
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]                                                      
        CommandLineToArgvW.restype = POINTER(LPWSTR)                                                                 
                                                                                                                     
        cmd = GetCommandLineW()                                                                                      
        argc = c_int(0)                                                                                              
        argv = CommandLineToArgvW(cmd, byref(argc))                                                                  
        if argc.value > 0:                                                                                           
            # Remove Python executable if present                                                                    
            if argc.value - len(sys.argv) == 1:                                                                      
                start = 1                                                                                            
            else:                                                                                                    
                start = 0                                                                                            
            if pcodec:
                r = [argv[i].encode(pcodec) for i in                                                                 
                    xrange(start, argc.value)]
                # sys.stdout.write(pcodec + ' encoding r: ' + repr(r))
            else:                                                                       
                r = [argv[i] for i in                                                                 
                    xrange(start, argc.value)]                                                                       
            return r                                                                       
    except Exception:                                                                                                
        pass
        
def parse_cmdline(cmdline=None):
    global options
    global args
    # Define a command-line option parser.
    parser = optparse.OptionParser(
        usage="%prog [options] <target> [<target2> ...]\n"
        "Execute a job for each track in the target CD image(s).",
        version='Cuesheet Processor (%%prog) Version %s, Copyright (c) 2006-2008 by %s\n' % (VERSION, AUTHOR)
        )
    parser.add_option(
        "-c", "--output",
        action="store", type="string", dest="codec",
        metavar="PLUGIN",
        help="Specify an output plugin for the target(s)."
        )
    parser.add_option(
        "-x", "--outputcmd",
        action="store", type="string", dest="encodercmd",
        default=unicode('',"utf-8"),
        metavar="COMMAND",
        help="Specify a command name for PLUGIN. "
        "An output plugin uses its default command name without this option specified.",
        )
    parser.add_option(
        "-p", "--outputopt",
        action="append", type="string", dest="encoderopt",
        default=None,
        metavar="PATTERN",
        help="Specify a template pattern to pass optional arguments to PLUGIN. "
        "Variable expressions ${<variable-name>} will be replaced with the actual values for the track(s). "
        "Conditional expressions such as #if{<condition>}, #elif{<condition>}, #else, #endif will be evaluated, where a condition <condition> is expressed by a Python code snippet.",
        )
    parser.add_option(
        "-e", "--outputext",
        action="store", type="string", dest="encoderext",
        default=unicode('', "utf-8"),
        metavar="EXT",
        help="Specify an extension for output files. "
        "An output plugin uses its default extension without this option specified.",
        )
    parser.add_option(
        "-o", "--outputfn",
        action="store", type="string", dest="outputfn",
        default=unicode('${TRACKNUMBER}_${TITLE}', "utf-8"),
        metavar="PATTERN",
        help="Specify a template pattern for output filenames. "
        "Although the specification of template pattern is the same as -p (--outputopt) option, any characters invalid for a filename will be replaced with spaces."
        )
    parser.add_option(
        "-d", "--outputdir",
        action="store", type="string", dest="outputdir",
        default=unicode(".", "utf-8"),
        metavar="PATTERN",
        help="Specify a template pattern for output directory names. "
        "Although the specification of template pattern is the same as -p (--outputopt) option, any characters invalid for a directory name will be replaced with spaces."
        )
    parser.add_option(
        "-m", "--outputcmdln",
        action="append", type="string", dest="outputcmdln",
        default=[],
        metavar="PATTERN",
        help="Specify a template pattern for 'extpipe' plugin. "
        "The specification of template pattern is the same as -p (--outputopt) option. "
        "The plugin can invoke multiple processes sequencially with this option specified multiple times."
        )
    parser.add_option(
        "-s", "--setvar",
        action="append", type="string", dest="setvars", metavar="NAME=VALUE",
        default=[],
        help="Define a user-defined track variable whose name is NAME and value is VALUE. "
        "This option can also overwrite the value of an existing variable. "
        "NAME must consist of alphanumeric and '_' letters. "
        "VALUE will be evaluated as a pattern similarly to the -p (--outputopt) option."
        )
    parser.add_option(
        "--no-auto-compilation",
        action="store_false", dest="auto_compilation",
        default=True,
        help="By default, CueProc sets COMPILATION flag to true for all tracks in the target cuesheet with multiple distinct PERFORMER names. "
        "This option disables the automatic process of activating compilation flag."
        )
    parser.add_option(
        "--albumart-files",
        action="store", dest="albumart_files",
        default=unicode("cover.jpg,albumart.jpg,folder.jpg", "utf-8"),
        help="Specify the list of files for albumart images in comma-separated values. "
        "CueProc sets ALBUMART variable if one of these file exists in the same directory as the cuesheet. "
        " The default value of the list is, 'cover.jpg,albumart.jpg,folder.jpg'."
        )
    parser.add_option(
        "--no-auto-albumart",
        action="store_false", dest="auto_albumart",
        default=True,
        help="This option disables the automatic detection of albumart image based on the esistence of image files."
        )
    parser.add_option(
        "--albumart-action",
        action="store", dest="albumart_action",
        choices=("embed", "copy", "both"),
        default=unicode("copy", "utf-8"),
        help="This option specifies the action when albumart images are detected, embed to output files (embed), copy to output directories (copy), or both (both)."
        )
    parser.add_option(
        "-t", "--track",
        action="store", type="string", dest="track",
        default=None,
        help="Specify track range where the job is applicable in comma separated values (CSV)."
        )
    parser.add_option(
        "--hidden-track1",
        action="store_true", dest="hidden_track1",
        default=False,
        help="This option assumes the first track to begin at INDEX 00 (or PREGAP)."
        )
    parser.add_option(
        "--target",
        action="store", type="string", dest="targets",
        default=None,
        help="Specify a text file describing the list of target filenames. Useful for converting a number of CD images at a time with a list file generated by --find option."
        )
    parser.add_option(
        "-W", "--syscharset",
        action="store", type="string", dest="syscharset",
        default="mbcs",
        help="Specify a charset for the current operating system. The default value for this option is '%default'."
        )
    parser.add_option(
        "-w", "--cscharset",
        action="store", type="string", dest="cscharset",
        default="mbcs",
        help="Specify a charset for the target cuesheet(s). The default value for this option is '%default'."
        )
    parser.add_option(
        "-f", "--overwrite",
        action="store_true", dest="overwrite",
        help="Force to overwrite existing output files. "
        "The default behavior (not overwriting) is useful "
        "to process tracks only in new CD images."
        )
    parser.add_option(
        "--tempdir",
        action="store", type="string", dest="tempdir",
        default=None,
        help="Specify a directory for temporary files to which some plugins create during the jobs."
        )
    parser.add_option(
        "-n", "--rehearsal",
        action="store_true", dest="rehearsal",
        help="Do not execute the jobs but only shows command-lines to be invoked by this program. Useful for debugging a job without running it."
        )
    parser.add_option(
        "--find",
        action="store", type="string", dest="find", metavar="PATTERN",
        default=None,
        help="Find files under the current directory (including its sub directories) that match the specified pattern."
        )
    parser.add_option(
        "--show-variables",
        action="store_true", dest="show_variables",
        help="Show values of the track variable for each track in the target(s). "
        "This option provides useful information for debugging a job."
        )
    parser.add_option(
        "-l", "--list-plugin",
        action="store_true", dest="list_codec",
        help="List names of installed plugins."
        )
    parser.add_option(
        "--help-plugin",
        action="store", dest="help_codec", metavar="PLUGIN",
        help="Show documentation for the specified plugin."
        )
    parser.add_option(
        "--help-all-plugins",
        action="store_true", dest="help_all_codecs",
        help="Show documentation for all installed plugins."
        )
    parser.add_option(
        "--hide-cmdln",
        action="store_true", dest="hide_cmdln",
        help="Do not display command-lines invoked by this program."
        )

    # Parse command-line arguments.
    parser.print_version(file=sys.stderr)
    return parser.parse_args(cmdline)

class InvalidParameter(exceptions.ValueError):
    pass

def qstr(value):
    """ Convert the value to a unicode string quoted if necessary.
    """
    if not isinstance(value, unicode):
        value = unicode(value)
    escapes = (' ', "'", '&', '<', '>', '|')
    for escape in escapes:
        if value.find(escape) >= 0:
            return unicode('"', 'utf-8') + value + unicode('"', 'utf-8')
    return value

def fstr(value):
    """ Convert the value to a unicode string suitable for a filename.
    """
    if not isinstance(value, unicode):
        value = unicode(value)
    value = value.replace(u'\\', u'-')
    value = value.replace(u'/', u'-')
    value = value.replace(u':', u';')
    value = value.replace(u'*', u'#')
    value = value.replace(u'?', u'$')
    value = value.replace(u'"', u' ')
    value = value.replace(u'<', u'[')
    value = value.replace(u'>', u']')
    value = value.replace(u'|', u'!')
    return value

def pstr(value):
    """ Convert the value to a unicode string suitable for a pathname.
    """
    if not isinstance(value, unicode):
        value = unicode(value)
    # replace colon character if it is not part of a drive specification
    # fo.write('value[2:4]=%s %s\n' % (type(value[2:4]), repr(value[2:4])))
    if ''.join(value[0:1]) in u'\"\'' and ''.join(value[1:2]).upper() in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and value[2:4] == u':\\':
        value = value[:3] + value[3:].replace(u':', u';')
    elif ''.join(value[0:1]).upper() in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and value[1:3] == u':\\':
        value = value[:2] + value[2:].replace(u':', u';')
    else:
        value = value.replace(u':', u';')
    # fo.write('value=%s %s\n' % (type(value), repr(value)))
    value = value.replace(u'*', u'#')
    value = value.replace(u'?', u'$')
    value = value.replace(u'"', u' ')
    value = value.replace(u'<', u'[')
    value = value.replace(u'>', u']')
    value = value.replace(u'|', u'!')
    return value

class optstr:
    def __init__(self, name = None, value = None):
        self.name = name
        self.value = value
    def __unicode__(self):
        if self.name is not None and self.value is not None:
            return unicode(qstr(self.name)) + unicode(' ', 'utf-8') + unicode(qstr(self.value))
        else:
            return unicode('', 'utf-8')

class optstr3:
    def __init__(self, name = None, name2 = None, value = None):
        self.name = name
        self.name2 = name2
        self.value = value
    def __unicode__(self):
        if self.name is not None and self.name2 is not None and self.value is not None:
            return unicode(qstr(self.name), 'utf-8') + unicode(' ', 'utf-8') + unicode(qstr(self.name2 + self.value), 'utf-8')
        else:
            return unicode('', 'utf-8')

def args_to_string(args):
    l = []
    for arg in args:
        if arg is not None and arg:
            l.append(unicode(arg))
    return unicode(' ').join(l)

class Console:
    def __init__(self):
        self.writable = True
        self.executable = True
        self.syscharset = sys.stdout.encoding

    def write(self, line):
        if self.writable:
            # fo.write(line)
            fo.write(repr(line))
            fo.write('\n')

    def execute(self, line):
        if self.writable:
            # fo.write(line)
            fe.write(repr(line))
            fe.write('\n')
            fe.write('\n')
        if self.executable:
            # try:
            retcode = os.system(line.encode(self.syscharset))
                # retcode = subprocess.call(line.decode('utf-8'))
                # fe.write('Child returned %s\n' % retcode)
                # if retcode < 0:
                    # print >>sys.stderr, "Child was terminated by signal", -retcode
                # else:
                    # print >>sys.stderr, "Child returned", retcode
            # except OSError, e:
                # print >>sys.stderr, "Execution failed:", e
            # return
            return retcode
        else:
            return -1

class InputModule:
    def __init__(self):
        pass
    def get_cmdln_track(self, track, is_utf8, extopt = ''):
        pass
    def test(self, filename):
        pass

class OutputModuleDocument:
    def __init__(self):
        self.tools = None
        self.commands = None
        self.limitations = None
        self.tags = None

class OutputModule:
    def __init__(self):
        self.name = None
        self.ext = None
        self.console = None
        self.is_utf8 = False
        self.doc = OutputModuleDocument()
    def handle_track(self, track, incmdln):
        pass

def find_input_object(cf, filename, options):
    for obj in cf:
        if obj.test(filename, options):
            return obj
    return None

def find_object_by_name(cf, name):
    for obj in cf:
        if obj.name == name:
            return obj
    return None

def evaluate_expression(strexp, track, globals, locals):
    # Evaluate conditions in strexp.
    tmpl = ''           # Resultant template string.
    conditions = []     # Condition stack.
    i = 0
    while i < len(strexp):
        if strexp.startswith('##', i):
            tmpl += '#'
            i += 2
        elif strexp.startswith('#if{', i):
            begin = i + 4
            end = strexp.find('}', begin)
            if begin <= end:
                b = eval(strexp[begin:end], globals, locals)
                conditions.append(b)
                i = end + 1
            else:
                raise exceptions.ValueError("'}' is missing (pos = %d)\n%s" % (i, strexp))
        elif strexp.startswith('#elif{', i):
            conditions.pop()
            begin = i + 6
            end = strexp.find('}', begin)
            if begin <= end:
                b = eval(strexp[begin:end], globals, locals)
                conditions.append(b)
                i = end + 1
            else:
                raise exceptions.ValueError("'}' is missing (pos = %d)\n%s" % (i, strexp))
        elif strexp.startswith('#else', i):
            if not conditions:
                raise exceptions.ValueError("Corresponding #if is missing (pos = %d)\n%s" % (i, strexp))
            i += 5
            b = conditions.pop()
            conditions.append(not b)
        elif strexp.startswith('#endif', i):
            if not conditions:
                raise exceptions.ValueError("Corresponding #if is missing (pos = %d)\n%s" % (i, strexp))
            i += 6
            b = conditions.pop()
        elif not conditions or conditions[-1]:
            tmpl += strexp[i]
            i += 1
        else:
            i += 1
    # fo.write('tmpl=%s %s\n' % (type(tmpl), repr(tmpl)))
    str_subst = string.Template(tmpl).substitute(track)
    # fo.write('str_subst=%s %s\n' % (type(str_subst), repr(str_subst)))    
    return str_subst
