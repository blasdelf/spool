
from google.appengine.ext.webapp import WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
from google.appengine.api import memcache
from spool.helpers import BaseRequestHandler, datetime, users, Settings, if_modified_since, auto_memcache
from spool.sanitize import urlcheck, commentcheck, unamecheck, quote, unquote
from spool.models import *
from spool import query
from spool import date
from cgi import escape
base = Settings.urlbase

class MainPage(BaseRequestHandler):
  
  def get(self):
    now   = datetime.utcnow()
    thisM = date.thisM(now.year, now.month)
    
    threads = query.threads(thisM, now)
    while not Settings.minFP < len(threads) < Settings.maxFP and query.before(thisM):
      prevM = date.prevM(thisM.year, thisM.month)
      threads += query.threads(prevM, thisM)
      thisM = prevM
    
    # Generate earlier link
    earlier = query.before(thisM)
    if earlier:
      earlier = { 'link': "/spool/%d/%02d/" % (earlier.created.year,earlier.created.month),
                'format': datetime(earlier.created.year,earlier.created.month,1).strftime("%B %Y") }
    
    values = {'threads':threads
             ,'earlier':earlier
             }
    if threads:
      self.render("spool.html", values)
    else:
      self.error(404, s="<a href=\"%snew\">There are no threads yet</a>" % base)
  
  def post(self):
    if not self.author or not self.author.member or self.author.banned:
      self.error(403, s="%s is not allowed to post" % self.user.email())
    else:
      title   = self.request.get("title")
      url     = self.request.get("url")
      comment = self.request.get("comment")

      try:
        url = urlcheck(url)
        if not title:
          raise ValueError, "The thread title can't be blank"
        comment = commentcheck(comment)
      except ValueError, error:
        values = { 'error': error, 'form_title': escape(title),
                'form_url': escape(url), 'form_comment': escape(comment) }
        self.render("newthread.html", values, code=400)
      else:
        def increment(t):
          new = int(t.key().name()[1:], 16)+1 if t else 0
          if Thread.get_by_key_name("x%X"%new):
            raise Rollback
          else:
            new_thread = Thread(key_name="x%X"%new, urltitle=url,
                               title=escape(title), creator=self.author)
            new_thread.put()
            posting = Comment( parent=new_thread, creator=self.author,
                               originIP = self.request.remote_addr,
                               bodytype = db.Category("html"), # more later
                               bodytext = db.Text(comment), upfront = True )
            posting.put()
            query.clear_memcache(new_thread)
            self.redirect(base+new_thread.key().name()+"/"+quote(url))
            
        db.run_in_transaction(increment, Thread.all().order('-created').get())

class NewPage(BaseRequestHandler):
  
  @login_required
  def get(self):
    if not self.author:
      self.error(403, s="%s has not <a href=\"%susers\">signed up for an account yet</a>" % (self.user.email(),base))
    elif not self.author.member or self.author.banned:
      self.error(403, s="You are not allowed to post")
    else:
      self.render("newthread.html", {})


class ThreadPage(BaseRequestHandler):
  
  def get(self):
    thread_id  = Thread.get_by_key_name(self.pathindex(0))
    if not thread_id:
      self.error(404, s="Thread '%s' not found" % escape(self.request.path))
    elif thread_id.snuffed:
      self.error(410, s="Thread '%s' is gone" % escape(self.request.path))
    else:
      comments = query.comments(thread_id)
      self.render("thread.html", {'thread':thread_id, 'comments':comments,
                            'form_upfront':'checked', 'threadpage':True } )

  def post(self):
    thread_id = Thread.get_by_key_name(self.pathindex(0))
    
    if not thread_id:
      self.error(404, s="Thread not found")
    elif thread_id.closed:
      self.error(400, s="That thread is closed to new comments")
    elif not self.user:
      self.error(401, s="You need to log in")
    elif not self.author:
      self.error(401, s="%s hasn\'t registered a username" % self.user.email())
    elif self.author.banned:
      self.error(403, s="%s is banned!" % self.author.id().name())
    
    comment = self.request.get("comment")
    upfront = self.request.get("upfront")
    
    try:
      comment = commentcheck(comment)
    except ValueError, error:
      comments = query.comments(thread_id)
      form_upfront = "checked" if self.request.get("upfront") else None
      values = ({ 'thread': thread_id, 'comments' : comments, 'error': error,
            'form_comment': escape(comment), 'form_upfront': form_upfront } )
      self.render("thread.html", values, code=400)
    else:
      posting = Comment( parent   = thread_id,
                         creator  = self.author,
                         originIP = self.request.remote_addr,
                         bodytype = db.Category("html"), # more later
                         bodytext = db.Text(comment),
                         upfront  = True if upfront else False,
                         snuffed  = False )
      posting.put()
      query.clear_memcache(thread_id)
      self.redirect(self.request.uri)


class AtomFeed(BaseRequestHandler):
  
  @if_modified_since
  @auto_memcache
  def get(self):
    if Settings.atomfresh:
      threads = query.freshthreads()
      updated = threads[0][1] if threads else datetime.utcnow()
    else:
      threads = query.recentthreads()
      updated = query.lastupdated()
    
    values = { 'updated':updated, 'threads':threads }
    self.render("atom.xml", values, mod=updated)


