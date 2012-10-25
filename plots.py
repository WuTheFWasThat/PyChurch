# PYPY wont work
import matplotlib.pyplot as plt
from tests import *
import csv

""" PLOTTING TOOLS """
""" currently unused """

# time series-like plot
def plotnames(d, names, plotname = 'plotnames'):
  for name in names:
    plot(range(niter), d[name], 'graphs/' + plotname + '-' + str(name) + '.png')

# histogram plots
def plotall(d, plotname = 'plots', nbuckets = 20):
  for name in d[0]:
    assert name in d[1]
    plt.figure()
    plt.title(plotname + '-' + str(name))
    plt.hist([d[0][name], d[1][name]], nbuckets, alpha = 0.5, histtype = 'bar', label = ['prior sample', 'follow prior'])
    plt.legend()
    plt.savefig('graphs/' + plotname + '-' + str(name) + '.png')

# time series-like plot
def plotnames(d, names, plotname = 'plotnames'):
  for name in names:
    plot(range(niter), d[name], 'graphs/' + plotname + '-' + name + '.png')

def plot(xs, ys, name = 'graphs/plot.png', minx = None, maxx = None, miny = None, maxy = None):
  if minx is None: minx = xs[0]
  if maxx is None: maxx = xs[-1]
  if miny is None: miny = min(ys)
  if maxy is None: maxy = max(ys)
  plt.axis([minx, maxx, miny, maxy])
  plt.plot(xs, ys) 
  plt.savefig(name)
#  plt.close()

def plot_dist(ys, start, end, bucketsize, name = 'graphs/plot.png', ymax = None):
  numbuckets = int(math.floor((end - start) / bucketsize))
  xs = [start + i * bucketsize for i in range(numbuckets+1)]
  plot(xs, ys, name, start, end, 0, ymax)

def plot_pdf(valuedict, start, end, bucketsize, name = 'graphs/plot.png', ymax = None):
  plot_dist(get_pdf(valuedict, start, end, bucketsize), start + (bucketsize / 2.0), end - (bucketsize / 2.0), bucketsize, name, ymax)

def plot_cdf(valuedict, start, end, bucketsize, name = 'graphs/plot.png'):
  plot_dist(get_cdf(valuedict, start, end, bucketsize), start, end, bucketsize, name, 1)

def plot_beta_cdf(a, b, bucketsize, name = 'graphs/betaplot.png'):
  plot_dist(get_beta_cdf(a, b, bucketsize), 0, 1, bucketsize, name, 1)

""" DATA PLOTS"""

class Data:
  def __init__(self, name):
    self.name = name

    self.params = []
    self.sample_avg = []
    self.sample_std = []
    self.follow_avg = []
    self.follow_std = []

  def add_direct(self, param, sample_avg, sample_std, follow_avg, follow_std):
    self.params.append(param)

    self.sample_avg.append(sample_avg)
    self.sample_std.append(sample_std)
    self.follow_avg.append(follow_avg)
    self.follow_std.append(follow_std)

  def add(self, param, a):
    self.params.append(param)

    sampletimes = a[0]['TIME']
    followtimes = a[1]['TIME']

    self.sample_avg.append(average(sampletimes))
    self.sample_std.append(standard_deviation(sampletimes))
    self.follow_avg.append(average(followtimes))
    self.follow_std.append(standard_deviation(followtimes))

  def plot_follow(self, format = 'ro'):
    #plt.errorbar(self.params, self.follow_avg, yerr=self.follow_std, fmt=format, label = self.name)
    plt.plot(self.params, self.follow_avg, format, label = self.name)

  def write_to_csv(self):
    with open('data/' + self.name + '.csv', 'wb') as csvfile:
      csvwriter = csv.writer(csvfile, delimiter = ',')
      csvwriter.writerow(['param', 'sample_avg', 'sample_std', 'follow_avg', 'follow_std'])
      for i in range(len(self.params)):
        csvwriter.writerow([str(self.params[i]), str(self.sample_avg[i]), str(self.sample_std[i]), str(self.follow_avg[i]), str(self.follow_std[i])])

  def print_as_array(self):
    return [self.params, self.sample_avg, self.sample_std, self.follow_avg, self.follow_std]

  def read_from_csv(self, name = None):
    if name is None:
      name = self.name
    with open('data/' + name + '.csv', 'rb') as csvfile:
      csvreader = csv.reader(csvfile, delimiter=',')
      csvreader.next()
      for row in csvreader:
        self.params.append(float(row[0]))
        self.sample_avg.append(float(row[1]))
        self.sample_std.append(float(row[2]))
        self.follow_avg.append(float(row[3]))
        self.follow_std.append(float(row[4]))

