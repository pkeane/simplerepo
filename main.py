#!/usr/bin/env python

import datetime
import os
import sys
import time

from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app 

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from yaro import Yaro 
from selector import Selector 

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

def rfc3339():
  return time.strftime('%Y-%m-%dT%H:%M:%S%z')

class Template():
  def __init__(self,request,template_name):
    self.template_name = template_name
    self.request = request
    self.vars = {}

  def assign(self,key,val):
    self.vars[key] = val

  def fetch(self):
    values = {
      'request': self.request,
      'user': users.GetCurrentUser(),
      'login_url': users.CreateLoginURL(self.request.uri.application_uri()),
      'logout_url': users.CreateLogoutURL(self.request.uri.server_uri() + '/'),
      'debug': self.request.get('deb'), 
      'application_name': 'SimpleRepository',
    }
    self.vars.update(values)
    template_dirs = []
    template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates'))
    env = Environment(loader = FileSystemLoader(template_dirs))
    try:
      template = env.get_template(self.template_name)
    except TemplateNotFound:
      raise TemplateNotFound(self.template_name)
    return template.render(self.vars)

def is_logged_in(req):
  user = users.get_current_user()
  if not user:
    if 'GET' == req.method:
      req.redirect(users.create_login_url(req.uri.application_uri()))
    else:
      #todo
      req.redirect(req.uri.application_uri()+'/401')

def get_index(req):
  is_logged_in(req)
  t = Template(req,'index.html')
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def get_401(req):
  req.res.status = '401 Unauthorized'
  req.res.body = 'unauthorized'
  return

def get_hello(req):
  t = Template(req,'hello.html')
  t.assign('name',req.get('name')) 
  t.assign('title','SimpleRepository') 
  req.res.body = t.fetch() 

def delete_hello(req):
  pass

def main():
  app = Selector(wrap=Yaro)  
  app.add('401', GET=get_401)  
  app.add('', GET=get_index)  
  app.add('/', GET=get_index)  
  app.add('/hello/{name}', GET=get_hello,DELETE=delete_hello)  
  run_wsgi_app(app)

if __name__ == '__main__':
  main()

#basic auth from
#http://appengine-cookbook.appspot.com/recipe/decorator-for-basic-http-authentication/

#import base64
#from google.appengine.ext.webapp import template
#...
#def basicAuth(func):
#  def callf(webappRequest, *args, **kwargs):
#    authHeader = webappRequest.request.headers.get('Authorization')
#    
#    if authHeader == None:
#      webappRequest.response.set_status(401, message="Authorization Required")
#      webappRequest.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'
#    else:
#      auth_parts = authHeader.split(' ')
#      user_pass_parts = base64.b64decode(auth_parts[1]).split(':')
#      user_arg = user_pass_parts[0]
#      pass_arg = user_pass_parts[1]
#  
#      if user_arg != "admin" or pass_arg != "foobar":
#        webappRequest.response.set_status(401, message="Authorization Required")
#        webappRequest.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'
#    
#        self.response.out.write(template.render('templates/error/401.html', {}))
#      else:
#        return func(webappRequest, *args, **kwargs)
#  
#  return callf

