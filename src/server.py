import flask
from flask import request
from flask import make_response


import json

import myripl
#ripl = myripl.DirectRIPL()
ripl = myripl.SocketRIPL()

global app
app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    #resp = make_response()
    #resp.status_code = 201
    #resp.data = json.dumps(directives)
    #return resp

    directives = ripl.report_directives()
    return json.dumps(directives)

@app.route('/', methods=['DELETE'])
def clear():
    ripl.clear()
    print "CLEARED"
    return "Cleared"

@app.route('/<int:did>', methods=['DELETE'])
def forget(did):
    ripl.forget(did)
    return "Deleted"

@app.route('/<int:did>', methods=['GET'])
def report_value(did):
    # FIXME: Make this threadsafe, and pass better reporting
    #        through the LocalRIPL caching layer
    if did in ripl.assumes:
        return json.dumps(ripl.assumes[did])
    elif did in ripl.observes:
        return json.dumps(ripl.observes[did])
    elif did in ripl.predicts:
        return json.dumps(ripl.predicts[did])
    else:
        raise Exception("requested invalid")

@app.route('/space', methods=['GET'])
def space():
    s = ripl.space()
    return json.dumps({"space": s})

@app.route('/seed', methods=['PUT'])
def seed():
    seed = json.loads(request.form["seed"])
    print "SEED REQUEST"
    print "seed: ", seed
    ripl.seed(seed)
    return "Seeded with %s" % str(seed)

@app.route('/infer', methods=['PUT'])
def infer():
    # FIXME: Define and support a proper config
    MHiterations = json.loads(request.form["MHiterations"])
    print "INFER REQUEST"
    print "iterations: " + str(MHiterations)
    t = ripl.infer(MHiterations)
    print "time: ", t
    return json.dumps({"time": t})

@app.route('/assume', methods=['PUT'])
def assume():
    name_str = json.loads(request.form["name_str"])
    expr_lst = json.loads(request.form["expr_lst"])
    print "ASSUMPTION REQUEST"
    print "name_str: " + str(name_str)
    print "expr_lst: " + str(expr_lst)
    (d_id, val) = ripl.assume(name_str, expr_lst)
    print "d_id: " + str(d_id)
    print "val: " + str(val)
    return json.dumps({"d_id": d_id,
                       "val": val})

@app.route('/observe', methods=['PUT'])
def observe():
    expr_lst = json.loads(request.form["expr_lst"])
    literal_val = json.loads(request.form["literal_val"])
    print "OBSERVE"
    print str(expr_lst)
    d_id = ripl.observe(expr_lst, literal_val)
    print "d_id: " + str(d_id)
    return json.dumps({"d_id": d_id})

@app.route('/predict', methods=['PUT'])
def predict():
    expr_lst = json.loads(request.form["expr_lst"])
    print "PREDICT"
    print str(expr_lst)
    (d_id, val) = ripl.predict(expr_lst)
    print "d_id: " + str(d_id)
    print "val: " + str(val)
    return json.dumps({"d_id": d_id, "val": val})

if __name__ == '__main__':
    #ripl.set_continuous_inference(enable=True)
    app.run(debug=True, use_reloader=False)

