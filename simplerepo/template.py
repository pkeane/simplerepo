from google.appengine.api import users
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import os

class Template():
  def __init__(self,request,template_name,template_path):
    self.template_name = template_name
    self.request = request
    self.template_path = template_path
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
    #template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates'))
    template_dirs.append(self.template_path)
    env = Environment(loader = FileSystemLoader(template_dirs))
    try:
      template = env.get_template(self.template_name)
    except TemplateNotFound:
      raise TemplateNotFound(self.template_name)
    return template.render(self.vars)
