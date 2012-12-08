import flask
from flask import request
from flask import make_response



import json

import myripl

from threading import Thread
import subprocess
import time

try:
  import argparse
  py_2_6 = False
  parser = argparse.ArgumentParser(description='Engine of Church implementation.')
  parser.add_argument('-e', default='traces', dest = 'engine',
                     help='Type of engine (db, traces, reduced_trace)')
  parser.add_argument('-s', default='', dest = 'socket_server',
                     help = 'Server to use a socket RIPL (otherwise will use direct RIPL = Python server).')
  parser.add_argument('-v', action='store_true', dest = 'verbose',
                     help = 'Print server activity')
  parser.add_argument('-p', default = 5000, action='store', dest = 'port', type = int,
                     help = 'Port number')
  
  flags = parser.parse_args()
except:
  print "WARNING:  USING Python 2.6?  Please use 2.7"
  py_2_6 = True
  class Flags():
    def __init__(self):
      self.engine = 't'
      self.socket_server = 'ec2-jeff-traces-server'
      self.verbose = False
      self.port = 5000
      return
  flags = Flags()

engine_type = flags.engine
if engine_type in ['rt', 'reduced', 'reduced_trace', 'reduced_traces', 'reducedtrace', 'reducedtraces']:
  engine_type = 'reduced traces'
elif engine_type in ['t', 'trace', 'traces']:
  engine_type = 'traces'
elif engine_type in ['r', 'db', 'randomdb']:
  engine_type = 'randomdb'
else:
  raise Exception("Engine %s is not implemented" % engine_type)

if flags.socket_server:
  # spawn new server thread
  print flags.socket_server
  if py_2_6:
    def threadcall():
      subprocess.Popen("./" + flags.socket_server, shell = True)
    t = Thread(target=threadcall, args=())
  else:
    t = Thread(target=subprocess.call, args=([flags.socket_server]))
  t.start()
  
  time.sleep(0.1) # to prevent deadlock

  # get the pid of the spawned process (very much a hack!)
  if py_2_6:
    output = subprocess.Popen("ps | grep -i %s" % flags.socket_server[:8], shell = True, stdout=subprocess.PIPE).communicate()[0]
  else:
    output = subprocess.check_output("ps | grep -i %s" % flags.socket_server, shell=True)
  output = output.split('\n')
  shortest = output[0]
  for x in output:
    if 5 < len(x) < len(shortest):
      shortest = x
  pid = int(shortest[:5])

  ripl = myripl.SocketRIPL(engine_type, "MH", pid)
else:
  ripl = myripl.DirectRIPL(engine_type)

global app
app = flask.Flask(__name__)

def print_verbose(header, message = None, args = None):
  if flags.verbose:
    print "\n----------\n"
    print
    print header
    if args is not None:
      for key in args:
        print key, ": ", args[key]
    if message is not None:
      print message 

def get_response(string, status_code = 200):
    resp = make_response(string)
    resp.status_code = status_code
    #resp.data = json.dumps(directives)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/', methods=['GET'])
def index(): 
    try:
      directives = ripl.report_directives()
    except Exception as e:
      return get_response(e.message, 400)
     
    print_verbose("DIRECTIVES REPORT", directives)
    return get_response(json.dumps(directives))

@app.route('/', methods=['POST'])
# DELETE
def clear():
    try:
      ripl.clear()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("CLEARED")
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['POST'])
# DELETE
def forget(did):
    try:
      ripl.forget(did)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("FORGOTTEN")
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['GET'])
def report_value(did):
    try:
      d = ripl.report_value(did)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("REPORT VALUE", d, {'did': did})
    return get_response(json.dumps(d))

@app.route('/memory', methods=['GET'])
def memory():
    try:
      s = ripl.memory()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("MEMORY", s)
    return get_response(json.dumps({"memory": s}))

@app.route('/entropy', methods=['GET'])
def entropy():
    try:
      h = ripl.entropy()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("ENTROPY", h)
    return get_response(json.dumps({"random_choices": h}))

