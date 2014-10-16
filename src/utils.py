# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''
import re

def AscToHex(buf):
    strs = re.findall(r'\w{2}', buf)
    return ''.join(chr(int(strs)))

def hex_format(text):
    return [('%02x' % (ord(ch))) for ch in text]

def asc_format(text):
    res = []
    for ch in text:
        if ch >=' ' and ch <= '~' :
            res.append(' %c' % ch)
        else:
            res.append(' .')
    return res
            
def hex_print(text, colNumPerLine=16):
    hexText = hex_format(text)
    ascText = asc_format(text)
    assert(len(hexText) == len(ascText))
    res = []
    for index in range(0, len(hexText), colNumPerLine):
        res.append(' '.join(hexText[index:index+colNumPerLine]))
        res.append(' '.join(ascText[index:index+colNumPerLine]))
    print '\n'.join(res)

if __name__ == '__main__':
    pass