def write_csv(b, name):
  with open('data/' + name, 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter = ',')
    csvwriter.writerow(['param', 'sample_avg', 'sample_std', 'follow_avg', 'follow_std'])
    for i in range(len(b[0])):
      csvwriter.writerow([b[0][i], b[1][i], b[2][i], b[3][i], b[4][i]])

def make_data(run_function, params, extra_args, name):
  data = Data(name)
  for param in params:
    print param, "..."
    data.add(param, run_function(param, extra_args))
  return data.print_as_array()

def plot_db_vs_traces(run_function, params, extra_args, name):
  globals.use_traces = False
  x = make_data(run_function, params, extra_args, name + '_db')
  write_csv(x, name + '_db.csv')
  globals.use_traces = True
  y = make_data(run_function, params, extra_args, name + '_traces')
  write_csv(y, name + '_traces.csv')
  
  a = Data(name + '_db')
  a.read_from_csv(name + '_db')
  b = Data(name + '_traces')
  b.read_from_csv(name + '_traces')

  plt.figure()
  a.plot_follow('ro')
  b.plot_follow('go')
  plt.savefig('graphs/' + name + '.png')

#plot_db_vs_traces(run_topic_model_collapsed, range(1, 50), 222222, 'topic_model_collapsed_vary_docsize')
#plot_db_vs_traces(run_topic_model_half_collapsed, range(1, 20), 222222, 'topic_model_half_collapsed_ntopics')

#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_collapsed_vary_docsize')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'bayes_k10')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'bayes_n50')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_collapsed_5topics')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_collapsed_20words')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_half_collapsed_5topics')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_half_collapsed_20words')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_half_collapsed_vary_docsize')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_uncollapsed_5topics')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_uncollapsed_20words')
#plot_db_vs_traces(run_topic_model_uncollapsed, range(1, 20), 222222, 'topic_model_uncollapsed_vary_docsize')

disease_n100_c_data = Data('disease_n100_c')
disease_n100_c_data.add_direct(1, 0.000229, 0.000109, 0.000011, 0.000019)
disease_n100_c_data.add_direct(2, 0.000229, 0.000100, 0.000010, 0.000017)
disease_n100_c_data.add_direct(3, 0.000201, 0.000087, 0.000009, 0.000002)
disease_n100_c_data.add_direct(4, 0.000192, 0.000110, 0.000010, 0.000019)
disease_n100_c_data.add_direct(5, 0.000189, 0.000075, 0.000010, 0.000018)
disease_n100_c_data.add_direct(6, 0.000184, 0.000081, 0.000009, 0.000017)
disease_n100_c_data.add_direct(7, 0.000182, 0.000072, 0.000009, 0.000018)
disease_n100_c_data.add_direct(8, 0.000191, 0.000080, 0.000009, 0.000017)
disease_n100_c_data.add_direct(9, 0.000183, 0.000075, 0.000010, 0.000017)
disease_n100_c_data.add_direct(10, 0.000194, 0.000071, 0.000010, 0.000018)
disease_n100_c_data.write_to_csv()

