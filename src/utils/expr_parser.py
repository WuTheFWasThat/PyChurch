from engine.expressions import *

def parse_token(s, i = 0):
    delim = ['(', ')', '[', ']', ',']
    while s[i] == ' ':
      i += 1
      if i == len(s):
        return ('', i)
    c = s[i]
    if c in delim:
      return (c, i + 1)
    else:
      j = i + 1
      d = s[j]
      while (d not in delim) and (d != ' '):
        j += 1
        d = s[j]
      return (s[i:j], j)

##def parse_expression_list(s, i):
##    expr_list = []
##    (token, i) = parse_token(s, i)
##    assert token == '['
##    while token != ']':
##        assert token == '[' or token == ','
##        (expression, i) = parse_expression(s, i)
##        expr_list.append(expression)
##        (token, i) = parse_token(s, i)
##    assert token == ']'
##    return (expr_list, i)

def parse_expr_list(s, i):
    (token, j) = parse_token(s, i)
    expr_list = []
    while token != ')':
      (expr, i) = parse_expression(s, i)
      expr_list.append(expr)
      (token, j) = parse_token(s, i)
    return (expr_list, i)

def parse_if(s, i):
    (cond_expr, i) = parse_expression(s, i)
    (true_expr, i) = parse_expression(s, i)
    (false_expr, i) = parse_expression(s, i)
    expr = ifelse(cond_expr, true_expr, false_expr)
    return (expr, i)

def parse_apply(s, i):
    (op_expression, i) = parse_expression(s, i)
    (expr_list, i) = parse_expr_list(s, i)
    return (apply(op_expression, expr_list), i)

def parse_lambda(s, i):
    (token, i) = parse_token(s, i)
    assert token == '('
    vars_list = []
    (token, i) = parse_token(s, i)
    while token != ')':
      vars_list.append(token)
      (token, i) = parse_token(s, i)
    assert token == ')'
    (body_expr, i) = parse_expression(s, i)
    return (function(vars_list, body_expr), i)

def parse_let(s, i):
    (token, i) = parse_token(s, i)
    assert token == '('
    letmap = []
    (token, i) = parse_token(s, i)
    while token != ')':
      assert token == '('
      (var, i) = parse_token(s, i)
      (expr, i) = parse_expression(s, i)
      letmap.append((var, expr))
      (token, i) = parse_token(s, i)
      assert token == ')'
      (token, i) = parse_token(s, i)
    assert token == ')'
    (body_expr, i) = parse_expression(s, i)
    return (let(letmap, body_expr), i)

def parse_op(s, i, operator):
    if operator == 'and':
      operator = '&'
    elif operator == 'or':
      operator = '|'
    elif operator == 'xor':
      operator = '^'
    elif operator == 'not':
      operator = '~'
    (children, i) = parse_expr_list(s, i)
    return (op(operator, children), i)
  
def parse_expression(s, i = 0):
    (token, i) = parse_token(s, i)
    if len(token) < 0:
      raise Exception("No token")
    if token == '(':
      (token, j) = parse_token(s, i)
      if token == 'if':
        (expr, i) = parse_if(s, j)
      elif token == 'lambda':
        (expr, i) = parse_lambda(s, j)
      elif token == 'let':
        (expr, i) = parse_let(s, j)
      elif token in ['+', '-', '*', '/', \
                     '&', '|', '^', '~', \
                     'and', 'or', 'xor', 'not', \
                     '=', '<', '<=', '>', '>=']:
        (expr, i) = parse_op(s, j, token)
      else:
        (expr, i) = parse_apply(s, i)
      (token, i) = parse_token(s, i)
      assert token == ')'
    else:
      try:
        intval = int(token)
        expr = int_expr(intval)
      except:
        try:
          floatval = float(token)
          expr = num_expr(floatval)
        except:
          expr = var(token)
    return (expr, i)
