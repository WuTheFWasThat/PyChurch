from engine.directives import Directives
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

import random

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

import threading

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

class inferThread(threading.Thread):
    def __init__(self, ripl):
        self.ripl = ripl
        threading.Thread.__init__(self)

    def run(self):
        while True:
          self.ripl.lock.acquire()
          if self.ripl.continuous_inference:
            self.ripl.infer_help() # TODO: maybe infer 10 times?  allow as argument?
            self.ripl.lock.release()
          else:
            self.ripl.lock.release()
            return

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
        
        self.lock = threading.Lock()
        self.thread = inferThread(self)
        self.continuous_inference = False

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
        self.lock.acquire()

        msg = "ASSUME " + name_str + " " + expr_list_to_string(expr_lst)

        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        val = self.string_to_value(self.get_field(msgs[0], 'value: '))
        id = int(self.get_field(msgs[1], 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-ASSUME"
        directive["directive-expression"] = "(" + msg + ")"
        directive["value"] = val
        directive["name"] = name_str
        self.directive_list.append(directive)

        self.assumes[id] = directive

        self.lock.release()
        return (id, val)
    
    def start_continuous_inference(self):
        self.lock.acquire()
        if not self.continuous_inference:
          self.continuous_inference = True
          self.thread.start()
        self.lock.release()
        return

    def stop_continuous_inference(self):
        self.lock.acquire()
        self.continuous_inference = False
        self.lock.release()

        # This also makes sure old thread is done doing what it was doing
        self.lock.acquire()
        self.thread = inferThread(self)
        self.lock.release()
        return

    def continuous_inference_status(self):
        self.lock.acquire()
        status = self.continuous_inference
        self.lock.release()
        return status

    def observe(self, expr_lst, literal_val):
        self.lock.acquire()

        msg = "OBSERVE " + expr_list_to_string(expr_lst) + ' ' + str(literal_val)

        recv_msg = self.get_recv_msg(msg)
        id = int(self.get_field(recv_msg, 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-OBSERVE"
        directive["directive-expression"] = "(" + msg + ")"
        #directive["value"] = literal_val
        self.directive_list.append(directive)
        
        self.observes[id] = directive

        self.lock.release()
        return id

    def predict(self, expr_lst):
        self.lock.acquire()

        msg = "PREDICT " + expr_list_to_string(expr_lst)

        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        val = self.string_to_value(self.get_field(msgs[0], 'value: '))
        id = int(self.get_field(msgs[1], 'id: ')) + 1

        directive = {}
        directive["directive-id"] = id
        directive["directive-type"] = "DIRECTIVE-PREDICT"
        directive["directive-expression"] = "(" + msg + ")"
        directive["value"] = val
        self.directive_list.append(directive)

        self.predicts[id] = directive

        self.lock.release()
        return (id, val)
        
    def forget(self, id):
        self.lock.acquire()
        msg = "forget " + str(id - 1)

        directive = self.directive_list[id - 1]
        if directive["directive-type"] == "DIRECTIVE-OBSERVE":
          directive["directive-type"] = "FORGOTTEN-OBSERVE"
        elif directive["directive-type"] == "DIRECTIVE-PREDICT":
          directive["directive-type"] = "FORGOTTEN-PREDICT"
        else:
          raise Exception("Can only forget non-forgotten observes and predicts")

        recv_msg = self.get_recv_msg(msg)
        self.lock.release()
                 
    def clear(self):
        self.lock.acquire()
        msg = "clear"
        recv_msg = self.get_recv_msg(msg)

        self.directive_list = []
        
        self.assumes = {}
        self.observes = {}
        self.predicts = {}
        self.lock.release()
                 
    def logscore(self, directive_id=None):
        self.lock.acquire()
        if directive_id is None:
          msg = "logscore" 
        else:
          msg = "logscore" + str(directive_id)

        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        score = self.get_field(msgs[0], 'logp: ')
        self.lock.release()
        return score

    def entropy(self):
        self.lock.acquire()
        msg = "entropy" 
        recv_msg = self.get_recv_msg(msg)
        msgs = recv_msg.split('\n')
        entropy = self.get_field(msgs[0], 'entropy: ')
        self.lock.release()
        return entropy

    def mhstats_aggregated(self):
        self.lock.acquire()
        msg = "mhstats aggregated"
        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        made = self.get_field(msgs[0], 'made-proposals: ')
        accepted = self.get_field(msgs[1], 'accepted-proposals: ')
        self.lock.release()
        return {'made-proposals': made, 'accepted-proposals': accepted}

    def mhstats_detailed(self):
        self.lock.acquire()
        msg = "mhstats detailed"
        recv_msg = self.get_recv_msg(msg)

        msgs = recv_msg.split('\n')
        d = {}
        for i in range(len(msgs) / 3):
          node = self.get_field(msgs[3 * i], 'node: ')
          made = self.get_field(msgs[3 * i + 1], '  made-proposals: ')
          accepted = self.get_field(msgs[3 * i + 2], '  accepted-proposals: ')
          d[node] = {'made-proposals': made, 'accepted-proposals': accepted}
        self.lock.release()
        return d

    def mhstats_on(self):
        self.lock.acquire()
        msg = "mhstats on"
        recv_msg = self.get_recv_msg(msg)
        self.lock.release()

    def mhstats_off(self):
        self.lock.acquire()
        msg = "mhstats off"
        recv_msg = self.get_recv_msg(msg)
        self.lock.release()

    def seed(self, seed):
        self.lock.acquire()
        msg = "seed " + str(seed)
        recv_msg = self.get_recv_msg(msg)
        self.lock.release()

    def memory(self):
        self.lock.acquire()
        pid = self.get_pid() 
        p = subprocess.Popen(["ps", "-o", "rss=", "-p", str(pid)], stdout=subprocess.PIPE)
        s = p.communicate()[0].strip()
        self.lock.release()
        return s

    def infer_help(self, iters = 1, rerun_first = False):
        msg = "infer " + str(iters)  + " " + str(rerun_first)

        recv_msg = self.get_recv_msg(msg)
        
        msgs = recv_msg.split('\n')
        t = self.get_field(msgs[0], 'time: ')
        return t

    def infer(self, iters = 1, rerun_first = False):
        self.lock.acquire()
        t = self.infer_help(iters, rerun_first)
        self.lock.release()
        return t
    
    def enumerate(self, truncation_config=None):
        raise Exception("Not implemented yet")

    def report_value(self, id):
        self.lock.acquire()
        msg = "report_value " + str(id - 1)

        recv_msg = self.get_recv_msg(msg)
        string_val = self.get_field(recv_msg, 'value: ')

        d = self.directive_list[id-1] 
        d["value"] = self.string_to_value(string_val)
        self.lock.release()
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
