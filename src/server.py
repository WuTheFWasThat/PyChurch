import flask
from flask import request
from flask import make_response


import json

import myripl
ripl = myripl.DirectRIPL()
#ripl = myripl.SocketRIPL()

global app
app = flask.Flask(__name__)

def get_response(string):
    resp = make_response(string)
    #resp.status_code = 201
    #resp.data = json.dumps(directives)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/', methods=['GET'])
def index():
    directives = ripl.report_directives()
    return get_response(json.dumps(directives))

@app.route('/', methods=['POST'])
# DELETE
def clear():
    ripl.clear()
    print "CLEARED"
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['POST'])
# DELETE
def forget(did):
    ripl.forget(did)
    print "FORGOTTEN"
    return get_response(json.dumps({}))

@app.route('/<int:did>', methods=['GET'])
def report_value(did):
    print "REPORTED VALUE"
    print "did: ", did
    d = ripl.report_value(did)
    print d
    return get_response(json.dumps(d))

@app.route('/memory', methods=['GET'])
def memory():
    s = ripl.memory()
    return get_response(json.dumps({"memory": s}))

@app.route('/entropy', methods=['GET'])
def entropy():
    h = ripl.entropy()
    return get_response(json.dumps({"random_choices": h}))

@app.route('/mhstats/aggregated', methods=['GET'])
def mhstats_aggregated():
    d = ripl.mhstats_aggregated()
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed', methods=['GET'])
def mhstats_detailed():
    d = ripl.mhstats_detailed()
    return get_response(json.dumps(d))

@app.route('/mhstats/detailed/on', methods=['POST'])
def mhstats_on(did):
    ripl.mhstats_on(did)
    return get_response(json.dumps({"MESSAGE": "Mhstats On"}))

@app.route('/mhstats/detailed/off', methods=['POST'])
def mhstats_off(did):
    ripl.mhstats_off(did)
    return get_response(json.dumps({"MESSAGE": "Mhstats Off"}))

@app.route('/logscore', methods=['GET'])
def logscore():
    p = ripl.logscore()
    return get_response(json.dumps({"directive_logscore": p}))

@app.route('/logscore/<int:did>', methods=['GET'])
def logscore_observe(did):
    p = ripl.logscore(did)
    return get_response(json.dumps({"directive_logscore": p}))

@app.route('/seed', methods=['POST'])
def seed():
    seed = json.loads(request.form["seed"])
    print "SEED REQUEST"
    print "seed: ", seed
    ripl.seed(seed)
    return get_response("Seeded with %s" % str(seed))

@app.route('/infer', methods=['POST'])
def infer():
    # FIXME: Define and support a proper config
    MHiterations = json.loads(request.form["MHiterations"])
    print "INFER REQUEST"
    print "iterations: " + str(MHiterations)
    t = ripl.infer(MHiterations)
    print "time: ", t
    return get_response(json.dumps({"time": t}))

@app.route('/assume', methods=['POST'])
def assume():
    name_str = json.loads(request.form["name_str"])
    expr_lst = json.loads(request.form["expr_lst"])
    print "ASSUMPTION REQUEST"
    print "name_str: " + str(name_str)
    print "expr_lst: " + str(expr_lst)
    (d_id, val) = ripl.assume(name_str, expr_lst)
    print "d_id: " + str(d_id)
    print "val: " + str(val)
    return get_response(json.dumps({"d_id": d_id,
                       "val": val}))

@app.route('/observe', methods=['POST'])
def observe():
    expr_lst = json.loads(request.form["expr_lst"])
    literal_val = json.loads(request.form["literal_val"])
    print "OBSERVE"
    print str(expr_lst)
    d_id = ripl.observe(expr_lst, literal_val)
    print "d_id: " + str(d_id)
    return json.dumps({"d_id": d_id})

@app.route('/predict', methods=['POST'])
def predict():
    expr_lst = json.loads(request.form["expr_lst"])
    print "PREDICT"
    print str(expr_lst)
    (d_id, val) = ripl.predict(expr_lst)
    print "d_id: " + str(d_id)
    print "val: " + str(val)
    return get_response(json.dumps({"d_id": d_id, "val": val}))

if __name__ == '__main__':
    #ripl.set_continuous_inference(enable=True)
    app.run(debug=True, use_reloader=False)

