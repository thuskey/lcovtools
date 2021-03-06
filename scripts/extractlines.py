"""
This script extracts the valid lines (lines that could be executed) from a set
of lua files.

USAGE:

	python ExtractLines.py --compile file1.lua file2.lua file3.lua

This tool will likely break with newer versions of Lua as it relies on parsing
the debug listing output generated by luac.exe (which is subject to change).
"""

"""
Example luac output format:

main <test.lua:0,0> (14 instructions, 56 bytes at 009417E8)
0+ params, 2 slots, 0 upvalues, 0 locals, 4 constants, 2 functions
		1       [5]     CLOSURE         0 0     ; 009419E0
		2       [2]     SETGLOBAL       0 -1    ; executed
		3       [9]     CLOSURE         0 1     ; 00941E10
		4       [7]     SETGLOBAL       0 -2    ; notexecuted
		5       [12]    GETGLOBAL       0 -1    ; executed
		6       [12]    CALL            0 1 1
		7       [12]    JMP             3       ; to 11
		8       [13]    JMP             2       ; to 11
		9       [14]    GETGLOBAL       0 -2    ; notexecuted
		10      [14]    CALL            0 1 1
		11      [17]    GETGLOBAL       0 -3    ; print
		12      [17]    LOADK           1 -4    ; "Done..."
		13      [17]    CALL            0 2 1
		14      [17]    RETURN          0 1

function <test.lua:2,5> (7 instructions, 28 bytes at 009419E0)
0 params, 2 slots, 0 upvalues, 0 locals, 3 constants, 0 functions
		1       [3]     GETGLOBAL       0 -1    ; print
		2       [3]     LOADK           1 -2    ; "This function is executed"
		3       [3]     CALL            0 2 1
		4       [4]     GETGLOBAL       0 -1    ; print
		5       [4]     LOADK           1 -3    ; "Isnt that great"
		6       [4]     CALL            0 2 1
		7       [5]     RETURN          0 1

function <test.lua:7,9> (4 instructions, 16 bytes at 00941E10)
0 params, 2 slots, 0 upvalues, 0 locals, 2 constants, 0 functions
		1       [8]     GETGLOBAL       0 -1    ; print
		2       [8]     LOADK           1 -2    ; "This function is not executed"
		3       [8]     CALL            0 2 1
		4       [9]     RETURN          0 1
"""

import re
import sys
import subprocess
import getopt
import glob

print "<validLines>"

for arg in sys.argv[1:]:
	items = None
	if arg.startswith("@"):
		# this is a response file
		items = open(arg[1:], "rt").read().splitlines()
	else:
		items = [arg]

	for item in items:
		for f in glob.glob(item):
			test = subprocess.Popen("luac -l %s" % f, stdout=subprocess.PIPE, shell=True).communicate()[0]

			state = "function_header"
			instructions = 0
			validLines = set()

			re_header = re.compile("\S+ \S+ \((\d+) instructions?, \d+ bytes at .*\)")
			re_decompile = re.compile("\s*\d+\s+\[(\d+)\].*")

			for x in [x for x in test.splitlines() if len(x) > 0]:
				if state == "function_header":
					instructions = int(re_header.match(x).groups(1)[0])
					state = "function_details"
				elif state == "function_details":
					state = "function_decompile" # this line is skipped
				elif state == "function_decompile":
					validLines.add(re_decompile.match(x).groups(1)[0])
					instructions -= 1
					if instructions == 0:
						state = "function_header"

			print " <file name=\"%s\">" % f

			# Write them out in order, nicer for debugging
			lines = [int(x) for x in validLines]
			lines.sort()
			
			for l in lines:
				print "  <l no=\"%s\"/>" % l,

			print " </file>"

print "</validLines>"
