#!/usr/bin/python
import getpass
import sys

sys.path.append("/home/pkeane/Desktop/google_appengine")
sys.path.append("/home/pkeane/Desktop/google_appengine/lib/fancy_urllib")

from google.appengine.tools import appengine_rpc

def auth_func():
    return raw_input('Username: '), getpass.getpass('Password: ')

server = appengine_rpc.HttpRpcServer('simplerepo.appspot.com', auth_func,None,'gae_login')

#Send(request_path, payload="", content_type="application/octet-stream")

url = server.Send('/collection/old_time_music/upload_url',None) #None makes it GET, otherwise method is POST

url = url.replace('https://simplerepo.appspot.com','')

data = open('redbox.jpg').read()

print "posting image"

resp = server.Send(url, payload=data, content_type="image/jpeg")

print resp
