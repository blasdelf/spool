from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app

class ErrorPage(RequestHandler):
  def get(self):
    self.response.headers.add_header("Content-Type", "text/plain")
    self.response.set_status(404)
    self.response.out.write("What are you looking for?")

app = WSGIApplication([('.*', ErrorPage)], debug=True)
def main():
  run_wsgi_app(app)
if __name__ == "__main__":
  main()
