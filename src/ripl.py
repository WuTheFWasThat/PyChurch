# FIXME SOMEDAY: play with a version that uses dictionaries with named
#                arguments instead of pythonic lists, for expressions and
#                for the basic (homoiconic) value type. this could lead to
#                greater ease in program induction, and greater efficiency
#                for very large programs (where the conditional independence
#                pattern of the data structure representing the code becomes
#                important again).

# FIXME: standardize autodoc to fit python's conventions and play with
#        iPython's help

# FIXME: Better document exceptions here

import sys
from engine.globals import Environment, Traces, RandomDB
#from engine.globals import *
#from engine.directives import *

##import evaluators
##import datatypes
##import kernels
##import xrps
##import threading
##import time

import socket

class RIPL:
    # returns a tuple of (<directive id>, val) or throws
    # an exception
    # efficiently persistently updated
    def assume(self, name_str, expr_lst):
        raise Exception("Not implemented")

    # returns a tuple of (<directive id>)
    # or throws an exception 
    # efficiently persistently updated
    def observe(self, expr_lst, literal_val):
        raise Exception("Not implemented")

    # returns a tuple of (<directive id>, val)
    # or throws an exception
    # efficiently persistently updated FIXME does this get asymptotics right?
    def predict(self, expr_lst):
        raise Exception("Not implemented")

    # tells the engine to forget a given OBSERVE or PREDICT directive.
    def forget(self, directive_id):
        raise Exception("Not implemented")

    # tells the engine to clear everything
    def clear(self):
        raise Exception("Not implemented")

    # returns the log probability of either the current belief in the engine
    # (unnormalized joint score) or the marginal probability of the random
    # choice in the given predict or observe (if there is a single random
    # choice at the farthest-out position).
    # FIXME: currently, this is not efficiently persistently updated
    def logscore(self, directive_id=None):
        raise Exception("Not implemented")


    # NOTE: The next two things, infer and enumerate, both require open-ended
    #       and potentially evolving configurations (to customize inference,
    #       include fine-grained control, set truncation search approaches,
    #       etc). This is being done opaquely at this layer to simplify using
    #       JSON blobs passed all the way in for this kind of stuff, without
    #       requiring a ton of rewriting. Maybe this isn't the best choice?

    # make the engine imagine a new explanation and update the values of all
    # visible directives. 
    # 
    # by default, all engines should make a best effort to have this
    # new explanation be close to a fresh sample from the posterior.
    #
    # configurations allow control of inference amount, etc.
    def infer(self, infer_config=None):
        raise Exception("Not implemented")

    # returns an immutable object containing as many execution traces
    # as possible, along with their joint and posterior probabilities.
    # truncation_config lets you specify hints for how to do this,
    # approximation parameters, and the like.
    def enumerate(self, truncation_config=None):
        raise Exception("Not implemented")

    # returns a list of all directives and their ids, types, and values.
    # if directive_type is specified (a string "assume" "observe" "predict")
    # then it returns only directives of that type.
    def report_directives(self, directive_type=None):
        raise Exception("Not implemented")
    
    # returns the value of the given directive
    def report_value(self, directive_id):
        raise Exception("Not implemented")

    def get_continuous_inference(self):
        raise Exception("Not implemented")

    def toggle_continuous_inference(self):
        raise Exception("Not implemented")

    # FIXME: Add an estimator for Z? Perhaps by default using enumerate,
    #        or AIS?

# Delegates to an internal evaluator and kernel for most of the work.
# rejection kernel with stateless evaluator is the default
# rejection kernel with randomdb evaluator does a bit more
# XRP-MH kernel with stateless evaluator
# XRP-MH kernel with randomdb evaluator
# XRP-MH kernel with traces evaluator
#
# WARNING: Now things get hard:
# XRP-MH-envelope kernel with traces evaluator
#
# Orthogonal:
# XRP-MH-or-enumerate-for-Gibbs kernel --- crosscat style
# ??? slice kernel?
# ??? gibbs-like kernel, algorithm 8 style?
#
# Parallel:
# ??? multithreaded boltzmann style kernel (or even just multithreading for the MH-or-enumerate)
# ??? randomly scheduled, XRP-parallel kernel


