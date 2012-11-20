from engine.directives import Directives
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

from ripl import RIPL


import os
import subprocess
import sys

sys.setrecursionlimit(10000)

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

# TODO:  make DirectRIPL and SocketRIPL into same thing, which just takes a function from strings to strings
# need to deal with the space pid thing though

# TODO : Make directives do the stuff with report directives

class DirectRIPL(RIPL):
    
    def __init__(self, engine_type = "traces", kernel_type = "MH"):
        if engine_type == 'reduced traces':
          engine = ReducedTraces()
        elif engine_type == 'traces':
          engine = Traces()
        elif engine_type == 'randomdb':
          engine = RandomDB()
        else:
          raise Exception("Engine %s is not implemented" % engine_type)
        
        self.directives = Directives(engine)

        self.directive_list = []
        
        self.assumes = {}
        self.observes = {}
        self.predicts = {}
        
        print "Constructing RIPL: " + str((engine_type, kernel_type))

    def get_field(self, msg, substring):
        return msg[msg.find(substring) + len(substring):]
    
    def assume(self, name_str, expr_lst):
        msg = "assume " + name_str + " " + expr_list_to_string(expr_lst)

        recv_msg = self.directives.parse_and_run_command(msg)
        msgs = recv_msg.split('\n')
        val = self.get_field(msgs[0], 'value: ')
        id = int(self.get_field(msgs[1], 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-ASSUME"
        directive["directive-expression"] = msg
        directive["value"] = val
        directive["name"] = name_str
        self.directive_list.append(directive)

        self.assumes[id] = directive
        return (id, val)

    def observe(self, expr_lst, literal_val):
        msg = "assume " + name_str + " " + expr_list_to_string(expr_lst)

        recv_msg = self.directives.parse_and_run_command(msg)
        id = int(self.get_field(recv_msg, 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-OBSERVE"
        directive["directive-expression"] = msg
        #directive["value"] = literal_val
        self.directive_list.append(directive)
        
        self.observes[id] = directive
        return id

    def predict(self, expr_lst):
        msg = "predict " + expr_list_to_string(expr_lst)

        recv_msg = self.directives.parse_and_run_command(msg)
        msgs = recv_msg.split('\n')
        val = self.get_field(msgs[0], 'value: ')
        id = int(self.get_field(msgs[1], 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-PREDICT"
        directive["directive-expression"] = msg
        directive["value"] = val
        self.directive_list.append(directive)

        self.predicts[id] = directive
        return (id, val)
        
    def forget(self, id):
        msg = "forget " + str(id - 1)
        recv_msg = self.directives.parse_and_run_command(msg)
                 
    def clear(self):
        msg = "clear"
        recv_msg = self.directives.parse_and_run_command(msg)
                 
    def logscore(self, directive_id=None):
        raise Exception("Not implemented yet")

    def seed(self, seed):
        msg = "seed " + str(seed)
        recv_msg = self.directives.parse_and_run_command(msg)

    def space(self):
        pid = os.getpid()
        p = subprocess.Popen(["ps", "-o", "rss=", "-p", str(pid)], stdout=subprocess.PIPE)
        s = p.communicate()[0].strip()
        return s

    def infer(self, iters, infer_config=None):
        msg = "infer " + str(iters)

        recv_msg = self.directives.parse_and_run_command(msg)
        
        msgs = recv_msg.split('\n')
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

    def report_value(self, id):
        msg = "report_directives " + str(id - 1)

        recv_msg = self.directives.parse_and_run_command(msg)
        return self.get_field(recv_msg, 'value: ')

    def report_directives(self, desired_directive_type=None):
        if desired_directive_type is None:
            desired_directive_type = ""

        directive_report = []
        for id in range(1, len(self.directive_list) + 1):
          directive_type = self.directive_list[id-1]
          if desired_directive_type in ["", directive_type]:
            d = self.directive_list[id-1] 
            if directive_type in ['DIRECTIVE-ASSUME', 'DIRECTIVE-PREDICT']:
              d["value"] = self.report_value(id)
            directive_report.append(d)
        return directive_report

