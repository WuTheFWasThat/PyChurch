#### NOTE: This project is defunct.

#### If you're interested, please check out these more recent projects:
- [Web PPL](http://webppl.org/)
- [Venture](http://probcomp.csail.mit.edu/venture/)


# PyChurch

[Read paper for details](papers/MEng%20thesis.pdf)

## RUNNING LOCALLY

To run a shell:
  `python run_program.py [-e ENGINE]`

To run a program:
  `python run_program.py [-e ENGINE] [-p PROGRAM]`

Flags:
```
ENGINE:  r = randomdb, t = traces, rt = reduced traces
PROGRAM:  The directory of some Church program.
```

## RUN A SERVER

All servers conform to a common REST API.

To run the python server:
  `python server.py [-e ENGINE] [-v] [-p PORT]`

To run a C server:
  `python server.py [-s BINARY] [-v] [-p PORT]`

Flags:
```
ENGINE:  r = randomdb, t = traces, rt = reduced traces
BINARY:  The directory of some C binary
PORT: The number of some port
The -v flag toggles whether the server should print its activity
```

## SETUP ON EC2

See [ec2_setup.txt](src/ec2_setup.txt)

## COMPILING THE C BINARIES

You can also compile a faster version of the server by doing the following:

1.  (OPTIONAL) Open `socket_server.py`, and change engine_type to what you'd like.
2.  Install pypy.
3.  Run (replace the path to the pypy folder as appropriate):
        ```python /Applications/pypy/rpython/bin/rpython socket_server.py```
    For a tracing JIT version (NOT YET READY):
        ```python /Applications/pypy/rpython/bin/rpython --opt=jit socket_server.py```
     WARNING:  This can take a long time.
4.  This should create a binary called `socket_server-c`.  You may want to rename it

## DEFINING CUSTOM XRPs

See [values.py](src/engine/values.py) for class definition

See [xrp.py](src/engine/xrp.py) for examples

Remember to set self.sample, depending on whether your XRP is a sampler or rescorer!

## ADDING PRIMITIVE PROCEDURES

See [directives.py](src/engine/directives.py) for examples. (Search for "PRIMITIVE PROCEDURES".)
The syntax for expressions can be found near the bottom of [expressions.py](src/engine/expressions.py) (or you can simply follow the examples).
Don't forget the 3rd argument must be set to 'True'.

## KNOWN ISSUES

- Propagation should use a priority queue (it is currently wrong, sometimes)
- Traces could be more intelligent at propagating up through arguments (and then, we can use the proper XRP if)
- Some Jenkins tests fail
- Outermost observe shouldn't be required
- Assumes resampling XRPs are all deterministic
- Needs to use unsample