class LocalRIPL(RIPL):
    """
    Builds a RIPL locally, based on the given config.

    All directive invocations are thread-safe. Implementing kernels can
    assume nothing will change under them, and callers can invoke directives
    on a single thread.
    """

    def __init__(self, state_type = "traces", kernel_type = "MH"):
        
        self.socket = socket.create_connection(('localhost', 5000))
        #self.socket.send("whoee")

        self.kernel_type = kernel_type
        if self.kernel_type != "MH":
          assert self.kernel_type ==  "rejection"
          raise Exception("not implemented")

        if self.state_type == "randomdb":
          self.db = RandomDB()
          self.mem = Directives_Memory() 
          raise Exception("not implemented")
        else:
          assert self.state_type == "traces"
          self.traces = Traces(self.env)
    
        self.directive_id = -1
          
        print "Constructing RIPL: " + str((state_type, kernel_type))

    def get_new_directive_id(self):
        self.directive_id += 1
        return self.directive_id

    def assume(self, name_str, expr_lst):
        print "assuming", name_str, "to be", expr_lst
        val = self.traces.assume(name_str, expr_lst)
        return (self.get_new_directive_id(), val)

    def observe(self, expr_lst, literal_val):
        print "observing", expr_lst, "to be", literal_val
        self.traces.observe(expr_lst, literal_val)
        return self.get_new_directive_id()

    def predict(self, expr_lst):
        print "predicting", expr_lst
        raise Exception("not implemented")
        #val = 
        #return (d_id, val)
        
##        prediction = {}
##        prediction["d_id"] = d_id
##        prediction["type"] = "predict"
##        prediction["expr_lst"] = expr_lst
##        prediction["val"] = datatypes.externalize(val)
##        self.predicts[d_id] = prediction

    def forget(self, directive_id):
        print "forgetting", directive_id
        raise Exception("not implemented")

    def clear(self):
        print "CLEAR"
        raise Exception("not implemented")

    def logscore(self, directive_id=None):
        raise Exception("not implemented")

    def infer(self, infer_config=None):
        print "INFER"
        raise Exception("not implemented")

##    # FIXME: support RIPL/engine parameters in a standardized way
    def toggle_continuous_inference(self):
        pass
##        if self.continuous_inference:
##            self.set_continuous_inference(False)
##        else:
##            self.set_continuous_inference(True)
##
    def get_continuous_inference(self):
        pass
##        return self.continuous_inference
##
    def set_continuous_inference(self, enable=True):
        pass
##        if self.continuous_inference == enable:
##            # no change needed
##            return
##        else:
##            self.continuous_inference = enable
##            if enable:
##                # start a thread
##                self.infer_thread = ContinuousInferenceThread(self)
##                self.infer_thread.start()
##                pass
##            else:
##                # kill the thread, and wait until this operation succeeds
##                if self.infer_thread is None:
##                    return
##                self.infer_thread.stop()
##                self.infer_thread.join()
##                self.infer_thread = None
##
    def enumerate(self, truncation_config=None):
        pass
##        raise Exception("Not implemented yet")
##        
    def report_value(self, directive_id):
        pass
##        self.directives_lock.acquire()
##        val = None
##        if directive_id in self.predicts:
##            val = self.predicts[directive_id]["val"]
##        elif directive_id in self.observes:
##            val =  self.observes[directive_id]["literal_val"]
##        elif directive_id in self.assumes:
##            val = self.assumes[directive_id]["val"]
##        else:
##            self.directives_lock.release()
##            raise Exception("invalid directive_id: " + str(directive_id))
##        self.directives_lock.release()
##        return val
##
    def report_directives(self, directive_type=None):
        pass
##        out = {}
##        self.directives_lock.acquire()
##        if directive_type == "assume":
##            out.update(self.assumes)
##        elif directive_type == "observe":
##            out.update(self.observes)
##        elif directive_type == "predict":
##            out.update(self.predicts)
##        else:
##            out.update(self.assumes)
##            out.update(self.observes)
##            out.update(self.predicts)
##
##        self.directives_lock.release()
##        return out

