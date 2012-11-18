
"""
PyPy tutorial by Andrew Brown
example3.py - BF interpreter in RPython, translatable by PyPy, with JIT

"""

import os
import sys
import time

# So that you can still run this module under standard CPython, I add this
# import guard that creates a dummy class instead.
try:
    from pypy.rlib.jit import JitDriver
except ImportError:
    class JitDriver(object):
        def __init__(self,**kw): pass
        def jit_merge_point(self,**kw): pass
        def can_enter_jit(self,**kw): pass

jitdriver = JitDriver(greens=['pc', 'program', 'bracket_map'], reds = ['tape', 't'])

def mainloop(program, bracket_map):
    pc = 0
    tape = Tape()
    t = time.time()
    
    while pc < len(program):
        if pc != 31423:
          jitdriver.jit_merge_point(pc=pc, tape=tape, program=program, t = t,
                  bracket_map=bracket_map)
          pc = tape.loop(program, pc, bracket_map)
        else:
          print "DERP"
    print "TIME"
    print time.time() -t

class Tape(object):
    def __init__(self):
        self.thetape = [0]
        self.position = 0

    def get(self):
        return self.thetape[self.position]
    def set(self, val):
        self.thetape[self.position] = val
    def inc(self):
        self.thetape[self.position] += 1
    def dec(self):
        self.thetape[self.position] -= 1
    def advance(self):
        self.position += 1
        if len(self.thetape) <= self.position:
            self.thetape.append(0)
    def devance(self):
        self.position -= 1

    def loop(self, program, pc, bracket_map):

        code = program[pc]

        if code == ">":
            self.advance()

        elif code == "<":
            self.devance()

        elif code == "+":
            self.inc()

        elif code == "-":
            self.dec()
        
        elif code == ".":
            # print
            os.write(1, chr(self.get()))
        
        elif code == ",":
            # read from stdin
            self.set(ord(os.read(0, 1)[0]))

        elif code == "[" and self.get() == 0:
            # Skip forward to the matching ]
            pc = bracket_map[pc]
            
        elif code == "]" and self.get() != 0:
            # Skip back to the matching [
            pc = bracket_map[pc]

        pc += 1
        return pc

def parse(program):
    parsed = []
    bracket_map = {}
    leftstack = []

    pc = 0
    for char in program:
        if char in ('[', ']', '<', '>', '+', '-', ',', '.'):
            parsed.append(char)

            if char == '[':
                leftstack.append(pc)
            elif char == ']':
                left = leftstack.pop()
                right = pc
                bracket_map[left] = right
                bracket_map[right] = left
            pc += 1
    
    return "".join(parsed), bracket_map

def run(fp):
    program_contents = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        program_contents += read
    os.close(fp)
    program, bm = parse(program_contents)
    mainloop(program, bm)

def entry_point(argv):
    try:
        filename = argv[1]
    except IndexError:
        print "You must supply a filename"
        return 1
    
    run(os.open(filename, os.O_RDONLY, 0777))
    return 0

def target(*args):
    return entry_point, None
    
def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

if __name__ == "__main__":
    entry_point(sys.argv)
