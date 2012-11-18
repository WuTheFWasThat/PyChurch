def table_to_string(table, headers = []):
  if len(table) == 0:
    return ""
  n = len(table[0])
  if headers == []:
    max_lens = [0] * n
  else:
    max_lens = []
    for header in headers:
      max_lens.append(len(header))
  for row in table:
    for i in range(n):
      if len(row[i]) > max_lens[i]:
        max_lens[i] = len(row[i])

  total_len = 3 * n + 1
  for i in range(n):
    total_len += max_lens[i]

  string = '-' * total_len 
  string += '\n'
  if headers != []:
    string += '| '
    for i in range(n):
      string += headers[i]
      string += ' ' * (max_lens[i] - len(headers[i]))
      string += ' | '
    string += '\n'
    string += '-' * total_len 
    string += '\n'
  for row in table:
    string += '| '
    for i in range(n):
      string += row[i]
      string += ' ' * (max_lens[i] - len(row[i]))
      string += ' | '
    string += '\n'
  string += '-' * total_len 
  return string