disease_n100_pypy_data = Data('disease_n100_pypy')
disease_n100_pypy_data.add_direct(1, 0.00103071475029, 0.00463616077949, 0.000263895750046, 0.00173316044668)
disease_n100_pypy_data.add_direct(2, 0.00102333664894, 0.0043715842488, 0.000264349222183, 0.00172613439816)
disease_n100_pypy_data.add_direct(3, 0.00104003810883, 0.00440874701643, 0.000267381668091, 0.00195438239929)
disease_n100_pypy_data.add_direct(4, 0.00104621648788, 0.00466183606276, 0.000271234750748, 0.00178279726929)
disease_n100_pypy_data.add_direct(5, 0.00102550363541, 0.00433261179414, 0.00026676774025, 0.00193062859014)
disease_n100_pypy_data.add_direct(6, 0.00104925608635, 0.00450744009622, 0.000287144184113, 0.0020625615467)
disease_n100_pypy_data.add_direct(7, 0.00118299150467, 0.00443806967888, 0.000280997037888, 0.00191369049529)
disease_n100_pypy_data.add_direct(8, 0.00118412685394, 0.00469786164021, 0.000317823171616, 0.00218184101828)
disease_n100_pypy_data.add_direct(9, 0.00115386891365, 0.00497424020067, 0.000257894277573, 0.00171918612978)
disease_n100_pypy_data.add_direct(10, 0.00112620806694, 0.00439776070541, 0.000272621870041, 0.00184610667529)
disease_n100_pypy_data.write_to_csv()

disease_n100_python_data = Data('disease_n100_python')
disease_n100_python_data.add_direct(1, 0.0163365387917, 0.00357962147599, 0.000727654933929, 0.000132814773252)
disease_n100_python_data.add_direct(2, 0.0149359538555, 0.00273698047882, 0.000700296640396, 0.000101108716467)
disease_n100_python_data.add_direct(3, 0.0149048900604, 0.00256061953426, 0.000791421890259, 0.000245065662912)
disease_n100_python_data.add_direct(4, 0.014818215847, 0.00273851873829, 0.00075128030777, 0.000177124390037)
disease_n100_python_data.add_direct(5, 0.0137988705635, 0.0015242125616, 0.000864345788956, 0.000244632139188)
disease_n100_python_data.add_direct(6, 0.0176681632996, 0.00385251386803, 0.00101977658272, 0.00044599744725)
disease_n100_python_data.add_direct(7, 0.0196812143326, 0.00610344349997, 0.00175886178017, 0.000679773194537)
disease_n100_python_data.add_direct(8, 0.0144479913712, 0.00296022012546, 0.000722544908524, 0.000136498344711)
disease_n100_python_data.add_direct(9, 0.0133442070484, 0.00155859498869, 0.00101549005508, 0.000335579258465)
disease_n100_python_data.add_direct(10, 0.0136990873814, 0.00163842051467, 0.000742602348328, 0.000165510082478)
disease_n100_python_data.write_to_csv()

#plt.figure()
#disease_n100_c_data.plot_follow('go')
#disease_n100_pypy_data.plot_follow('yo')
#disease_n100_python_data.plot_follow('ro')
#plt.savefig('graphs/' + 'disease_n100' + '.png')

disease_k10_c_data = Data('disease_k10_c')
disease_k10_c_data.add_direct(10, 0.000019, 0.000006, 0.000003, 0.000002)
disease_k10_c_data.add_direct(20, 0.000034, 0.000008, 0.000004, 0.000002)
disease_k10_c_data.add_direct(30, 0.000061, 0.000035, 0.000005, 0.000005)
disease_k10_c_data.add_direct(40, 0.000073, 0.000056, 0.000008, 0.000002)
disease_k10_c_data.add_direct(50, 0.000095, 0.000057, 0.000006, 0.000002)
disease_k10_c_data.add_direct(60, 0.000092, 0.000042, 0.000006, 0.000001)
disease_k10_c_data.add_direct(70, 0.000133, 0.000066, 0.000007, 0.000002)
disease_k10_c_data.add_direct(80, 0.000152, 0.000082, 0.000008, 0.000016)
disease_k10_c_data.add_direct(90, 0.000163, 0.000069, 0.000010, 0.000003)
disease_k10_c_data.add_direct(100, 0.000201, 0.000086, 0.000010, 0.000020)
disease_k10_c_data.write_to_csv()

