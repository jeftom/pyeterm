# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''

import socket
from sys import stderr
import ConfigParser
import codecs


MATIP_PORT = 350

class MATIPException(Exception):
    '''
    Base class for all exceptions raised by this module.
    '''
    

class MATIPServerDisconnected(MATIPException):
    '''Not connected to any MATIP server.

    This exception is raised when the server unexpectedly disconnects,
    or when an attempt is made to use the SMTP instance before
    connecting it to a server.
    '''


class MATIP(object):
    '''
    classdocs
    '''

    debuglevel = 0
    file = None
    default_port = 350

    def __init__(self, host='', port=0,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        '''
        Constructor
        '''
        self.timeout = timeout
        self.esmtp_features = {}
        if host:
            self.connect(host, port)
            
        
    def set_debuglevel(self, debuglevel):
        self.debuglevel = debuglevel
        
    def _get_socket(self, host, port, timeout):
        if self.debuglevel > 0:
            print>>stderr, 'create connect:', (host, port)
        return socket.create_connection((host, port), timeout)     
        
    def connect(self, host='localhost', port=0):
        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if i >= 0:
                host, port = host[:i], host[i+1:]
                try:
                    port = int(port)
                except ValueError:
                    raise socket.error, "nonnumeric port"
        if not port:
            port = self.default_port
        if self.debuglevel > 0:
            print>>stderr, 'connect:', (host, port)
        self.sock = self._get_socket(host, port, self.timeout)
        self.getreply()
        
    def send(self, content):
        if self.debuglevel > 0:
            print>>stderr, 'send;', repr(content)
        if hasattr(self, 'sock') and self.sock:
            try:
                self.sock.sendall(content)
            except socket.error:
                self.close()
                raise MATIPServerDisconnected('Server not connected')
        else:
            raise MATIPServerDisconnected('Please run connect() first')
        
    def getreply(self):
#         resp = []
        if self.file is None:
            self.file = self.sock.makefile('rb')
        while 1:
            try:
                line = self.file.readline()
            except socket.error as e:
                self.close()
                raise MATIPServerDisconnected("Connection unexpectedly closed: "
                                              + str(e))
            if line == '':
                self.close()
                raise MATIPServerDisconnected("Connection unexpectedly closed")
            if self.debuglevel > 0:
                print>>stderr, 'reply:', repr(line)
            print line
            break
            
                
    def login(self, username, password):
        pass
    
    def close(self):
        if self.file:
            self.file.close()
        self.file = None
        if self.sock:
            self.sock.close()
        self.sock = None
        
    

if __name__ == "__main__":
    pass    
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open('config.cgi', 'r', 'utf-8-sig'))
    
    server = config.get("eterm", "server")
    port = config.getint("eterm", "port")
    username = config.get("eterm", "username")
    password = config.get("eterm", "password")
    
    el = MATIP()    
    el.set_debuglevel(1) 
    el.connect(server, port)
    
    