
from google.appengine.api import memcache
from settings import *
from models import *


def before(upperB):
  beforeQ.bind(upperB)
  return beforeQ.get()
beforeQ = db.GqlQuery("""SELECT * FROM Thread
                           WHERE created < :1
                           ORDER BY created DESC""")

def after(lowerB):
  afterQ.bind(lowerB)
  return afterQ.get()
afterQ = db.GqlQuery("""SELECT * FROM Thread
                          WHERE created >= :1
                          ORDER BY created""")

def threads(lowerB, upperB, asc=False):
  tquery = threadsQasc if asc else threadsQdesc
  tquery.bind(lowerB, upperB)
  return [(tid,comments(tid)) for tid in tquery.fetch(1000)]
threadsQasc = db.GqlQuery("""SELECT * FROM Thread
                               WHERE created >= :1 AND created < :2
                               ORDER BY created""")
threadsQdesc= db.GqlQuery("""SELECT * FROM Thread
                               WHERE created >= :1 AND created < :2
                               ORDER BY created DESC""")


def comments(tid):
  key = str(tid.key())
  data = memcache.get(key)
  if data:
    return data
  else:
    commentsQ.bind(tid)
    data = commentsQ.fetch(1000)
    memcache.set(key, data)
    return data
commentsQ = db.GqlQuery("""SELECT * FROM Comment
                             WHERE ANCESTOR IS :1
                             ORDER BY created""")

def clear_memcache(tid):
  """Clear caches when adding a comment to a thread."""
  key = str(tid.key())
  while not memcache.delete(key):
    pass
  while not memcache.delete(Settings.urlbase+"atom.xml"):
    pass
  while not memcache.delete("LM%satom.xml" % Settings.urlbase):
    pass

def freshthreads():
  """A list of recently commented-in threads suitable for use in an Atom feed"""
  newcomments = newcommentsQ.fetch(100)
  threads = []
  added = []
  for c in newcomments:
    if len(threads) != Settings.atomlimit:
      if (len(threads) == 0) or c.parent().key() not in added:
        threads.append( (c.parent(), c.created, c.creator.key().name()) )
        added.append( c.parent().key() )
  """# Generate a list of recent commenters for each fresh thread
    for t in threads:
      if c.thread.urltitle == t[0].urltitle:
        if len(t[2]) != 3:
          if not t[2].count(c.creator.key().name()):
            t[2].append(c.creator.key().name())"""
  return threads
newcommentsQ = db.GqlQuery("""SELECT * FROM Comment
                                ORDER BY created DESC""")

def recentthreads():
  """A list of recently posted threads suitable for use in an Atom feed"""
  newthreads = newthreadsQ.fetch(Settings.atomlimit)
  threads = []
  for t in newthreads:
    commentsQdesc.bind(t)
    c = commentsQdesc.get()
    threads.append( (t, c.created, c.creator.key().name()) )
  return threads
newthreadsQ = db.GqlQuery("""SELECT * FROM Thread
                               ORDER BY created DESC""") 
commentsQdesc = db.GqlQuery("""SELECT * FROM Comment
                                 WHERE ANCESTOR IS :1
                                 ORDER BY created DESC""")

def lastupdated():
  return newcommentsQ.get().created

def threadsmodified(lowerB, upperB):
  """Get the datetime of the most recent comment in a range of threads
     would be useful for Last-Modified headers if it were faster"""
  threadsQasc.bind(lowerB, upperB)
  def modified(tid):
    commentsQdesc.bind(tid)
    return commentsQdesc.get().created
  return max([modified(tid) for tid in threadsQasc.fetch(1000)])







  