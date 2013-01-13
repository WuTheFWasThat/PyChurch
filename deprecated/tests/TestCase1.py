import client_changed
import lisp_parser # From here: http://norvig.com/lispy.html

Port = 8081
MyRIPL = client_changed.RemoteRIPL("http://ripl.pcp-project.com:" + str(Port))

# Tricky coin
MyRIPL.clear() # To delete previous sessions data.
MyRIPL.assume("is-tricky", ['bernoulli', 0.1])

# You can either write the Church code via the Python lists:
# MyRIPL.assume("head-probability", ['if', 'is-tricky', ['beta', 1.0, 1.0], 0.5])
# Or to parse it from the string:
MyRIPL.assume("head-probability", lisp_parser.parse("(if is-tricky (beta 1.0 1.0) 0.5)"))
(is_tricky, _) = MyRIPL.predict("is-tricky") # It could be done through the first ASSUME,
                                             # but we are using the PREDICT just to
                                             # check its operability.

print(client_changed.directives_to_string(MyRIPL.report_directives()))                                            
                                             
for i in range(9):
    MyRIPL.observe(['bernoulli', 'head-probability'], 'true')

print MyRIPL.report_value(is_tricky)

HowManyTimesIsTricky = 0
NumberOfSamples = 100
IntermediateMHIterations = 100

for sample_number in range(NumberOfSamples):
  MyRIPL.infer(IntermediateMHIterations, 5)
  sample = MyRIPL.report_value(is_tricky)
  print "Sample #" + str(sample_number) + " = " + str(sample)
  if sample is True:
    HowManyTimesIsTricky = HowManyTimesIsTricky + 1

print "Empirical prob.: " + str(float(HowManyTimesIsTricky) / NumberOfSamples) + " versus the theoretical =appr.= 0.850498339"
