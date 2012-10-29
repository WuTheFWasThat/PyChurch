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

from engine.globals import Environment, Traces, RandomDB, Directives_Memory
import sys

##import evaluators
##import datatypes
##import kernels
##import xrps
##import threading
##import time

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
    
        sys.setrecursionlimit(10000)
    
          
        print "Constructing RIPL: " + str((state_type, kernel_type))

    def assume(self, name_str, expr_lst):
        print "assuming", name_str, "to be", expr_lst
##        #name_str = util.filter_data(name_str)
##        #expr_lst = util.filter_data(expr_lst)
##
##        self.directives_lock.acquire()
##
##        d_id = self.get_new_directive_id()
##
##        val = self.evaluator.eval([d_id], expr_lst, self.global_env)
##        self.global_env.bind(name_str, val)
##
##        # create a new record and store it
##        assumption = {}
##        assumption["d_id"] = d_id
##        assumption["type"] = "assume"
##        assumption["val"] = datatypes.externalize(val)
##        assumption["name_str"] = name_str
##        assumption["expr_lst"] = expr_lst
##        self.assumes[d_id] = assumption
##
##        self.directives_lock.release()
##
##        return (d_id, assumption["val"])
##
    def observe(self, expr_lst, literal_val):
        print "observing", expr_lst, "to be", literal_val
##        #expr_lst = util.filter_data(expr_lst)
##        #literal_val = util.filter_data(literal_val)
##
##        self.directives_lock.acquire()
##
##        d_id = self.get_new_directive_id()
##
##        val = self.evaluator.eval([d_id], expr_lst, self.global_env)
##        constraint_success = self.evaluator.constrain([d_id], literal_val)
##
##        # we might fail, because there isn't outermost randomness, or there
##        # is, but no way to exploit it. if this is the case, then we need
##        # to reject, rerunning directives from the beginning. 
##        #
##        # Note that this is independent of the structure of inference:
##        # even with an MH engine, this can be the case. It can also
##        # result in an infinite loop --- if the observes are actually
##        # unsatisfiable (e.g. because there is no outer randomness).
##        #
##        # FIXME: Do we set a bound on the number of attempts? Perhaps keyed
##        #        to the maximum tolerable surprisal to be handled by
##        #        rejection?
##
##        rejected = False
##        count = 0
##        while not constraint_success:
##            count += 1
##            if count % 10 == 0 and count > 0:
##                print "-- " + str(count) + " rejections"
##
##            # repeat all the assumes so far, replaying them
##            for assumption in self.assumes.values():
##                a_d_id = assumption["d_id"]
##                a_name_str = assumption["name_str"]
##                a_expr_lst = assumption["expr_lst"]
##
##                # unevaluate the old stuff
##                self.evaluator.uneval([a_d_id])
##                self.global_env.unbind(a_name_str)
##
##                # evaluate the new stuff
##                a_val = self.evaluator.eval([a_d_id], a_expr_lst, self.global_env)
##                #print str([a_d_id]) + " --- [ASSUME " + str(a_name_str) + " " + str(a_expr_lst) + "] : " + str(a_val)
##
##                # bind the results
##                self.global_env.bind(a_name_str, a_val)
##                assumption["val"] = datatypes.externalize(a_val)
##
##            # repeat all the pre-existing observes
##            failure = False
##            for observation in self.observes.values():
##                if failure:
##                    # some observe failed, so skip this observation.
##                    # FIXME: Can we use "break" to avoid O(#observes)
##                    #        cost here?
##                    continue
##
##                o_d_id = observation["d_id"]
##                o_expr_lst = observation["expr_lst"]
##                o_literal_val = observation["literal_val"]
##
##                # unevaluate the old constrained expression
##                self.evaluator.uneval([o_d_id])
##
##                # evaluate the new expression (to be constrained)
##                o_val = self.evaluator.eval([o_d_id], o_expr_lst, self.global_env)
##                # FIXME: Thread through debugging/verbosity levels, using
##                #        a coherent (pref standard) Python logging framework
##                #print str([o_d_id]) + " --- [OBSERVE " + str(o_expr_lst) + " " + str(o_literal_val) + "] --- " + str(o_val)
##
##                # attempt to the constraint from this old observe
##                if not self.evaluator.constrain([o_d_id], o_literal_val):
##                    # short-circuit if this constraint fails, retrying
##                    # all the assumes, and recording the fact that predictions
##                    # might need to change
##                    rejected = True
##                    failure = True
##            
##            # now either all the previous observes were handled correctly,
##            # or we failed on one of them.
##            if not failure:
##                # the previous observes succeded, so we can try to add
##                # the new observe (evaling and enforcing the constraint)
##                val = self.evaluator.eval([d_id], expr_lst, self.global_env)
##                
##                # FIXME debug
##                #print str([d_id]) + " --- triggering [OBSERVE " + str(expr_lst) + " " + str(literal_val) + "] --- " + str(val)
##
##                constraint_success = self.evaluator.constrain([d_id], literal_val)
##                if not constraint_success:
##                    rejected = True
##
##        # we succeded in finding a world consistent with this new observation.
##        # proceed to record this directive in the RIPL!
##        observation = {}
##        observation["d_id"] = d_id
##        observation["type"] = "observe"
##        observation["expr_lst"] = expr_lst
##        observation["literal_val"] = literal_val
##        self.observes[d_id] = observation
##
##        # now we can request new values for the predictions. 
##        #
##        # if we never rejected, then we never unevaled and revaled
##        # anything that can totally invalidate the old predictions (by
##        # (partial) exchangeability of the program). so we don't need
##        # to do anything. (note that this means that for an interative
##        # engine, i.e. a non-rejection based kernel or a non-stateless
##        # evaluator, INFER is needed any new OBSERVE to move the distribution
##        # more in line with the implied change in the conditioning.)
##        #
##        # if we did reject, things were invalidated, so we better re-predict.
##        if rejected:
##            for prediction in self.predicts.values():
##                p_d_id = prediction["d_id"]
##                p_expr_lst = prediction["expr_lst"]
##
##                # remove the old prediction
##                self.evaluator.uneval([p_d_id])
##
##                p_new_val = self.evaluator.eval([p_d_id], p_expr_lst, self.global_env)
##                
##                prediction["val"] = datatypes.externalize(p_new_val)
##
##        self.directives_lock.release()
##
##        return d_id
##
    def predict(self, expr_lst):
          print "predicting", expr_lst