@app.route('/mhstats/aggregated', methods=['GET'])
def mhstats_aggregated():
    try:
      d = ripl.mhstats_aggregated()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("MHSTATS AGGREGATED", d)
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed', methods=['GET'])
def mhstats_detailed():
    try:
      d = ripl.mhstats_detailed()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("MHSTATS DETAILED", d)
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed/on', methods=['POST'])
def mhstats_on(did):
    try:
      ripl.mhstats_on(did)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("MHSTATS DETAILED ON")
    return get_response(json.dumps({"MESSAGE": "Mhstats On"}))

@app.route('/mhstats/detailed/off', methods=['POST'])
def mhstats_off(did):
    try:
      ripl.mhstats_off(did)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("MHSTATS DETAILED OFF")
    return get_response(json.dumps({"MESSAGE": "Mhstats Off"}))

@app.route('/logscore', methods=['GET'])
def logscore():
    try:
      p = ripl.logscore()
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("LOGSCORE", p)
    return get_response(json.dumps({"total_logscore": p}))

@app.route('/logscore/<int:did>', methods=['GET'])
def logscore_observe(did):
    try:
      p = ripl.logscore(did)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("LOGSCORE", p, {"did": did})
    return get_response(json.dumps({"directive_logscore": p}))

@app.route('/seed', methods=['POST'])
def seed():
    seed = json.loads(request.form["seed"])
    print_verbose("SEED", seed)
    try:
      ripl.seed(seed)
    except Exception as e:
      return get_response(e.message, 400)
    return get_response("Seeded with %s" % str(seed))

@app.route('/infer', methods=['POST'])
def infer():
    MHiterations = json.loads(request.form["MHiterations"])
    rerun_first = json.loads(request.form["rerun"])
    try:
      t = ripl.infer(MHiterations, rerun_first)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("INFER", None, {"iters": MHiterations, "rerun": rerun_first, "time": t})
    return get_response(json.dumps({"time": t}))

@app.route('/assume', methods=['POST'])
def assume():
    name_str = json.loads(request.form["name_str"])
    expr_lst = json.loads(request.form["expr_lst"])
    try:
      (d_id, val) = ripl.assume(name_str, expr_lst)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("ASSUME", {"d_id": d_id, "val": val}, {"name": name_str, "expression": expr_lst})
    return get_response(json.dumps({"d_id": d_id,
                       "val": val}))

@app.route('/observe', methods=['POST'])
def observe():
    expr_lst = json.loads(request.form["expr_lst"])
    literal_val = json.loads(request.form["literal_val"])
    try:
      d_id = ripl.observe(expr_lst, literal_val)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("OBSERVE", {"d_id": d_id}, {"expression": expr_lst, "obs_val": literal_val})
    return get_response(json.dumps({"d_id": d_id}))

@app.route('/predict', methods=['POST'])
def predict():
    expr_lst = json.loads(request.form["expr_lst"])
    try:
      (d_id, val) = ripl.predict(expr_lst)
    except Exception as e:
      return get_response(e.message, 400)
    print_verbose("PREDICT", {"d_id": d_id, "val": val}, {"expression": expr_lst})
    return get_response(json.dumps({"d_id": d_id, "val": val}))

@app.route('/start_cont_infer', methods=['POST'])
def start_cont_infer():
    try:
      ripl.start_continuous_inference();
    except Exception as e:
      return get_response(e.message, 400)
    return get_response(json.dumps({"started": True}))

@app.route('/stop_cont_infer', methods=['POST'])
def stop_cont_infer():
    try:
      ripl.stop_continuous_inference();
    except Exception as e:
      return get_response(e.message, 400)
    return get_response(json.dumps({"stopped": True}))

@app.route('/cont_infer_status', methods=['GET'])
def cont_infer_status():
    try:
      continuous_inference = ripl.continuous_inference_status()
    except Exception as e:
      return get_response(e.message, 400)
    if continuous_inference:
      return get_response(json.dumps({"status": "on"}))
    else:
      return get_response(json.dumps({"status": "off"}))

if __name__ == '__main__':
    #ripl.set_continuous_inference(enable=True)
    app.run(debug=True, use_reloader=False, port = flags.port)

