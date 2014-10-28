# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''

import socket
from sys import stderr
import struct


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

class MATIPResponseException(MATIPException):
    """Base class for all exceptions that include an MATIP error code.
    """

class MATIP(object):
    '''
    classdocs
    '''

    debuglevel = 0
    file = None
    default_port = 350
    
    ver = 1
    
    def __init__(self, host='', port=0,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        '''
        Constructor
        '''
        self.timeout = timeout
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
#         if self.file is None:
#             self.file = self.sock.makefile('rb')
        try:
#             resp = self.file.readline()
            resp = self.sock.recv(4096)
        except socket.error as e:
            self.close()
            raise MATIPServerDisconnected("Connection unexpectedly closed: "
                                          + str(e))
        if resp == '':
            self.close()
            raise MATIPServerDisconnected("Connection unexpectedly closed")
        if self.debuglevel > 0:
            print>>stderr, 'reply:', repr(resp)
        return resp
            
    
    def createPacket(self, version, cmd, content):
        msg = chr(version)
        msg += chr(cmd)
        msg += struct.pack("!H", len(content)+4)
        msg += content
        return msg
                
    def getSessionOpenPacket(self, cd, styp, mpx, hdr, pres, h1, h2, ascus=[]):
        '''
        get the session open message
        
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |0|0|0|0|0| Ver |1|1 1 1 1 1 1 0|            length             |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |0 0|0 1|0| CD  | STYP  |0 0 0 0| RFU           |MPX|HDR| PRES. |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |       H1      |      H2       |              RFU              |
        |-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |    Reserved   |              RFU              |  Nbr of ASCUs |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        | Nbr of ASCUs  |     ASCU list (opt)                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        
        CD
        This field specifies the Coding
        000 : 5 bits (padded baudot)
        010 : 6 bits (IPARS)
        100 : 7 bits (ASCII)
        110 : 8 bits (EBCDIC)
        xx1 : R.F.U
        
        STYP
        This is the traffic subtype (type being TYPE A).
        0001 : TYPE A Conversational
        
        MPX
        This flag specifies the multiplexing used within the TCP session.
        Possible values are:
        00 : Group of ASCU with 4 bytes identification per ASCU (H1H2A1A2)
        01 : Group of ASCUs with 2 bytes identification per ASCU (A1A2)
        10 : single ASCU inside the TCP session.
        
        HDR
        This field specifies which part of the airline’s specific address is
        placed ahead of the message texts transmitted over the session.
        Possible values are:
        00 : ASCU header = H1+H2+A1+A2
        01 : ASCU Header = A1+A2
        10 : No Header
        11 : Not used
        The MPX and HDR must be coherent. When ASCUs are multiplexed, the data
        must contain the ASCU identification. The table below summarizes the
        allowed combinations:
        +-----------------------+
        | MPX |  00 |  01 |  10 |
        +-----------------------+
        | HDR |                 |
        | 00  |  Y  |  Y  |  Y  |
        | 01  |  N  |  Y  |  Y  |
        | 10  |  N  |  N  |  Y  |
        +-----------------------+
        
        PRES
        This field indicates the presentation format
        0001 : P1024B presentation
        0010 : P1024C presentation
        0011 : 3270 presentation
        
        H1 H2
        These fields can logically identify the session if MPX is not equal to
        00. When this field is not used, it must be set to 0. If used in
        session (MPX <> 0) with HDR=00, H1H2 in data packet must have the same
        value as set in SO command.
        
        Nbr of ASCUs
        Nbr_of_ASCUs field is mandatory and gives the number of ASCUs per
        session. A 0 (zero) value means unknown. In this case the ASCU list is
        not present in the ‘Open Session’ command and must be sent by the
        other end in the ‘Open Confirm’ command.
        
        ASCU LIST
        Contains the list of identifier for each ASCU. If MPX=00 it has a
        length of four bytes (H1H2A1A2) for each ASCU, otherwise it is two
        bytes (A1A2).        
        '''
        content = chr(1<<4 | cd)
        content += chr(styp<<4)
        content += chr(0) # RFU
        content += chr(mpx<<6 | hdr<<4 | pres)
        content += chr(h1)
        content += chr(h2)
        content += ''.ljust(2, chr(0)) # RFU
        content += chr(0) # Reserved
        content += ''.ljust(2, chr(0)) # RFU
        content += struct.pack("!H", len(ascus))
        
        if mpx == 0:
            fmt = "4B"  # 4个字节(H1H2A1A2)
        else:
            fmt = "2B"  # 2个字节(A1A2)
        for ascu in ascus:
            content += struct.pack(fmt, *ascu)
    
        return self.createPacket(self.ver, 0xFE, content)
    
    def getDataPacket(self, ascu, data):
        content = ascu[:3]+chr(1)+ascu[3:]
        content += chr(0x70)
        content += data
        content += chr(0x3)
        return self.createPacket(self.ver, 0, content)
            
    def close(self):
        if self.file:
            self.file.close()
        self.file = None
        if self.sock:
            self.sock.close()
        self.sock = None
        
    
if __name__ == "__main__":
    import ConfigParser
    import codecs    
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open('config.cgi', 'r', 'utf-8-sig'))
    
    server = config.get("eterm", "server")
    port = config.getint("eterm", "port")
    username = config.get("eterm", "username")
    password = config.get("eterm", "password")
    
    el = MATIP()    
    el.set_debuglevel(1) 
    el.connect(server, port)
    
    