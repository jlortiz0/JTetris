#!/usr/bin/env python3

import socket, json, select

class SocketReader(object):
        def __init__(self, sock):
                self.sock = sock

        def close(self):
                self.send("quit")
                self.sock.shutdown(1)
                self.sock.close()

        def readable(self):
                return bool(self.sock.recv(1, socket.MSG_PEEK))

        def send(self, data):
                data = json.dumps(data).encode()
                if len(data)>65535:
                        raise ValueError
                size=int.to_bytes(len(data), 2, 'big')
                totalsent = 0
                while totalsent<2:
                        sent=self.sock.send(size[totalsent:])
                        if sent==0:
                                raise BrokenPipeError
                        totalsent+=sent
                totalsent = 0
                size=len(data)
                while totalsent<size:
                        sent=self.sock.send(data[totalsent:])
                        if not sent:
                                raise BrokenPipeError
                        totalsent+=sent

        def receive(self):
                chunks=bytes()
                totalrecd=0
                while totalrecd<2:
                        chunk=self.sock.recv(2)
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd+=len(chunk)
                        chunks+=chunk
                size=int.from_bytes(chunks[:2], 'big')
                chunks=chunks[2:]
                totalrecd-=2
                while totalrecd<size:
                        chunk=self.sock.recv(2048)
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd+=len(chunk)
                        chunks+=chunk
                return json.loads(chunks.decode())

def handle_msg(sock):
        sock=SocketReader(sock)
        data=sock.receive()
        if data=='quit':
                sock.close()
                socks.remove(sock)
        elif data=='stop':
                for x in socks:
                        x.close()
                raise StopIteration
        else:
                sock.send(data)

socks=[socket.socket()]
socks[0].bind(('', 7777))
socks[0].listen()
while True:
        rd, _, err = select.select(socks, [], socks)
        for x in rd:
                if x==socks[0]:
                        accepted = (socks[0].accept())
                        accepted[0].setblocking(False)
                        socks.append(accepted[0])
                        continue
                handle_msg(x)
                        
        for x in err:
                x.close()
                sockets.remove(x)
        
