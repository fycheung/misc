from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
class IndexPage(webapp.RequestHandler):
    def get(self):
        html = template.render('templates/index.html',{})
        self.response.out.write(html)
app = webapp.WSGIApplication([('/subsub',IndexPage)],debug=True)


def main():
##    run_wsgi_app(app)
    global count
    count += 1
    print 'submain',count

if __name__ == '__main__':
    main()
        
    