class MonthPage(BaseRequestHandler):

  def get(self, why):
    year  = int(self.pathindex(0))
    month = int(self.pathindex(1))
    
    # Generate earlier/later links
    earlier = query.before(date.thisM(year,month))
    later   = query.after(date.nextM(year,month))
    if earlier:
      earlier = { 'link': base+"%d/%02d/" % (earlier.created.year,earlier.created.month),
      'format': datetime(earlier.created.year,earlier.created.month,1).strftime("%B %Y") }
    if later: 
      later   = { 'link': base+"%d/%02d/" % (later.created.year,later.created.month),
      'format':datetime(later.created.year,later.created.month,1).strftime("%B %Y")}
    
    threads = query.threads(thisM, nextM)
    
    values = {'threads':threads
             ,'earlier':earlier
             ,  'later':later 
             ,  'month':datetime(year,month,1).strftime("%B")
             ,   'year':year
             }
    
    if threads:
      self.render("month.html", values)
    else:
      self.render("month.html", values, code=404)

class YearPage(BaseRequestHandler):
  
  def get(self):
    year  = int(self.pathindex(0))
    
    # Generate earlier/later links
    earlier = query.before(date.thisY(year))
    later   = query.after(date.nextY(year))
    if earlier:    
       earlier = { 'link': base+"%d/" % earlier.created.year
               , 'format': str(earlier.created.year)}
    if later: 
       later   = { 'link': base+"%d/" % later.created.year
               , 'format': str(later.created.year)}
    
    threads = query.threads(thisY, nextY, asc=True)
    
    values = {'threads':threads
             ,'earlier':earlier
             ,  'later':later 
             ,   'year':year
             }
    
    if threads:
      self.render("year.html", values)
    else:
      self.render("year.html", values, code=404)

class NewUserPage(BaseRequestHandler):
  
  @login_required
  def get(self):
    if self.author:
      self.error(400, s="You already have an account, you don't need another!")
    else:
      redirect = self.request.referer
      self.render("users.html", {'nick':escape(self.user.nickname()),
                               'signup':True, 'redirect':redirect} )
  
  def post(self):
    if not self.user:
      self.error(401, s="You need to log in")
    elif self.author:
      self.error(400, s="You already have an account, you don't need another!")
    else:
      member   = True if users.is_current_user_admin() else False
      uname    = escape(self.request.get("nick"))
      fullname = escape(self.request.get("fullname"))
      redirect = self.request.get("redirect")
      
      try:
        uname = unamecheck(uname)
        if Author.get_by_key_name(uname):
          raise ValueError, "That username is taken"
      except ValueError, error:
        self.render("users.html", {'signup':True, 'error':error,'nick':uname,
                                 'fullname':fullname, 'redirect':escape(redirect)}, code=400)
      else:
        author = Author( key_name=uname, uid=self.user, member=member, fullname=fullname )
        author.put()
        site = "http://" + Settings.domain + base
        self.redirect(redirect if redirect.startswith(site + "x") else site+"users/"+quote(uname))

class UserPage(BaseRequestHandler):
  
  @login_required
  def get(self, path):
    if path:
      uname = unquote(path)
      userpage = Author.get_by_key_name(uname)
      
      if self.author and userpage and self.author.key() == userpage.key():
        self.render("users.html", {'editpage':userpage})
      elif userpage:
        self.render("users.html", {'userpage':userpage})
      else:
        self.error(404, s="%s is not anyone's username" % uname)
    else:
      allusers = Author.all().order('-created').fetch(100)
      self.render("users.html", {'allusers': allusers})

  def post(self, path):
    if path:
      uname = unquote(path)
      userpage = Author.get_by_key_name(uname)
      
      if self.author and userpage and self.author.key() == userpage.key():
          fullname = escape(self.request.get("fullname"))
          userpage.fullname = fullname
          userpage.put()
          self.redirect(base+"users/"+quote(uname))
      else:
        self.error(404, s="%s is not anyone's username" % uname)
    else:
      self.error(404)

class ErrorPage(BaseRequestHandler):
  def get(self):
    self.error(404, s="What are you looking for?")

class SearchPage(BaseRequestHandler):
  def get(self):
    query = self.request.get('q')
    self.error(501, s="You should look elsewhere for \"%s\"" % query)


def real_main():
  app = WSGIApplication( [ (base, MainPage)
                       , (base+'x[\dA-F]+/[0-9a-zA-Z%\-_\.]*', ThreadPage)
                       , (base+'atom.xml', AtomFeed)
                       , (base+'200\d/(0[1-9]|1[012])/', MonthPage)
                       , (base+'200\d/', YearPage)
                       , (base+'new', NewPage)
                       , (base+'users', NewUserPage)
                       , (base+'users/([a-zA-Z%\-\.][0-9a-zA-Z%\-_\.]*)?', UserPage)
                       , (base+'search.*', SearchPage)
                       , (base+'.*', ErrorPage)
                       ] , debug=Settings.debug)
  run_wsgi_app(app)

def profile_main():
 # This is the main function for profiling 
 # We've renamed our original main() above to real_main()
 import cProfile, pstats, StringIO
 import logging
 prof = cProfile.Profile()
 prof = prof.runctx("real_main()", globals(), locals())
 stream = StringIO.StringIO()
 stats = pstats.Stats(prof, stream=stream)
 stats.sort_stats("cumulative")  # Or cumulative
 stats.print_stats(80)  # 80 = how many to print
 # The rest is optional.
 # stats.print_callees()
 # stats.print_callers()
 logging.info("Profile data:\n%s", stream.getvalue())

if __name__ == "__main__":
  profile_main()
