import flask
from flask import request
from flask import make_response

import argparse

import json

import myripl

parser = argparse.ArgumentParser(description='Engine of Church implementation.')
parser.add_argument('-e', default='traces', dest = 'engine',
                   help='Type of engine (db, traces, reduced_trace)')
parser.add_argument('-s', action='store_true', dest = 'use_socket',
                   help = 'Use the socket RIPL.  Remember to change the PID!')
parser.add_argument('-v', action='store_true', dest = 'verbose',
                   help = 'Print server activity')

flags = parser.parse_args()

engine_type = flags.engine
if engine_type in ['rt', 'reduced', 'reduced_trace', 'reduced_traces', 'reducedtrace', 'reducedtraces']:
  engine_type = 'reduced traces'
elif engine_type in ['t', 'trace', 'traces']:
  engine_type = 'traces'
elif engine_type in ['r', 'db', 'randomdb']:
  engine_type = 'randomdb'
else:
  raise Exception("Engine %s is not implemented" % engine_type)

if flags.use_socket:
  ripl = myripl.SocketRIPL(engine_type)
else:
  ripl = myripl.DirectRIPL(engine_type)

global app
app = flask.Flask(__name__)

def print_verbose(header, message = None, args = None):
  if flags.verbose:
    print
    print header
    if args is not None:
      for key in args:
        print key, ": ", args[key]
    if message is not None:
      print message 
    print "\n----------\n"

def get_response(string):
    resp = make_response(string)
    #resp.status_code = 201
    #resp.data = json.dumps(directives)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/', methods=['GET'])
def index():
    directives = ripl.report_directives()
    print_verbose("DIRECTIVES REPORT", directives)
    return get_response(json.dumps(directives))

@app.route('/', methods=['POST'])
# DELETE
def clear():
    ripl.clear()
    print_verbose("CLEARED")
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['POST'])
# DELETE
def forget(did):
    ripl.forget(did)
    print_verbose("FORGOTTEN")
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['GET'])
def report_value(did):
    d = ripl.report_value(did)
    print_verbose("REPORT VALUE", d, {'did': did})
    return get_response(json.dumps(d))

@app.route('/memory', methods=['GET'])
def memory():
    s = ripl.memory()
    print_verbose("MEMORY", s)
    return get_response(json.dumps({"memory": s}))

@app.route('/entropy', methods=['GET'])
def entropy():
    h = ripl.entropy()
    print_verbose("ENTROPY", h)
    return get_response(json.dumps({"random_choices": h}))

@app.route('/mhstats/aggregated', methods=['GET'])
def mhstats_aggregated():
    d = ripl.mhstats_aggregated()
    print_verbose("MHSTATS AGGREGATED", d)
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed', methods=['GET'])
def mhstats_detailed():
    d = ripl.mhstats_detailed()
    print_verbose("MHSTATS DETAILED", d)
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed/on', methods=['POST'])
def mhstats_on(did):
    ripl.mhstats_on(did)
    print_verbose("MHSTATS DETAILED ON")
    return get_response(json.dumps({"MESSAGE": "Mhstats On"}))

@app.route('/mhstats/detailed/off', methods=['POST'])
def mhstats_off(did):
    ripl.mhstats_off(did)
    print_verbose("MHSTATS DETAILED OFF")
    return get_response(json.dumps({"MESSAGE": "Mhstats Off"}))

@app.route('/logscore', methods=['GET'])
def logscore():
    p = ripl.logscore()
    print_verbose("LOGSCORE", p)
    return get_response(json.dumps({"directive_logscore": p}))

@app.route('/logscore/<int:did>', methods=['GET'])
def logscore_observe(did):
    p = ripl.logscore(did)
    print_verbose("LOGSCORE", p, {"did": did})
    return get_response(json.dumps({"directive_logscore": p}))

@app.route('/seed', methods=['POST'])
def seed():
    seed = json.loads(request.form["seed"])
    print_verbose("SEED", seed)
    ripl.seed(seed)
    return get_response("Seeded with %s" % str(seed))

@app.route('/infer', methods=['POST'])
def infer():
    MHiterations = json.loads(request.form["MHiterations"])
    t = ripl.infer(MHiterations)
    print_verbose("INFER", None, {"iters": MHiterations, "time": t})
    return get_response(json.dumps({"time": t}))

@app.route('/assume', methods=['POST'])
def assume():
    name_str = json.loads(request.form["name_str"])
    expr_lst = json.loads(request.form["expr_lst"])
    (d_id, val) = ripl.assume(name_str, expr_lst)
    print_verbose("ASSUME", {"d_id": d_id, "val": val}, {"name": name_str, "expression": expr_lst})
    return get_response(json.dumps({"d_id": d_id,
                       "val": val}))

@app.route('/observe', methods=['POST'])
def observe():
    expr_lst = json.loads(request.form["expr_lst"])
    literal_val = json.loads(request.form["literal_val"])
    d_id = ripl.observe(expr_lst, literal_val)
    print_verbose("OBSERVE", {"d_id": d_id}, {"expression": expr_lst, "obs_val": literal_val})
    return json.dumps({"d_id": d_id})

@app.route('/predict', methods=['POST'])
def predict():
    expr_lst = json.loads(request.form["expr_lst"])
    (d_id, val) = ripl.predict(expr_lst)
    print_verbose("PREDICT", {"d_id": d_id, "val": val}, {"expression": expr_lst})
    return get_response(json.dumps({"d_id": d_id, "val": val}))

if __name__ == '__main__':
    #ripl.set_continuous_inference(enable=True)
    app.run(debug=True, use_reloader=False)

