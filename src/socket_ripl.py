
import sys
import subprocess
import socket

from ripl import RIPL

def expr_list_to_string(expr_list):
    if type(expr_list) is not list:
        return str(expr_list)
    string = "("
    for i in range(len(expr_list)):
        if i > 0:
            string += " "
        x = expr_list[i]
        if type(x) is list:
            string += expr_list_to_string(x)
        else:
            string += str(x)
    string += ")"
    return string

class SocketRIPL(RIPL):

    def __init__(self, state_type = "traces", kernel_type = "MH"):
        
        self.socket = socket.create_connection(('localhost', 2222))

        self.bufsize = 1048576
        self.socket.recv(self.bufsize)

        self.assumes = {}
        self.observes = {}
        self.predicts = {}
        
        print "Constructing RIPL: " + str((state_type, kernel_type))

    def get_field(self, msg, substring):
        return msg[msg.find(substring) + len(substring):]
    
    def assume(self, name_str, expr_lst):
        msg = "assume " + name_str + " " + expr_list_to_string(expr_lst)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
        msgs = msg.split('\n')
        val = self.get_field(msgs[0], 'value: ')
        id = self.get_field(msgs[1], 'id: ')

        assumption = {}
        assumption["d_id"] = id
        assumption["type"] = "assume"
        assumption["val"] = val
        assumption["name_str"] = name_str
        assumption["expr_lst"] = expr_lst
        self.assumes[id] = assumption
        
        return (id, val)

    def observe(self, expr_lst, literal_val):
        msg = "assume " + name_str + " " + expr_list_to_string(expr_lst)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
        id = self.get_field(msg, 'id: ')

        observation = {}
        observation["d_id"] = id
        observation["type"] = "observe"
        observation["expr_lst"] = expr_lst
        observation["literal_val"] = literal_val
        self.observes[id] = observation
        
        return id

    def predict(self, expr_lst):
        msg = "predict " + expr_list_to_string(expr_lst)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
        msgs = msg.split('\n')
        val = self.get_field(msgs[0], 'value: ')
        id = self.get_field(msgs[1], 'id: ')

        prediction = {}
        prediction["d_id"] = id
        prediction["type"] = "predict"
        prediction["expr_lst"] = expr_lst
        prediction["val"] = val
        self.predicts[id] = prediction
        
        return (id, val)
        
    def forget(self, directive_id):
        msg = "forget " + str(directive_id)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
                 
    def clear(self):
        msg = "clear"
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
                 
    def logscore(self, directive_id=None):
        raise Exception("Not implemented yet")

    def seed(self, seed):
        msg = "seed " + str(seed)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)

    def space(self):
        pid = 22139
        p = subprocess.Popen(["ps", "-o", "rss=", "-p", str(pid)], stdout=subprocess.PIPE)
        s = p.communicate()[0].strip()
        return s

    def infer(self, iters, infer_config=None):
        msg = "infer " + str(iters)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
        
        msgs = msg.split('\n')
        t = self.get_field(msgs[0], 'time: ')
        return t
    
    def toggle_continuous_inference(self):
        raise Exception("Not implemented yet")

    def get_continuous_inference(self):
        raise Exception("Not implemented yet")

    def set_continuous_inference(self, enable=True):
        raise Exception("Not implemented yet")

    def enumerate(self, truncation_config=None):
        raise Exception("Not implemented yet")

    def report_value(self, directive_id):
        msg = "report_directives " + str(directive_id)
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)
        return self.get_field(msg, 'value: ')

    def report_directives(self, directive_type=None):
        if directive_type is None:
            directive_type = ""
        msg = "report_directives " + directive_type
        self.socket.send(msg)
        msg = self.socket.recv(self.bufsize)

        out = {}
        if directive_type == "assume":
            out.update(self.assumes)
        elif directive_type == "observe":
            out.update(self.observes)
        elif directive_type == "predict":
            out.update(self.predicts)
        else:
            out.update(self.assumes)
            out.update(self.observes)
            out.update(self.predicts)

        rows = msg.split('\n')
        rows = rows[3:-1]
        for row in rows:
            entries = row.split('|')
            id = entries[1].strip()
            val = entries[3].strip()
            assert id in out
            out[id]["val"] = val

        return out
            

