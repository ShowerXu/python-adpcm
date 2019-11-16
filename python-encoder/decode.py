#!/usr/bin/env python3

import argparse
import wave
import sys
import byteadpcm
import struct

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--sr', default=44100, type=int, help='sample rate')
parser.add_argument('input', help='input ADPCM file, or - for stdin')
parser.add_argument('output', help='output mono 8-bit WAV file', type=argparse.FileType('wb'))
args = parser.parse_args()

if args.input == '-':
	infile = sys.stdin.buffer
else:
	try:
		infile = open(args.input, 'rb')
	except Exception as e:
		print('Cannot open input file: %s' % str(e), file=sys.stderr)
		sys.exit(1)

wavfile = wave.open(args.output, 'wb')

wavfile.setnchannels(1)
wavfile.setsampwidth(1)
wavfile.setframerate(args.sr)

try:
	start_value, start_index = struct.unpack('BB', infile.read(2))
except Exception as e:
	print('Unable to read header: %s' % str(e), file=sys.stderr)
	sys.exit(1)

decoder = byteadpcm.ByteAdpcmDecoder(start_value, start_index)
wavfile.writeframesraw(struct.pack('B', start_value))

while True:
	frame = infile.read(1)
	if not frame:
		break

	frame, = struct.unpack('B', frame)
	low = decoder.decode(frame & 0xF)
	high = decoder.decode(frame >> 4)
	wavfile.writeframesraw(struct.pack('BB', low, high))

wavfile.close()
