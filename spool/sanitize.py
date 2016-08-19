from BeautifulSoup import BeautifulSoup
from BeautifulSoup import Comment
import re
import urllib

def unquote(s):
  """http://mail.python.org/pipermail/python-dev/2008-May/079210.html"""
  s = urllib.unquote(s)
  try:
      u = s.decode("utf-8")
      try:
          s2 = s.decode("ascii")
      except UnicodeDecodeError:
          s = u #yes, s was definitely utf8, which isn't pure ascii
      else:
          if u != s:
              s = u
  except UnicodeDecodeError:
      pass  #can't have been utf8
  return s

def quote(s, safe='/'):
  """http://mail.python.org/pipermail/python-dev/2008-May/079210.html"""
  try:
      return urllib.quote(s, safe)
  except KeyError:
      return urllib.quote(s.encode("utf-8", safe))
 
def sanitize(value):
  """
  See http://www.djangosnippets.org/snippets/169/
  """
  valid_tags = 'a i b u em strong tt code s strike del small ol ul li dl dt dd center blockquote q sup sub abbr acronym blink marquee'.split()
  valid_attrs = 'href title alt'.split()
  
  soup = BeautifulSoup(value)
  for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
      comment.extract()
  
  for tag in soup.findAll(True):
      if tag.name not in valid_tags:
          tag.hidden = True
      tag.attrs = [(attr, val) for attr, val in tag.attrs
                                     if attr in valid_attrs]
  return soup.renderContents().decode('utf8')

def obliterate(value):
  soup = BeautifulSoup(value)
  for tag in soup.findAll(True):
      tag.hidden = True
  return soup.renderContents().decode('utf8')


def ampersands(string):
  """Allow terminated entities but escape wild ampersands."""
  # could be replaced with a non-capturing regex
  # could also verify that terminated entities are valid ones
  splits = string.split('&')
  if len(splits) == 1:
    return string
  result = splits[0]
  for split in splits[1:]:
    if split:
      for char in split:
        if char.isspace():
          result += "&amp;" + split; break
        elif char == ';':
          result += "&" + split; break
      else: # end of split
        result += "&amp;" + split
    else: # empty split
      result += "&amp;"
  return result

def newlines(value):
  """Turn LFs into <br>, up to two in a row, obliterating stupid CRs"""
  return re.sub("\n\n+", "\n\n", value.replace("\r","")).replace("\n", "<br>\n")

def rtl_mark(string):
  """Ensure that the right-to-left mark is terminated if used"""
  pass

def commentcheck(com):
  if com:
    com = com.strip()
    if not com:
      raise ValueError, "Your comment is whitespace!"
    elif com.count('<') != com.count('>'):
      raise ValueError, """Your comment has unbalanced angle brackets:<br>
                           Encode them as &amp;lt; and &amp;gt; for display"""
    com = sanitize(com)
    if not com:
      raise ValueError, "Your comment was obliterated by the HTML parser &mdash; only use allowed tags"
    elif len(com) > 10240:
      raise ValueError, "Your comment is way too big!"
  else:
    raise ValueError, "Your comment is blank!"
  
  return ampersands(newlines(com))
  
def urlcheck(url, length=100, thing="Thread URLs"):
  if url:
    if len(url) >= length:
      raise ValueError, thing+" can't be over %s characters" % length
    if url.count("/"):
      raise ValueError, thing+" can't contain a forward slash"
  else:
    raise ValueError, thing+" can't be blank"
  return url
  
def unamecheck(uname, length=30, thing="User names"):
  urlcheck(uname, length=length, thing=thing)
  if uname[0].isdigit():
    raise ValueError, thing+" can't start with a number"
  elif uname[0] == '_':
    raise ValueError, thing+" can't start with an underscore"
  return uname



