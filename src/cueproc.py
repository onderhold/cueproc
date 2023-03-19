#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    CueProc main.

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

This program requires Python 2.6 or later.
"""

from __future__ import print_function

import codecs
import exceptions
import fnmatch
import locale
import logging
import os
import sys
import string
import shutil

import cuesheet
from celib import *
import ce_getaudio
import ce_wave
import ce_oggenc
import ce_lame
import ce_lame_eyed3
import ce_fiismp3
import ce_hmp3
import ce_mpc
import ce_wma
import ce_ctmp4
import ce_nero
#import ce_nero_mpeg4ip
#import ce_nero_ap
import ce_flac
import ce_wavpack
import ce_extpipe

# Add audio input objects.
input_class_factory = [
    ce_getaudio.GetAudioInput(),
]

# Add audio output objects.
output_class_factory = [
    ce_wave.WaveOutput(),
    ce_flac.FlacOutput(),
    ce_wavpack.WavPackOutput(),
    ce_oggenc.OggEncOutput(),
    ce_lame.LameOutput(),
    ce_lame_eyed3.LameEyeD3Output(),
    ce_fiismp3.FiisMP3Output(),
    ce_hmp3.HelixMP3Output(),
    ce_mpc.MusePackOutput(),
    ce_wma.WmaOutput(),
    ce_ctmp4.CTMP4Output(),
    ce_nero.NeroMP4Output(),
#   ce_nero_mpeg4ip.NeroMP4Output(),
#   ce_nero_ap.NeroMP4Output(),
    ce_extpipe.GenericEncoderPipingOutput(),
]

def set_track_attributes(track, target, options, is_embedded):
    """Initialize track attributes (variables).

    This function updates the dictionary of the track.
    """

    # Set filename to the target file if the cuesheet is embedded.
    if is_embedded:
        track.filename = target
    else:
        if not os.path.isabs(track.filename):
            track.filename = os.path.join(os.path.dirname(target), track.filename)

    track.url = os.path.abspath(track.filename)
    # fo.write('track.url=%s, %s\n' % (type(track.url), track.url))
    track[unicode('audio','utf-8')] = track.filename
    track[unicode('audio_path','utf-8')] = os.path.dirname(track.filename)
    track[unicode('audio_path_drive','utf-8')] = os.path.splitdrive(track['audio_path'])[0]
    track[unicode('audio_path_dir','utf-8')] = os.path.splitdrive(track['audio_path'])[1]
    track[unicode('audio_base','utf-8')] = os.path.basename(track.filename)
    track[unicode('audio_file','utf-8')] = os.path.splitext(track['audio_base'])[0]
    track[unicode('audio_ext','utf-8')] = os.path.splitext(track['audio_base'])[1]
    track[unicode('audio_absolute','utf-8')] = track.url
    track[unicode('audio_absolute_path','utf-8')] = os.path.dirname(track['audio_absolute'])
    track[unicode('audio_absolute_path_drive','utf-8')] = os.path.splitdrive(os.path.dirname(track['audio_absolute_path']))[0]
    track[unicode('audio_absolute_path_dir','utf-8')] = os.path.splitdrive(os.path.dirname(track['audio_absolute_path']))[1]
    track[unicode('cuesheet','utf-8')] = target
    track[unicode('cuesheet_path','utf-8')] = os.path.dirname(target)
    track[unicode('cuesheet_path_drive','utf-8')] = os.path.splitdrive(track['cuesheet_path'])[0]
    track[unicode('cuesheet_path_dir','utf-8')] = os.path.splitdrive(track['cuesheet_path'])[1]
    track[unicode('cuesheet_base','utf-8')] = os.path.basename(target)
    track[unicode('cuesheet_file','utf-8')] = os.path.splitext(track['cuesheet_base'])[0]
    track[unicode('cuesheet_ext','utf-8')] = os.path.splitext(track['cuesheet_base'])[1]
    track[unicode('cuesheet_absolute','utf-8')] = os.path.abspath(target)
    track[unicode('cuesheet_absolute_path','utf-8')] = os.path.dirname(track['cuesheet_absolute'])
    track[unicode('cuesheet_absolute_path_drive','utf-8')] = os.path.splitdrive(os.path.dirname(track['cuesheet_absolute_path']))[0]
    track[unicode('cuesheet_absolute_path_dir','utf-8')] = os.path.splitdrive(os.path.dirname(track['cuesheet_absolute_path']))[1]
    track[unicode('audio_range_begin','utf-8')] = track.begin
    track[unicode('audio_range_end','utf-8')] = track.end
    track[unicode('cuesheet_embedded','utf-8')] = is_embedded

    track[unicode('output_plugin','utf-8')] = options.codec
    track[unicode('output_command','utf-8')] = options.encodercmd

    track[unicode('quot','utf-8')] = unicode('"','utf-8')

def set_compilation_flag(tracks):
    # Collect artist names in the tracks
    artists = set()
    for track in tracks:
        artists.add(track['ARTIST'])

    # Determine the compilation flag.
    compilation = (len(artists) != 1)
    
    for track in tracks:
        if not track.has_key('COMPILATION'):
            track[unicode('COMPILATION', 'utf-8')] = compilation

def set_albumart(track, options):
    if not track.get('ALBUMART'):
        images = options.albumart_files.split(',')
        images.append('%s.jpg' % track['cuesheet_file'])
        images.append('%s.jpeg' % track['cuesheet_file'])
        images.append('%s.png' % track['cuesheet_file'])
        images.append('%s.gif' % track['cuesheet_file'])
        for image in images:
            name = evaluate_expression(image, track, globals(), locals())
            fn = os.path.join(track['cuesheet_path'], name)
            if os.path.exists(fn):
                track[unicode('ALBUMART', 'utf-8')] = fn
                break

def copy_albumart(track, options):
    src = track.get('ALBUMART')
    if src is not None:
        filepart = os.path.basename(src)
        dst = os.path.join(track['output_path'], filepart)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            shutil.copy2(src, dst)

def open_text(target, charset):
    """Open a file that contains file names of cuesheets.

    Applies the correct decoding when the file contains a BOM, otherwise it uses
    the charset parameter for decoding.
    """
    boms = (
        (codecs.BOM_UTF8, 'utf8'),
        (codecs.BOM_UTF16, 'utf16'),
        (codecs.BOM_UTF32, 'utf32'),
        )
    # fo.write('%s\n' % repr(target.encode(options.syscharset)))    
    # f = open(target.encode(options.syscharset), mode='rb')
    # f = open(target.encode(fs_encoding), mode='rb')
    f = open(target, mode='rb')
    test = f.read(4)
    for bom, cs in boms:
        if test.startswith(bom):
            fi = codecs.open(target.encode(options.syscharset), mode='r', encoding=cs)
            fi.read(len(bom))
            return fi
    # fi = codecs.open(target.encode(options.syscharset), mode='r', encoding=charset)
    fi = codecs.open(target, mode='r', encoding=charset)
    return fi

def open_target(target, options):
    """Open a target cuesheet.

    This function parse the target cuesheet and returns a list of tracks.
    If the target file is an audio file with an embedded cuesheet, the
    function uses an input audio object to obtain the CUESHEET tag value.
    """

    is_embedded = False
    # Check the extension of the target cuesheet
    if target.lower().endswith('.cue'):
        # An external cuesheet
        fi = open_text(target, options.cscharset)
        tracks = cuesheet.reader(fi, options.hidden_track1)
    else:
        # Possibly an embedded cuesheet
        inobj = find_input_object(input_class_factory, target, options)
        if not inobj:
            return
        lines = inobj.get_tag(target, "CUESHEET", options)
        if not lines:
            return
        tracks = cuesheet.reader(
            lines,
            options.hidden_track1
            )
        is_embedded = True

    # Initialize track attributes.
    for track in tracks:
        # fo.write('target %s %s\n' % (type(target), target))
        set_track_attributes(track, target, options, is_embedded)

    return tracks

def warn(msg):
    fe.write(u'WARNING: %s\n' % msg)

def error(msg):
    fe.write(u'ERROR: %s\n' % msg)

def list_codec(fo, options):
    """List the names of all supported codecs.
    """

    fo.write('Supported codecs:\n')
    for outobj in output_class_factory:
        fo.write(u'  %s\n' % outobj.name)

def show_help_codec(fo, name):
    """Show information about the output codec.
    """

    # Find an output object with the specified name.
    outobj = find_object_by_name(output_class_factory, name)
    if not outobj:
        warn(u"No suitable output codec found for '%s'" % name)

    if outobj.doc.tools:
        fo.write(u'Tool:\n')
        for tool in outobj.doc.tools:
            fo.write(u'  %s\n' % tool)
    if outobj.doc.commands:
        fo.write(u'Dependencies:\n')
        for command in outobj.doc.commands:
            fo.write('  %s\n' % command)
    if outobj.doc.limitations:
        fo.write(u'Limitations:\n')
        for limitation in outobj.doc.limitations:
            fo.write('  %s\n' % limitation)
    if outobj.doc.tags:
        fo.write(u'Supported fields:\n')
        l = list(outobj.doc.tags)
        l.sort(lambda x, y: cmp(x, y))
        for tag in l:
            fo.write('  %s\n' % tag)

    fo.write(u'Default extension: %s\n' % outobj.ext)

def show_help_all_codecs(fo, options):
    """Show information about all output codec.
    """

    for outobj in output_class_factory:
        fo.write('[%s]\n' % outobj.name)
        show_help_codec(fo, outobj.name)
        fo.write('\n')

def show_variables(track):
    """Show values of all variables in the track.
    """
    fo.write(u'Variables:\n')
    l = track.items()
    l.sort(lambda x, y: cmp(x[0], y[0]))
    # fo.write(u'l=%s %s\n' % (type(l), repr(l)))
    
    for name, value in l:
        line = unicode('  %s=%s', 'utf-8') % (name, value)
        fo.write(line)
        fo.write('\n')

    if 1 == 2:        
        fo.write(u'name=%s %s\n' % (type(name), repr(name)))
        fo.write(u'value=%s %s\n' % (type(value), repr(value)))
        # line = u'  %s=%s\n' % (name, value) 
        # fo.write(line)
        return
        if isinstance(name, str):
            line = unicode('  %s=' % name, 'utf-8')
        else:
            line = u'  %s=' % name
        if isinstance(value, str):
            line += u'%s' % unicode(value)
        else:
            line += u'%s' % value
        fo.write(repr(line))
        fo.write('\n')

def find_callback((fo, encoding, pattern), dirname, names):
    # dirname = dirname.decode(encoding)
    for name in names:
        # name = name.decode(encoding)
        if fnmatch.fnmatch(name, pattern):
            # print(type(os.path.join(dirname, name)), repr(os.path.join(dirname, name)))
            # print(u'\n')
            print(os.path.join(dirname, name))
            # sys.stdout.write(u''.join(os.path.join(dirname, name)).encode(sys.stdout.encoding))
            # fo.write(u''.join(os.path.join(dirname, name)))
            # fo.write(u'\n')
    
def find(fo, options):
    directory = u''.join(os.path.dirname(options.find))
    pattern = u''.join(os.path.basename(options.find))  
    os.path.walk(directory, find_callback, (fo, options.syscharset, pattern))

def get_track_range(strrange):
    track_list = []
    values = strrange.split(',')
    for value in values:
        track_list.append(int(value))
    track_list.sort()
    return track_list

def process(options, target):
    # Find an output object with the specified name.
    outobj = find_object_by_name(output_class_factory, options.codec)
    if not outobj:
        warn('No suitable output class found')
        return

    # Change the encoder command if specified.
    if options.encodercmd:
        outobj.cmd = options.encodercmd
    if options.encoderext:
        outobj.ext = options.encoderext

    # Bind console object
    console = Console()
    console.syscharset = lp_encoding
    if options.rehearsal:
        console.executable = False
    if options.hide_cmdln:
        console.writable = False
    outobj.console = console

    # Open the target.
    tracks = open_target(target, options)
    if not tracks:
        warn('Failed to open a target, %s' % target)
        return

    # Determine compilation flag.
    if options.auto_compilation:
        set_compilation_flag(tracks)

    #
    valid_tracks = None
    if options.track:
        valid_tracks = get_track_range(options.track)

    # Loop for tracks
    for track in tracks:
        # Check if we're going to process this track.
        if valid_tracks is not None:
            if track['tracknumber'] not in valid_tracks:
                continue

        # Determine albumart variable.
        if options.auto_albumart:
            set_albumart(track, options)

        # Set optional variables specified by options.setvars.
        for setvar in options.setvars:
            pos = setvar.find('=')
            if pos >= 0:
                name = setvar[:pos]
                value = setvar[pos+1:]
                track[name] = evaluate_expression(
                    value, track, globals(), locals())
                # print("track[", name, "]", track[name])
            else:
                warn('Skipping an optional variable, %s' % strvar)

        # Report the progress.
        # print(type(target), repr(target))
        # fo.write('CueProc: %s \n' % target)
        fo.write(unicode('CueProc: %s [%02d/%02d]\n', 'utf-8') % (
            target, track['tracknumber'], int(track['TOTALTRACKS'])))

        # Determine an input module suitable for this track.
        inobj = find_input_object(input_class_factory, track.url, options)
        if not inobj:
            warn(u'No suitable input class found for track #%d, %s' % (
                track['tracknumber'],
                track.url)
                )
            continue

        # Obtain the command-line for extracting the source audio.
        incmdln = inobj.get_cmdln_track(track, outobj.is_utf8)

        # Generate an output directory name
        odir = evaluate_expression(options.outputdir, track, globals(), locals())
        odir = pstr(odir).strip()

        # Generate an output filename.
        ofn = evaluate_expression(options.outputfn, track, globals(), locals())
        ofn = fstr(ofn).strip()

        # Set more variables of the current track
        track[unicode('input_cmdline', 'utf-8')] = incmdln
        track[unicode('output', 'utf-8')] = os.path.join(odir, ofn + outobj.ext)
        track[unicode('output_ext', 'utf-8')] = outobj.ext
        track[unicode('output_path', 'utf-8')] = odir
        track[unicode('output_base', 'utf-8')] = ofn

        # Evaluate output_cmdln variable.
        if options.outputcmdln:
            track[unicode('output_cmdline', 'utf-8')] = evaluate_expression(
                options.outputcmdln[0], track, globals(), locals())
            for i in range(1, len(options.outputcmdln)):
                track[unicode('output_cmdline' + str(i), 'utf-8')] = evaluate_expression(
                    options.outputcmdln[i], track, globals(), locals())

        # Evaluate output_option variable.
        track[unicode('output_option', 'utf-8')] = unicode('', 'utf-8') 
        if options.encoderopt:
            opts = []
            for encoderopt in options.encoderopt:
                opts.append(evaluate_expression(encoderopt, track, globals(), locals()))
            track[unicode('output_option', 'utf-8')] = ' '.join(opts)

        # Show variables if specified.
        if options.show_variables:
            show_variables(track)

        # Check the existence of the output file.
        # fo.write('\n')
        # fo.write('%s %s' % (unicode('Track:', 'utf-8'), track['output'])) 
        # fo.write('\n')
        # fo.write('\n')
        if not options.overwrite and os.path.exists(track['output']):
            warn('Skipping existing file, %s' % track['output'])
            continue

        # Create the output directory if it does not exist
        if not os.path.exists(os.path.dirname(track['output'])):
            os.makedirs(os.path.dirname(track['output']))

        # Copy albumart images if specified.
        if options.albumart_action in ('copy', 'both'):
            copy_albumart(track, options)

        # Remove albumart variable for 'copy' action so that
        # the output object cannot refer to this variable.
        if options.albumart_action == 'copy':
            if track.has_key('ALBUMART'):
                del track['ALBUMART']

        outobj.handle_track(track, options)

        fo.write('\n')

    return True

if __name__ == '__main__':
    # For py2exe use only. sitecustomize.py and site.py are not available for py2exe, but we can call sys.setdefaultencoding directly.
    # Force to use UTF-8 encoding for internal string representations for the best compatibility (to avoid so-called 'dame-moji' problem in Shift_JIS encoding)
    if hasattr(sys, 'setdefaultencoding'):
       sys.setdefaultencoding('utf-8')

    # get sys.argv as unicode     
    uargv = win32_argv('utf-8')
    if uargv:
        fs_encoding = 'utf-8'
    else:
        uargv = sys.argv
        fs_encoding = sys.getfilesystemencoding()
    sys.argv = [x.decode(fs_encoding) for x in uargv]

    (options, args) = parse_cmdline()
    # Wrap IO streams.
    set_writer(options.syscharset)
    
    # Run the jobs.
    if options.list_codec:
        list_codec(fo, options)
    elif options.help_codec:
        show_help_codec(fo, options.help_codec)
    elif options.help_all_codecs:
        show_help_all_codecs(fo, options)
    elif options.find:
        find(fo, options)
    else:
        # Determine targets.
        targets = []
        for arg in args:
            # targets must be a list of unicode strings 
            targets.append(arg)
        if options.targets:
            # options.syscharset ensures that targets will be a list of 
            # unicode strings
            f = open_text(options.targets, options.syscharset)
            targets += map(string.strip, f.readlines())

        if not targets:
            warn("No target specified. Use -h or --help to see the usage.")
            sys.exit(1)

        # Execute job(s)
        for target in targets:
            # target is a unicode string
            # fo.write('target %s %s\n' % (type(target), repr(target)))
            process(options, target)
