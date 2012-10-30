import requests
# Change 1: connecting 'simplejson'
try: # http://stackoverflow.com/questions/791561/python-2-5-json-module
    import json
except ImportError:
    import simplejson as json 

class BadRequestStatus(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
            
def CheckStatus(request_object):
    if (request_object.status_code != 200):
      raise BadRequestStatus(str('Bad status code: ' + str(request_object.status_code) + '. Return message from the engine: "' + request_object.content + '"'))
          
def directives_to_string(directives): # Change 8: added new utility.
  info = []
  info_element = [] # Better through info_element.append(...)?
  info_element.append("ID")
  info_element.append("EXPRESSION")
  info_element.append("VALUE")
  info.append(info_element)
  print(info)
  while len(directives) > 0:
    directive = directives.pop()
    info_element = [0, 0, 0]
    info_element[0] = str(directive['directive-id'])
    info_element[1] = str(directive['directive-expression'])
    if (directive['directive-type'] == 'DIRECTIVE-ASSUME' or directive['directive-type'] == 'DIRECTIVE-PREDICT'):
      info_element[2] = str(directive['value'])
    else:
      info_element[2] = "-"
    info.append(info_element)

  max_lengths = [0, 0, 0]
  for i in range(len(info)):
    for j in range(3):
      info[i][j] = ' ' + info[i][j]
      if (len(info[i][j]) > 50):
        info[i][j] = (info[i][j])[:47] + "..."
      info[i][j] = info[i][j] + ' '
      if (max_lengths[j] < len(info[i][j])):
        max_lengths[j] = len(info[i][j])

  output = ""
  for i in range(len(info)):
    if (i > 0):
      output = output + '\n'
    for j in range(3):
      output = output + info[i][j]
      for z in range(max_lengths[j] - len(info[i][j])):
        output = output + ' '
      output = output + '|'
    output = output
  return output
          
class RemoteRIPL():
    """
    uri --- the URI of the REST RIPL server to connect to
    """
    def __init__(self, uri):
        self.uri = uri
        
    def assume(self, name_str, expr_lst):
        payload = {"name_str": json.dumps(name_str),
                   "expr_lst": json.dumps(expr_lst)}
        r = requests.put(self.uri + '/assume', data=payload)
        CheckStatus(r)
        return_dict = json.loads(r.content)
        return (return_dict["d_id"], return_dict["val"])

    def observe(self, expr_lst, literal_val):
        payload = {"expr_lst": json.dumps(expr_lst),
                   "literal_val": json.dumps(literal_val)}
        r = requests.put(self.uri + '/observe', data=payload)
        CheckStatus(r)
        return json.loads(r.content)["d_id"]

    def predict(self, expr_lst):
        payload = {"expr_lst": json.dumps(expr_lst)}
        r = requests.put(self.uri + '/predict', data=payload)
        CheckStatus(r)
        return_dict = json.loads(r.content)
        return (return_dict["d_id"], return_dict["val"])
    
    def forget(self, directive_id):
        # FIXME: This REST choice interacts badly with proxies
        r = requests.delete(self.uri + '/' + str(directive_id))
        CheckStatus(r)

    def clear(self):
        # FIXME: This REST choice interacts badly with proxies
        r = requests.delete(self.uri + '/')
        CheckStatus(r)

    def logscore(self, directive_id=None):
        raise Exception("not implemented")

    def infer(self, MHiterations, threadsNumber): # Change 2: changed parameters.
        # FIXME: Define and support a proper config
        payload = {"MHiterations": MHiterations,
                   "threadsNumber": threadsNumber}
        r = requests.put(self.uri + "/infer", data=payload)
        CheckStatus(r)

    def enumerate(self, truncation_config=None):
        raise Exception("not implemented")

    def report_directives(self, directive_type=None):
        if directive_type is not None:
            raise Exception("not implemented")
        r = requests.get(self.uri + '/')
        CheckStatus(r)
        return json.loads(r.content)

    def report_value(self, directive_id):
        r = requests.get(self.uri + '/' + str(directive_id))
        CheckStatus(r)
        contents = json.loads(r.content)
        return contents["val"]

    def logscores(self): # Change 3: added new function.
        r = requests.get(self.uri + '/logscores')
        CheckStatus(r)
        contents = json.loads(r.content)
        return contents
        
    def ERPs_number(self): # Change 4: added new function.
        r = requests.get(self.uri + '/ERPs_number')
        CheckStatus(r)
        contents = json.loads(r.content)
        return contents['ERPs_number']
        
    def start_cont_infer(self, threadsNumber=1): # Change 5: added new function.
        payload = {"threadsNumber": threadsNumber}
        r = requests.put(self.uri + '/start_cont_infer', data=payload)
        CheckStatus(r)
        
    def stop_cont_infer(self): # Change 6: added new function.
        r = requests.put(self.uri + '/stop_cont_infer')
        CheckStatus(r)
        
    def cont_infer_status(self): # Change 7: added new function.
        r = requests.get(self.uri + '/cont_infer_status')
        CheckStatus(r)
        contents = json.loads(r.content)
        return contents
        