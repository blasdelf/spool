
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app
from spool.settings import Settings

class MainPage(RequestHandler):

  def get(self):
    self.response.set_status(303) # see other
    self.response.headers.add_header("Location", Settings.urlbase)

app = WSGIApplication([('/', MainPage)])
def main():
  run_wsgi_app(app)
if __name__ == "__main__":
  main()

