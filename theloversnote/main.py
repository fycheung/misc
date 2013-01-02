from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import hjcode

class IndexPage(webapp.RequestHandler):
    def get(self):
        html = template.render('templates/index.html',{})
        self.response.out.write(html)

class CodeHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('hello,hello,hello')
    def post(self):
        code = self.request.get('code')
        codetype = self.request.get('codetype')
        self.response.out.write(str(code)+'+++'+str(codetype))
        
app = webapp.WSGIApplication([('/code',CodeHandler),('/.*',IndexPage)],debug=True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()
        
    
