#!/usr/bin/env python3

import socket, json, select
_DEBUG=True
_PORT=7777

class SocketReader(object):
        def __init__(self, sock):
                self.sock = sock

        def close(self):
                self.send("quit")
                self.sock.shutdown(1)
                self.sock.close()

        def send(self, data):
                data = json.dumps(data).encode()
                if len(data)>65535:
                        raise ValueError
                size=int.to_bytes(len(data), 3, 'big')
                totalsent = 0
                while totalsent<3:
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
                while totalrecd<3:
                        chunk=self.sock.recv(3)
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd+=len(chunk)
                        chunks+=chunk
                size=int.from_bytes(chunks[:3], 'big')
                chunks=chunks[3:]
                totalrecd-=3
                while totalrecd<size:
                        chunk=self.sock.recv(min(2048, size-totalrecd))
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd+=len(chunk)
                        chunks+=chunk
                try:
                        return json.loads(chunks.decode().strip())
                except ValueError:
                        # Fine, YOU deal with it. Probably a plain string anyways.
                        return chunks.decode().strip()[1:-1]

nicks=[None]

def handle_msg(sock):
        sock=SocketReader(sock)
        try:
                data=sock.receive()
                if isinstance(data, str):
                        data=data.strip()
        except (ConnectionResetError, BrokenPipeError):
                data = 'quit'
        if data=='quit':
                if nicks[socks.index(sock.sock)]:
                        for x in socks[1:]:
                                if x!=sock.sock:
                                        SocketReader(x).send('leave '+nicks[socks.index(sock.sock)])
                sock.sock.shutdown(1)
                sock.sock.close()
                del nicks[socks.index(sock.sock)]
                socks.remove(sock.sock)
        elif data=='stop' and _DEBUG:
                for x in socks[1:]:
                        SocketReader(x).close()
                raise StopIteration
        elif data=='isJTetris':
                sock.send('yes')
        elif data=='nick':
                sock.send(nicks[socks.index(sock.sock)])
        elif data[:5]=='nick ':
                if data[5:15].strip()=='None' or not data[5:15].strip():
                        sock.send("BadNick")
                        return
                if data[5:15].strip() in nicks:
                        # Add some proper handling for this later
                        sock.send("NickInUse")
                        return
                for x in socks[1:]:
                        if x!=sock.sock:
                                SocketReader(x).send('join '+data[5:15].strip()+' '+str(nicks[socks.index(sock.sock)]))
                nicks[socks.index(sock.sock)]=data[5:15].strip()
        elif data=='connected' and _DEBUG:
                sock.send([x.getpeername()[0] for x in socks[1:]])
        elif data[:6]=='rsend ' and _DEBUG:
                SocketReader(socks[int(data.split(' ')[1])]).send(' '.join(data.split(' ')[2:]))
        elif data=='nicks':
                sock.send(nicks[1:])
        elif data[:6]=='rnick ' and _DEBUG:
                if data[6:16] in nicks:
                        sock.send(nicks.index(data[6:16]))
                else:
                        sock.send(None)
        elif data[:10]=='challenge ':
                if data[10:20].strip() in nicks:
                        sock.send("sent")
                        SocketReader(socks[nicks.index(data[10:20])]).send("challenged "+nicks[socks.index(sock.sock)])
                else:
                        sock.send("BadNick")
        else:
                sock.send(data)

socks=[socket.socket()]
socks[0].bind(('', _PORT))
socks[0].listen()
while True:
        rd, _, err = select.select(socks, [], socks)
        for x in rd:
                if x==socks[0]:
                        accepted = (socks[0].accept())
                        socks.append(accepted[0])
                        nicks.append(None)
                        continue
                handle_msg(x)
                        
        for x in err:
                x.close()
                socks.remove(x)
                del nicks[x]
        
