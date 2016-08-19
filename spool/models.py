
from google.appengine.ext import db

class Author(db.Model):
  # key_name is the username
  created = db.DateTimeProperty(auto_now_add=True)
  fullname = db.StringProperty(multiline=False, required=False)
  uid = db.UserProperty(required=True)
  member = db.BooleanProperty(required=True, default=False)
  banned = db.BooleanProperty(required=True, default=False)
  # userpage stuffs?

class Thread(db.Model):
  # key_name is "x" + unique incrementing hex number
  created = db.DateTimeProperty(auto_now_add=True)
  creator = db.ReferenceProperty(Author, required=True)
  title = db.StringProperty(multiline=False, required=True)
  urltitle = db.StringProperty(multiline=False, required=True)
  closed = db.BooleanProperty(required=True, default=False)  # allow new comments?
  snuffed = db.BooleanProperty(default=False)  # show at all?

class Comment(db.Model):
  # parent is the thread it belongs to
  created = db.DateTimeProperty(auto_now_add=True, required=True)
  creator = db.ReferenceProperty(Author, required=True)
  originIP = db.StringProperty(multiline=False)
  bodytype = db.CategoryProperty(required=True, choices=['html']) # raw, ascii-art, code:language, video:host, image
  bodytext = db.TextProperty(required=True)
  upfront = db.BooleanProperty(default=False)  # show above the fold?
  snuffed = db.BooleanProperty(default=False)  # show at all?

