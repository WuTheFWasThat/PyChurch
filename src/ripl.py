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
