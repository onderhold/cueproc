# -*- coding: utf-8 -*-

"""
    Input Plugin for Generic audio (getaudio)

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
import datetime
import string, unicodedata
from celib import *
import subprocess

class GetAudioInput(InputModule):
    def __init__(self):
#        self.name = 'getaudio'
#        self.cmd = 'getaudio'
#        self.name = unicode('sox', 'utf-8')
#        self.cmd = unicode('sox', 'utf-8')
        self.name = unicode('ffmpeg', 'utf-8')
        self.cmd = unicode('ffmpeg', 'utf-8')

    def get_cmdln_track(self, track, is_utf8 = False, extopt = ''):
        args = []
        args.append(qstr(self.cmd))
#        args.append(unicode('-V1', 'utf-8')) # sox
        args.append(unicode('-v quiet -f wav -c:a pcm_s16le -i','utf-8'))  # ffmpeg
        args.append(qstr(track.url))
#        args.append(unicode('-t wav - trim', 'utf-8'))  # sox
#        if is_utf8:
#            args.append(unicode('--utf8', 'utf-8'))
        if track.begin:
            s_begin = track.begin[:5] + '.' + '%d' % round(float(track.begin[7:]) * 1000 / 75, 0)
            d_begin = datetime.datetime.strptime(s_begin, '%M:%S.%f')
            begin = unicode('-ss ', 'utf-8') + '00:' + s_begin  # ffmpeg
            duration = ''
#            duration = track.begin[:5] + '.' + track.begin[7:]  # sox
#            args.append(optstr(unicode('--begin', 'utf-8'), track.begin))  # getaudio
        if track.end:
            s_end = track.end[:5] + '.' + '%d' % round(float(track.end[7:]) * 1000 / 75, 0)
            d_end = datetime.datetime.strptime(s_end, '%M:%S.%f')
            d_duration = d_end - d_begin
#            print('ce_audio' , type(d_duration), repr(d_duration))
#            print('ce_audio' , d_duration)
            d_min, d_sec = divmod(d_duration.seconds, 60)
            s_duration = '%02d:%02d.%03d' % (d_min, d_sec, d_duration.microseconds/1000)
            duration = unicode('-t ', 'utf-8') + '00:' + s_duration
#            duration = duration + unicode('=', 'utf-8') + track.end[:5] + '.' + track.end[7:]  # sox
        args.append(begin) # ffmpeg
        args.append(duration)  # ffmpeg
        args.append(unicode('-c:a copy -f wav -', 'utf-8'))  # ffmpeg
#        args.append(duration)  # sox
        args.append(extopt)
        retval = args_to_string(args)
        # print(type(retval), repr(retval))
        return retval

    def test(self, filename, options, is_utf8 = False):
        args = []
        args.append(qstr(self.cmd))
#        if is_utf8:
#           args.append(unicode('--utf8', 'utf-8'))
#        args.append(unicode('--info', 'utf-8'))  # sox
#        args.append(unicode('-V1', 'utf-8'))  # sox
#        args.append(qstr(filename))  # sox
        args.append(unicode('-v error -analyzeduration 700M -i', 'utf-8'))  # ffmpeg
        args.append(qstr(filename))  # ffmpeg
        args.append(unicode('-f null NUL', 'utf-8'))  # ffmpeg
        cmdln = args_to_string(args)
        # print('ce_audio' , type(cmdln), repr(cmdln))
        # fo.write(unicode('cmdln=%s\n', 'utf-8') % cmdln)
        cmd_enc = cmdln.encode(fs_encoding)
        # print('ce_audio' , type(cmd_enc), repr(cmd_enc))
        try:
            proc = subprocess.Popen(cmd_enc, 
                        shell=True, 
                        stdout=subprocess.PIPE,
                        )
        except Exception:
            print('getaudio Error', type(cmd_enc), repr(cmd_enc))
            retval = False                                                                                                
        else:
            line = proc.communicate()[0]
            print('ce_audio' , type(line), repr(line))
#            retval = not line.startswith('sox FAIL')  # sox
            retval = not line.startswith('filename')  # ffmpeg
        return retval 

    def get_tag(self, filename, tagname, options):
        args = []
        args.append(qstr(self.cmd))
        args.append(unicode('--utf8', 'utf-8'))
        args.append(optstr(unicode('--tag', 'utf-8'), tagname))
        args.append(qstr(filename))
        cmdln = args_to_string(args)
        cmd_enc = cmdln.encode(fs_encoding)
        try:
            proc = subprocess.Popen(cmd_enc, 
                        shell=True, 
                        stdout=subprocess.PIPE,
                        )
            # f = os.popen(cmdln.encode(options.syscharset), 'r')
        except Exception:
            print('getaudio Error', type(cmd_enc), repr(cmd_enc))
            retval = False                                                                                                
        else:
            line = proc.communicate()[0]
            # print('ce_audio' , type(line), repr(line))
            if line.startswith('GETTAG OK'):
                retval = map(lambda x: x.decode('utf8'), f.readlines())  
                return retval 