disease_k10_pypy_data = Data('disease_k10_pypy')
disease_k10_pypy_data.add_direct(10, 0.000603148698807, 0.00283561068724, 0.000212868690491, 0.00150132804386)
disease_k10_pypy_data.add_direct(20, 0.00061913061142, 0.00271365827779, 0.000226029634476, 0.00156124838273)
disease_k10_pypy_data.add_direct(30, 0.000821088790894, 0.0036797154039, 0.000323210716248, 0.00204207481559)
disease_k10_pypy_data.add_direct(40, 0.000980027198792, 0.00429031981749, 0.000271678447723, 0.0017979518382)
disease_k10_pypy_data.add_direct(50, 0.000818110227585, 0.00422343352232, 0.000272183418274, 0.00195084905562)
disease_k10_pypy_data.add_direct(60, 0.000800563335419, 0.00359806368422, 0.000321378231049, 0.00227914008191)
disease_k10_pypy_data.add_direct(70, 0.00129010653496, 0.00617462143553, 0.000277037143707, 0.0015104973822)
disease_k10_pypy_data.add_direct(80, 0.00114066886902, 0.00558788032763, 0.000233529090881, 0.00160126037332)
disease_k10_pypy_data.add_direct(90, 0.0010220105648, 0.00446737056294, 0.000250656366348, 0.00188999764222)
disease_k10_pypy_data.add_direct(100, 0.00104930949211, 0.00448472143756, 0.000282061815262, 0.00196681505527)
disease_k10_pypy_data.write_to_csv()

disease_k10_python_data = Data('disease_k10_python')
disease_k10_python_data.add_direct(10, 0.0021944360733, 0.000736499251198, 0.00026576590538, 0.000115637586147)
disease_k10_python_data.add_direct(20, 0.00256779980659, 0.000469677746265, 0.00024465918541, 7.47307244932e-05)
disease_k10_python_data.add_direct(30, 0.00376481723785, 0.000626834297833, 0.000297212600708, 7.14948286099e-05)
disease_k10_python_data.add_direct(40, 0.00503368806839, 0.000760533505717, 0.000365610599518, 9.18237868658e-05)
disease_k10_python_data.add_direct(50, 0.0063146443367, 0.000779939180459, 0.000423383951187, 8.83032708344e-05)
disease_k10_python_data.add_direct(60, 0.00890722346306, 0.00185689739107, 0.000473623037338, 9.23909683809e-05)
disease_k10_python_data.add_direct(70, 0.00908578014374, 0.00119884800964, 0.000544655323029, 0.000124574541586)
disease_k10_python_data.add_direct(80, 0.0112387945652, 0.00274523180287, 0.000613186120987, 0.00014722334261)
disease_k10_python_data.add_direct(90, 0.0128745806217, 0.0031156079776, 0.000725767850876, 0.000227509653651)
disease_k10_python_data.add_direct(100, 0.0148376424313, 0.00375497829901, 0.000755171060562, 0.000182275455674)
disease_k10_python_data.write_to_csv()

#plt.figure()
#disease_k10_c_data.plot_follow('go')
#disease_k10_pypy_data.plot_follow('yo')
#disease_k10_python_data.plot_follow('ro')
#plt.savefig('graphs/' + 'disease_k10' + '.png')





