#!/usr/bin/env python3

import argparse
import wave
import sys
import byteadpcm
import struct

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('input', help='input WAV file', type=argparse.FileType('rb'))
parser.add_argument('output', help='output ADPCM file, or - for stdout')
args = parser.parse_args()

try:
	wavfile = wave.open(args.input, 'rb')
except Exception as e:
	print('Unable to open wave file: %s' % str(e), file=sys.stderr)
	sys.exit(1)

if wavfile.getcomptype() != 'NONE':
	print('Unsupported compression: %s' % wavfile.getcompname(), file=sys.stderr)
	sys.exit(1)

if args.output == '-':
	outfile = sys.stdout.buffer
else:
	try:
		outfile = open(args.output, 'wb')
	except Exception as e:
		print('Cannot open output file: %s' % str(e), file=sys.stderr)
		sys.exit(1)

if wavfile.getsampwidth() == 1:
	format = '<' + 'B' * wavfile.getnchannels()
	def read_u8_sample():
		frame = wavfile.readframes(1)
		if not frame:
			return None
		frame = struct.unpack(format, frame)
		frame = int(round(sum(frame) / len(frame)))
		return frame
elif wavfile.getsampwidth() == 2:
	format = '<' + 'h' * wavfile.getnchannels()
	def read_u8_sample():
		frame = wavfile.readframes(1)
		if not frame:
			return None
		frame = struct.unpack(format, frame)
		frame = int(round(sum(frame) / len(frame)) + 32768)
		return frame >> 8
else:
	print('Unsupported sample width: %d bits' % (wavfile.getsampwidth() * 8), file=sys.stderr)
	sys.exit(1)

first_value = read_u8_sample()
second_value = read_u8_sample()

encoder = byteadpcm.ByteAdpcmEncoder(first_value)
low_nibble = encoder.encode(second_value)

outfile.write(struct.pack('BB', first_value, encoder.start_index))

while True:
	value = read_u8_sample()
	if value is None:
		break

	cur_nibble = encoder.encode(value)
	if low_nibble is None:
		low_nibble = cur_nibble
	else:
		outfile.write(struct.pack('B', (cur_nibble << 4) | low_nibble))
		low_nibble = None

if low_nibble is not None:
	outfile.write(struct.pack('B', low_nibble))

wavfile.close()
outfile.close()
