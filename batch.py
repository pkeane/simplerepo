#!/usr/bin/python
import getpass
import sys

sys.path.append("google_appengine")
sys.path.append("google_appengine/lib/fancy_urllib")

from google.appengine.tools import appengine_rpc

def auth_func():
    return raw_input('Username: '), getpass.getpass('Password: ')

server = appengine_rpc.HttpRpcServer('simplerepo.appspot.com', auth_func,None,'gae_login')

#Send(request_path, payload="", content_type="application/octet-stream")

print server.Send('/notes',None) #None makes it GET, otherwise method is POST