##seed = 222222
#hmm_data = Data('hmm')
#hmm_data.add(1, 0.00812904659178, 0.00626097044897, 0.00556190927738, 0.00566606000237)
#hmm_data.add(5, 0.0376656796874, 0.0217878799904, 0.0227006008852, 0.0203330105744)
#hmm_data.add(10, 0.0871249557746, 0.0419460226666, 0.0578157261987, 0.0489025754606)
#hmm_data.add(15, 0.170955156705, 0.0690402145124, 0.0995952314641, 0.0709816080639)
#hmm_data.add(20, 0.265828003277, 0.0945814631268, 0.183685649003, 0.123743438549)
#
#plt.figure()
#plt.axis([0, 20, 0, .3])
#plt.errorbar(hmm_data.params, hmm_data.follow_avg, yerr=hmm_data.follow_std, fmt='ro')
#plt.savefig('graphs/hmm.png')
#
##seed = 222222
#topic_model_data = Data('topic_model')
#topic_model_data.add(1, 0.0208570768959, 0.015321529704, 0.0140580143247, 0.0144142302525)
#topic_model_data.add(3,  0.0545531548597, 0.0344417732193, 0.0389357399022, 0.0456104863959)
#topic_model_data.add(5, 0.0957533187004, 0.0517844480104, 0.080251379512, 0.0897071443888)
#topic_model_data.add(7, 0.146083920657, 0.0760272612594, 0.111043426885, 0.115478403271)
#topic_model_data.add(10, 0.223726152061, 0.104072930456, 0.157427375161, 0.179218604844)
##topic_model_data.add(20, 0.705127952096, 1.22737416536, 1.50600930139, 16.883197195)
#
#plt.figure()
#plt.axis([0, 10, 0, .3])
#plt.errorbar(topic_model_data.params, topic_model_data.follow_avg, yerr=topic_model_data.follow_std, fmt='ro')
#plt.savefig('graphs/topic_model.png')
#
##seed = 222222
#mixture_model_data = Data('mixture_model')
#mixture_model_data.add(1,  0.0068850965345, 0.00599777984416, 0.00736121801071, 0.00373542363499)
#mixture_model_data.add(5,  0.021991380373, 0.0123562422511, 0.0249126335109, 0.00924054846976)
#mixture_model_data.add(10,  0.0443421121447, 0.0203322263697, 0.0543036803543, 0.0194905377211)
#mixture_model_data.add(15, 0.068116959418, 0.0293144883568, 0.0890436683382, 0.0340571510514)
#mixture_model_data.add(20,  0.099873314261, 0.0388492011943, 0.130028741958, 0.0447411981929)
#
#plt.figure()
#plt.axis([0, 20, 0, .25])
#plt.errorbar(mixture_model_data.params, mixture_model_data.follow_avg, yerr=mixture_model_data.follow_std, fmt='ro')
#plt.savefig('graphs/mixture_model.png')
#
## with 3 causes
#bayes_3_causes_db_data = Data('bayes_3_db')
#bayes_3_causes_db_data.add(1, 0.000734379543132, 0.000177585005905, 0.00052721314616, 0.00017653146747)
#bayes_3_causes_db_data.add(5, 0.00786403608421, 0.00358912872179, 0.00737285267707, 0.00397913963328)
#bayes_3_causes_db_data.add(10 , 0.0174361319723, 0.00838303159271, 0.0178328054647, 0.0147905727933)
#bayes_3_causes_db_data.add(20 , 0.0476711175604, 0.0175299141238, 0.0302452071443, 0.0347098374401)
#
#bayes_3_causes_traces_data = Data('bayes_3_traces')
#bayes_3_causes_traces_data.add(1, 0.00044543472762, 0.000115312138388, 0.000568989595753, 0.000451709013696)
#bayes_3_causes_traces_data.add(5, 0.00219723483447, 0.000633447222222, 0.000709884928101, 0.000640276027602)
#bayes_3_causes_traces_data.add(10, 0.00360253658372, 0.00060827740564, 0.00070580955227, 0.000513526146297)
#bayes_3_causes_traces_data.add(20, 0.00780386930734, 0.00180963505478, 0.000832875989043, 0.000526502711859)
#
#plt.figure()
#plt.axis([0, 20, 0, .1])
#bayes_3_causes_db_data.plot_follow('ro')
#bayes_3_causes_traces_data.plot_follow('go')
#plt.legend()
#plt.savefig('graphs/bayes_3_causes.png')
#
##    plt.hist([d[0][name], d[1][name]], nbuckets, alpha = 0.5, histtype = 'bar', label = ['prior sample', 'follow prior'])
#
## with 10 causes
#bayes_10_causes_db_data = Data('bayes_10_db')
#bayes_10_causes_db_data.add(1 , 0.000974022883635, 0.000345125723535, 0.000591423891593, 0.000203060828312)
#bayes_10_causes_db_data.add(5, 0.00780168997275, 0.00422045678023, 0.00843196034026, 0.00420959279771)
#bayes_10_causes_db_data.add(10 , 0.0160794338343, 0.0081869300303, 0.0214855182245, 0.0173238070549)
#bayes_10_causes_db_data.add(20, 0.0400891282098, 0.0121862904287, 0.0370052913156, 0.0426862678885)
#
#bayes_10_causes_traces_data = Data('bayes_10_traces')
#bayes_10_causes_traces_data.add(1, 0.000681924216355, 0.00015905581483, 0.00178079144294, 0.0019109665053)
#bayes_10_causes_traces_data.add(5, 0.00307568977405, 0.000843188642079, 0.00211389455944, 0.00270777596136)
#bayes_10_causes_traces_data.add(10, 0.00479229397598, 0.000660736569767, 0.00194291773254, 0.00217296134233)
#bayes_10_causes_traces_data.add(20, 0.01160112287, 0.00304434647465, 0.00211449092527, 0.00201714824527)
#
#plt.figure()
#plt.axis([0, 20, 0, .1])
#bayes_10_causes_db_data.plot_follow('ro')
#bayes_10_causes_traces_data.plot_follow('go')
#plt.legend()
#plt.savefig('graphs/bayes_10_causes.png')


