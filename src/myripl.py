from engine.directives import Directives
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

from ripl import RIPL

try:
  from pypy.rlib import rsocket as socket
  use_pypy = True
except:
  import socket
  use_pypy = False

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

class MyRIPL(RIPL):
    
    def __init__(self, engine_type = "traces", kernel_type = "MH", pid = None):
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
         
        self.init_help(pid)

    def init_help(self, pid):
        raise Exception("Not implemented yet")

    def get_pid(self):
        raise Exception("Not implemented yet")

    def get_recv_msg(self, msg):
        raise Exception("Not implemented yet")

    def get_field(self, msg, substring):
        return msg[msg.find(substring) + len(substring):]
    
    def assume(self, name_str, expr_lst):
        msg = "assume " + name_str + " " + expr_list_to_string(expr_lst)

        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        val = self.string_to_value(self.get_field(msgs[0], 'value: '))
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
        msg = "observe " + expr_list_to_string(expr_lst) + ' ' + str(literal_val)

        recv_msg = self.get_recv_msg(msg)
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

        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        val = self.string_to_value(self.get_field(msgs[0], 'value: '))
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

        directive = self.directive_list[id - 1]
        if directive["directive-type"] == "DIRECTIVE-OBSERVE":
          directive["directive-type"] = "FORGOTTEN-OBSERVE"
        elif directive["directive-type"] == "DIRECTIVE-PREDICT":
          directive["directive-type"] = "FORGOTTEN-PREDICT"
        else:
          raise Exception("Can only forget non-forgotten observes and predicts")

        recv_msg = self.get_recv_msg(msg)
                 
    def clear(self):
        msg = "clear"
        recv_msg = self.get_recv_msg(msg)

        self.directive_list = []
        
        self.assumes = {}
        self.observes = {}
        self.predicts = {}
                 
    def logscore(self, directive_id=None):
        if directive_id is None:
          msg = "logscore" 
        else:
          msg = "logscore" + str(directive_id)

        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        score = self.get_field(msgs[0], 'logp: ')
        return score

    def entropy(self):
        msg = "entropy" 
        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        entropy = self.get_field(msgs[0], 'entropy: ')
        return entropy

    def mhstats_aggregated(self):
        msg = "mhstats aggregated"
        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        made = self.get_field(msgs[0], 'made-proposals: ')
        accepted = self.get_field(msgs[1], 'accepted-proposals: ')
        return {'made-proposals': made, 'accepted-proposals': accepted}

    def mhstats_detailed(self):
        msg = "mhstats detailed"
        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        d = {}
        for i in range(len(msgs) / 3):
          node = self.get_field(msgs[3 * i], 'node: ')
          made = self.get_field(msgs[3 * i + 1], '  made-proposals: ')
          accepted = self.get_field(msgs[3 * i + 2], '  accepted-proposals: ')
          d[node] = {'made-proposals': made, 'accepted-proposals': accepted}
        return d

    def mhstats_on(self):
        msg = "mhstats on"
        recv_msg = self.get_recv_msg(msg)

    def mhstats_off(self):
        msg = "mhstats off"
        recv_msg = self.get_recv_msg(msg)

    def seed(self, seed):
        msg = "seed " + str(seed)
        recv_msg = self.get_recv_msg(msg)

    def memory(self):
        pid = self.get_pid() 
        p = subprocess.Popen(["ps", "-o", "rss=", "-p", str(pid)], stdout=subprocess.PIPE)
        s = p.communicate()[0].strip()
        return s

    def infer(self, iters, infer_config=None):
        msg = "infer " + str(iters)

        recv_msg = self.get_recv_msg(msg)
        
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
        msg = "report_value " + str(id - 1)

        recv_msg = self.get_recv_msg(msg)
        string_val = self.get_field(recv_msg, 'value: ')

        d = self.directive_list[id-1] 
        d["value"] = self.string_to_value(string_val)
        return d

    def string_to_value(self, string_val):
        if string_val == 'True':
          return True
        elif string_val == 'False':
          return False
        else:
          try:
            intval = int(string_val)
            return intval
          except:
            try:
              floatval = float(string_val)
              return floatval
            except:
              return string_val

    def report_directives(self, desired_directive_type=None):
        if desired_directive_type is None:
            directive_types = ["DIRECTIVE-ASSUME", "DIRECTIVE-PREDICT", "DIRECTIVE-OBSERVE"]
        else:
            directive_types = [desired_directive_type]

        directive_report = []
        for id in range(1, len(self.directive_list) + 1):
          d = self.directive_list[id-1] 
          directive_type = d['directive-type']
          if directive_type in directive_types:
            if directive_type in ['DIRECTIVE-ASSUME', 'DIRECTIVE-PREDICT']:
              d = self.report_value(id)
            directive_report.append(d)
        return directive_report

class DirectRIPL(MyRIPL):
    def init_help(self, pid = None):
        return 

    def get_pid(self):
        return os.getpid()

    def get_recv_msg(self, msg):
        return self.directives.parse_and_run_command(msg)

class SocketRIPL(MyRIPL):
    def init_help(self, pid):
        self.socket = socket.socket()
        self.socket.connect(('localhost', 2222))

        self.bufsize = 1048576
        self.socket.recv(self.bufsize)

        self.pid = pid
        
    def get_pid(self):
        return self.pid

    def get_recv_msg(self, msg):
        self.socket.send(msg)
        return self.socket.recv(self.bufsize)