class LocalRIPL(RIPL):
    """
    Builds a RIPL locally, based on the given config.

    All directive invocations are thread-safe. Implementing kernels can
    assume nothing will change under them, and callers can invoke directives
    on a single thread.
    """

    def __init__(self, state_type = "traces", kernel_type = "MH"):
        self.state_type = state_type
        self.env = Environment()

        self.kernel_type = kernel_type
        if self.kernel_type != "MH":
          assert self.kernel_type ==  "rejection"
          raise Exception("not implemented")

        if self.state_type == "randomdb":
          self.db = RandomDB()
          self.mem = Directives_Memory() 
          raise Exception("not implemented")
        else:
          assert self.state_type == "traces"
          self.traces = Traces(self.env)
    
        self.directive_id = -1
        sys.setrecursionlimit(10000)
          
        print "Constructing RIPL: " + str((state_type, kernel_type))

    def get_new_directive_id(self):
        self.directive_id += 1
        return self.directive_id

    def assume(self, name_str, expr_lst):
        print "assuming", name_str, "to be", expr_lst
        val = self.traces.assume(name_str, expr_lst)
        return (self.get_new_directive_id(), val)

    def observe(self, expr_lst, literal_val):
        print "observing", expr_lst, "to be", literal_val
        self.traces.observe(expr_lst, literal_val)
        return self.get_new_directive_id()

    def predict(self, expr_lst):
        print "predicting", expr_lst
        raise Exception("not implemented")
        #val = 
        #return (d_id, val)
        
##        prediction = {}
##        prediction["d_id"] = d_id
##        prediction["type"] = "predict"
##        prediction["expr_lst"] = expr_lst
##        prediction["val"] = datatypes.externalize(val)
##        self.predicts[d_id] = prediction

    def forget(self, directive_id):
        print "forgetting", directive_id
        raise Exception("not implemented")

    def clear(self):
        print "CLEAR"
        raise Exception("not implemented")

    def logscore(self, directive_id=None):
        raise Exception("not implemented")

    def infer(self, infer_config=None):
        print "INFER"
        raise Exception("not implemented")

##    # FIXME: support RIPL/engine parameters in a standardized way
    def toggle_continuous_inference(self):
        pass
##        if self.continuous_inference:
##            self.set_continuous_inference(False)
##        else:
##            self.set_continuous_inference(True)
##
    def get_continuous_inference(self):
        pass
##        return self.continuous_inference
##
    def set_continuous_inference(self, enable=True):
        pass
##        if self.continuous_inference == enable:
##            # no change needed
##            return
##        else:
##            self.continuous_inference = enable
##            if enable:
##                # start a thread
##                self.infer_thread = ContinuousInferenceThread(self)
##                self.infer_thread.start()
##                pass
##            else:
##                # kill the thread, and wait until this operation succeeds
##                if self.infer_thread is None:
##                    return
##                self.infer_thread.stop()
##                self.infer_thread.join()
##                self.infer_thread = None
##
    def enumerate(self, truncation_config=None):
        pass
##        raise Exception("Not implemented yet")
##        
    def report_value(self, directive_id):
        pass
##        self.directives_lock.acquire()
##        val = None
##        if directive_id in self.predicts:
##            val = self.predicts[directive_id]["val"]
##        elif directive_id in self.observes:
##            val =  self.observes[directive_id]["literal_val"]
##        elif directive_id in self.assumes:
##            val = self.assumes[directive_id]["val"]
##        else:
##            self.directives_lock.release()
##            raise Exception("invalid directive_id: " + str(directive_id))
##        self.directives_lock.release()
##        return val
##
    def report_directives(self, directive_type=None):
        pass
##        out = {}
##        self.directives_lock.acquire()
##        if directive_type == "assume":
##            out.update(self.assumes)
##        elif directive_type == "observe":
##            out.update(self.observes)
##        elif directive_type == "predict":
##            out.update(self.predicts)
##        else:
##            out.update(self.assumes)
##            out.update(self.observes)
##            out.update(self.predicts)
##
##        self.directives_lock.release()
##        return out
##
##class ContinuousInferenceThread(threading.Thread):
##    def __init__(self, ripl):
##        threading.Thread.__init__(self)
##        self.ripl = ripl
##        self._stop = threading.Event()
##
##    def stop(self):
##        self._stop.set()
##
##    def run(self):
##        while not self._stop.isSet():
##            self.ripl.infer()
##            time.sleep(0)
##
