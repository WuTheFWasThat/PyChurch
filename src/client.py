import requests
import json
from engine import *

class RemoteRIPL():
    """
    uri --- the URI of the REST RIPL server to connect to
    """
    def __init__(self, uri):
        self.uri = uri
    
    def assume(self, name_str, expr_lst):
        payload = {"name_str": json.dumps(name_str),
                   "expr_lst": json.dumps(expr_lst)}
        r = requests.put(self.uri + '/assume', data=payload)
        r.raise_for_status()
        return_dict = json.loads(r.content)
        return (return_dict["d_id"], return_dict["val"])

    def observe(self, expr_lst, literal_val):
        payload = {"expr_lst": json.dumps(expr_lst),
                   "literal_val": json.dumps(literal_val)}
        r = requests.put(self.uri + '/observe', data=payload)
        r.raise_for_status()
        return json.loads(r.content)["d_id"]

    def predict(self, expr_lst):
        payload = {"expr_lst": json.dumps(expr_lst)}
        r = requests.put(self.uri + '/predict', data=payload)
        r.raise_for_status()
        return_dict = json.loads(r.content)
        return (return_dict["d_id"], return_dict["val"])
    
    def forget(self, directive_id):
        # FIXME: This REST choice interacts badly with proxies
        r = requests.delete(self.uri + '/' + str(directive_id))
        r.raise_for_status()

    def clear(self):
        # FIXME: This REST choice interacts badly with proxies
        r = requests.delete(self.uri + '/')
        r.raise_for_status()

    def logscore(self, directive_id=None):
        raise Exception("not implemented")

    def infer(self, infer_config=None):
        # FIXME: Define and support a proper config
        payload = {"infer_config": infer_config}
        r = requests.put(self.uri + "/infer", data=payload)
        r.raise_for_status()

    def enumerate(self, truncation_config=None):
        raise Exception("not implemented")

    def report_directives(self, directive_type=None):
        if directive_type is not None:
            raise Exception("not implemented")
        r = requests.get(self.uri + '/')
        r.raise_for_status()
        return json.loads(r.content)

    def report_value(self, directive_id):
        r = requests.get(self.uri + '/' + str(directive_id))
        r.raise_for_status()
        contents = json.loads(r.content)
        return contents["val"]
