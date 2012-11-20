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
        id = self.get_field(msgs[1], 'id: ')

        directive = {}
        directive["id"] = id
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
        id = self.get_field(recv_msg, 'id: ')

        directive = {}
        directive["id"] = id
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
        id = self.get_field(msgs[1], 'id: ')

        directive = {}
        directive["id"] = id
        directive["directive-type"] = "DIRECTIVE-PREDICT"
        directive["directive-expression"] = msg
        directive["value"] = val
        self.directive_list.append(directive)

        self.predicts[id] = directive
        return (id, val)
        
    def forget(self, directive_id):
        msg = "forget " + str(directive_id)

        msg = self.directives.parse_and_run_command(msg)
                 
    def clear(self):
        msg = "clear"

        msg = self.directives.parse_and_run_command(msg)
                 
    def logscore(self, directive_id=None):
        raise Exception("Not implemented yet")

    def seed(self, seed):
        msg = "seed " + str(seed)

        msg = self.directives.parse_and_run_command(msg)

    def space(self):
        pid = os.getpid()
        p = subprocess.Popen(["ps", "-o", "rss=", "-p", str(pid)], stdout=subprocess.PIPE)
        s = p.communicate()[0].strip()
        return s

    def infer(self, iters, infer_config=None):
        msg = "infer " + str(iters)

        msg = self.directives.parse_and_run_command(msg)
        
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

        msg = self.directives.parse_and_run_command(msg)
        return self.get_field(msg, 'value: ')

    def report_directives(self, directive_type=None):
        if directive_type is None:
            directive_type = ""
        msg = "report_directives " + directive_type

        msg = self.directives.parse_and_run_command(msg)

        directive_report = []
        for id in range(len(self.directives)):
          directive_type = self.directives[id]
          if desired_directive_type in ["", directive_type]:
            d = {}
            d["directive-id"] = str(id)
            if directive_type == 'assume':
              (varname, expr) = self.assumes[id]
              d["directive-type"] = "DIRECTIVE-ASSUME"
              d["directive-expression"] = expr.__str__()
              d["name"] = varname
              d["value"] = self.report_value(id).__str__()
              directive_report.append(d)
            elif directive_type == 'observe':
              (expr, val, active) = self.observes[id]
              d["directive-type"] = "DIRECTIVE-OBSERVE"
              d["directive-expression"] = expr.__str__()
              #d["value"] = self.report_value(id).__str__()
              directive_report.append(d)
            elif directive_type == 'predict':
              (expr, active) = self.predicts[id]
              d["directive-type"] = "DIRECTIVE-PREDICT"
              d["directive-expression"] = expr.__str__()
              d["value"] = self.report_value(id).__str__()
              directive_report.append(d)
            else:
              raise RException("Invalid directive %s" % directive_type)
    return directive_report


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
            
