
from google.appengine.ext.webapp import template, RequestHandler, Response
from google.appengine.api import users
from google.appengine.api import memcache
from models import Author
from settings import Settings
from os import path # for loading the template
from datetime import datetime

template.register_template_library('spool.filters')
rfc1123 = "%a, %d %b %Y %H:%M:%S GMT"
rfc850  = "%A, %d-%b-%y %H:%M:%S GMT"
def parsetime(s):
  try:
    return datetime.strptime(s, rfc1123)
  except ValueError:
    try:
      return datetime.strptime(s, rfc850)
    except ValueError:
      return None

def if_modified_since(f):
  """Decorator for sending 304 Not-Modified"""
  def wrapper(self, *args):
    mod = memcache.get("LM"+self.request.path)
    if mod:
      self.response.headers.add_header('Last-Modified', mod.strftime(rfc1123))
    self.response.headers.add_header('Expires', '0')
    ims = self.request.headers.get('If-Modified-Since')
    if ims:
      ims = parsetime(ims)
      if mod and ims and mod <= ims:
        self.response.set_status(304)
      else: #bogus header
        return f(self, *args)
    else:
      return f(self, *args)
  return wrapper

def auto_memcache(f):
  """Decorator to automatically fetch/store rendered responses in the memcache"""
  def wrapper(self, *args):
    path = self.request.path
    data = memcache.get(path)
    if data:
      self.response.out.write(data)
    else:
      f(self, *args)
      memcache.set(path, self.response.out.getvalue())
  return wrapper

class BaseRequestHandler(RequestHandler):
  
  def initialize(self, request, response):
    self.request  = request
    self.response = response
    self.user     = users.get_current_user()
    if self.user:
      email = self.user.email()
      data = memcache.get(email)
      if data:
        self.author = data
      else:
        author = Author.all().filter('uid =', self.user).get()
        if author:
          self.author = author
          memcache.set(email, author)
        else:
          self.author = None
  
  def error(self, code, s=None):
    m = Response.http_status_message(code)
    s = s if s else m
    self.render("error.html", {'error':s,'errorcode':code, 'errormessage':m}, code=code)
  
  def pathindex(self,index):
    """Return the string at index in the path after the base ("/spool/" by default) is stripped out"""
    return self.request.path[len(Settings.urlbase):].split('/')[index]
  
  def render(self, template_name, tvalues, code=None, mod=None):
    
    if self.user:
      sign = {'url':users.create_logout_url(self.request.path), 'label':"Sign Out"}
    else:
      sign = {'url':users.create_login_url(self.request.path),  'label':"Sign In"}
    
    values = {
       'request': self.request,
       'user': self.user,
       'administrator': users.is_current_user_admin(),
       'sign': sign,
       'spool': Settings,
       'author': self.author,
       'urlpath': self.request.path,
       'now': datetime.utcnow(),
       'base':Settings.urlbase
    }
    values.update(tvalues)
    if code:
      self.response.set_status(code)
    
    if mod:
      mod = datetime(mod.year,mod.month,mod.day,mod.hour,mod.minute,mod.second) #strip ms
      self.response.headers.add_header('Last-Modified', mod.strftime(rfc1123))
      memcache.set("LM"+self.request.path, mod)
    
    # See AppEngine Issue #732
    # self.response.headers.add_header('Cache-Control', 'no-cache')
    self.response.headers.add_header('Expires', '0')
    
    directory = path.dirname(__file__)
    tpath = path.join(directory, path.join('templates', template_name))
    self.response.out.write(template.render(tpath, values, debug=False))
                           #debug turns off usage of template.template_cache {}


