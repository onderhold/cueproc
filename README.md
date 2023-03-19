                    Cuesheet Processor (CueProc)                  
                   Copyright (c) 2006-2007 by Nyaochi, 2023 by onderhold
                                                                      


###### a) Preamble

---

onderhold: After modifying this utility in 2010 and 2012, I will now 
again update it to make it run with current versions of Python and Windows.
(original README.MD in README.Nyaochi.md)


# 1. Introduction

---
Cuesheet Processor (CueProc) is a command-line tool for converting
audio CD images into another format such as WAV, MP3, Ogg Vorbis, MP4,
MPC, WMA, etc. The functions of this tool can be summarized as follows:

- Parse a cuesheet (a .cue or audio file with the cuesheet embedded).
  Field values in a cuesheet (e.g., TITLE, PERFORMER, REM DATE, etc)
  will be used by the latter job.
- Read audio data in a CD image (supported format: FLAC, Monkey's Audio,
  WavPack, WAVE).
- Extract tracks in a CD image to individual WAVE files.
- Execute an external encoder with predefined command-line arguments
  for each track. CueProc sets appropriate command-line arguments
  (e.g., naming for output files, tagging, etc) automatically by
  specifying a codec.
- Execute an external encoder with configurable command-line arguments.
- Send audio stream of each track to STDIN of the external encoder.
- Enumerate cuesheets recursively under a directory.
- Process multiple cuesheets at a time, which is useful for converting
  an audio collection into a lossy format.
- Skip encoding when the corresponding output file exists, which is
  useful for converting new CD images only.

CueProc is distributed under GNU General Public Lisence (GPL).



# 2. Usage

---

Please refer to the wayback web site capture (copied to doc in this repo)
as for the tutorial



# 3. Acknowledgement

---

This software uses the following libraries:
- libsndfile
    available at: https://libsndfile.github.io/libsndfile/

- Monkey's Audio
    available at: https://www.monkeysaudio.com/

- Free Lossless Audio Codec (FLAC)
	available at: https://xiph.org/flac/

- WavPack
	available at: https://www.wavpack.com/