##        #expr_lst = util.filter_data(expr_lst)
##
##        self.directives_lock.acquire()
##
##        d_id = self.get_new_directive_id()
##
##        val = self.evaluator.eval([d_id], expr_lst, self.global_env)
##
##        prediction = {}
##        prediction["d_id"] = d_id
##        prediction["type"] = "predict"
##        prediction["expr_lst"] = expr_lst
##        prediction["val"] = datatypes.externalize(val)
##        self.predicts[d_id] = prediction
##
##        self.directives_lock.release()
##
##        return (d_id, prediction["val"])
##
    def forget(self, directive_id):
          print "forgetting", directive_id
##        self.directives_lock.acquire()
##
##        # find the directive
##        (directive_type, index) = self.directives[directive_id]
##
##        if directive_id in self.assumes:
##            raise Exception("can't forget an assumption in isolation; would need to forget them all")
##
##            # reclaim any probability consumed by the process
##            # self.evaluator.uneval([self.assumes[index]["d_id"]])
##            #
##            # remove the record of the directive
##            # del self.assumes[index]
##            # del self.directives[directive_id]
##        elif directive_id in self.observes:
##            # remove the constraint associated with the observation
##            self.evaluator.unconstrain([directive_id])
##
##            # reclaim any probability consumed by the process
##            self.evaluator.uneval([directive_id])
##            
##            # remove the record of the directive
##            del self.observes[directive_id]
##        elif directive_id in self.predicts:
##            # reclaim any probability consumed by the prediction
##            self.evaluator.uneval([directive_id])
##
##            # remove any record of the directive
##            del self.predicts[directive_id]
##        else:
##            self.directives_lock.release()
##            raise Exception("Tried to forget a non-stateless directive: " + str((directive_type, index)))
##
##        self.directives_lock.release()
##
    def clear(self):
        print "CLEAR"
##        self.directives_lock.acquire()
##
##        for prediction in self.predicts.values():
##            self.evaluator.uneval([prediction["d_id"]])
##        self.predicts.clear()
##
##        for observation in self.observes.values():
##            self.evaluator.unconstrain([observation["d_id"]])
##            self.evaluator.uneval([observation["d_id"]])
##        self.observes.clear()
##
##        for assumption in self.assumes.values():
##            self.evaluator.uneval([assumption["d_id"]])
##            self.global_env.unbind(assumption["name_str"])
##        self.assumes.clear()
##
##        self.directives_lock.release()
##
##    def logscore(self, directive_id=None):
##        self.directives_lock.acquire()
##        if directive_id is None:
##            return self.evaluator.logscore()
##        
##        if directive_id in self.predicts or directive_id in self.observes:
##            self.evaluator.logscore([directive_id])
##        else:
##            self.directives_lock.release()
##            raise Exception("Tried to request logscore for non observe/predict: " + str(directive_id))
##        self.directives_lock.release()
##
    def infer(self, infer_config=None):
        print "INFER"
##        self.directives_lock.acquire()
##        self.kernel.infer(infer_config)
##        self.directives_lock.release()
##
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
### FIXME: Move elsewhere
##class Environment:
##    def __init__(self, parent):
##        self.parent = parent
##        self.bindings = {}
##
##    def lookup(self, name):
##        if name in self.bindings:
##            return self.bindings[name]
##        elif self.parent is not None:
##            return self.parent.lookup(name)
##        else:
##            return None
##
##    def bind(self, name, val):
##        #print "====Setting " + name + " to " + str(val)
##
##        if isinstance(val, str):
##            raise Exception("how did this happen?")
##
##        self.bindings[name] = val
##
##    def unbind(self, name):
##        if name in self.bindings:
##            del self.bindings[name]
##        else:
##            raise Exception("trying to unbind an unbound symbol: " + name)
##
