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
  resp.headers['Access-Control-Allow-Origin'] = '*'
  return resp

@app.route('/', methods=['GET'])
def index():
    #resp = make_response()
    #resp.status_code = 201
    #resp.data = json.dumps(directives)
    #return resp

    directives = ripl.report_directives()
    return get_response(json.dumps(directives))

@app.route('/', methods=['DELETE'])
def clear():
    ripl.clear()
    print "CLEARED"
    return get_response("Cleared")

@app.route('/<int:did>', methods=['DELETE'])
def forget(did):
    ripl.forget(did)
    return get_response("Deleted")

@app.route('/<int:did>', methods=['GET'])
def report_value(did):
    print "REPORTED VALUE"
    print "did: ", did
    d = ripl.report_value(did)
    print d
    return get_response(json.dumps(d))

@app.route('/space', methods=['GET'])
def space():
    s = ripl.space()
    return get_response(json.dumps({"space": s}))

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