### BAYES K10

## cloud.call(make_data, run_bayes_net, range(1, 50), 222222, 'db')
## a = cloud.result(jobID)
## write_csv(a, 'bayes_k10_db.csv')

#a = Data('bayes_k10_db')
#a.read_from_csv('bayes_k10_db')
#b = Data('bayes_k10_traces')
#b.read_from_csv('bayes_k10_traces')
#
#plt.figure()
#a.plot_follow('ro')
#b.plot_follow('go')
#plt.legend()
#plt.savefig('graphs/bayes_k10.png')

### BAYES N50

## cloud.call(make_data, run_bayes_net, range(1, 10), 222222, 'db')
## a = cloud.result(jobID)
## write_csv(a, 'bayes_n50_db.csv')

#c = Data('bayes_n50_db')
#c.read_from_csv('bayes_n50_db')
#d = Data('bayes_n50_traces')
#d.read_from_csv('bayes_n50_traces')
#
#plt.figure()
#c.plot_follow('ro')
#d.plot_follow('go')
#plt.legend()
#plt.savefig('graphs/bayes_n50.png')





#bayes_3_traces = make_data(run_bayes_net, range(1, 25), 222222, 'bayes_10_db')
#bayes_3_traces.write_csv()
#
#plt.figure()
##plt.axis([0, 20, 0, .01])
#bayes_3_traces.plot_follow('ro')
#plt.legend()
#plt.savefig('graphs/bayes_10_traces.png')

d = run_HMM(1, 222222, 1000, 100, False)
plotall(d, 'HMM1', 50)
#d = run_mixture(1, 222222, 1000, 100, False)
#plotall(d, 'mixture1', 50)
#d = run_topic_model(5, 222222, 1000, 100, False)
#plotall(d, 'topicmodel1', 50)
#d = run_bayes_net(5, 222222, 1000, 100, False)
#plotall(d, 'bayesnet1', 50)
#
#sampletimes = a[0]['TIME']
#print average(sampletimes)
#print standard_deviation(sampletimes)
#           
#followtimes = a[1]['TIME']
#print average(followtimes)
#print standard_deviation(followtimes)
#print time() - t 
#
