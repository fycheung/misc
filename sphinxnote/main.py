#coding=utf-8
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import hjcode

class IndexPage(webapp.RequestHandler):
    def get(self):
        html = template.render('templates/index.html',{})
        self.response.out.write(html)

class CodeHandler(webapp.RequestHandler):
    def post(self):
        code = self.request.get('text')
        text = code.encode('utf-8')
        codetype = self.request.get('codetype')
        result = ''
        if codetype == 'encode':
            result = hjcode.encode(text)
        elif codetype == 'decode':
            result = hjcode.decode(text)
        html = template.render('templates/show.html',{'code':str(result)})
        self.response.out.write(html)
        
app = webapp.WSGIApplication([('/code',CodeHandler),('/.*',IndexPage)],debug=True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()
        
    
