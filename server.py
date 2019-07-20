#!/usr/bin/env python3

import socket, json, select
_PORT=7777

class ClientSocket(object):
        def __init__(self, sock):
                self.sock = sock
                self.nick = None
                self.challenge = None
                self.challengers = []
                self.game = None

        def close(self):
                self.send("quit")
                self.sock.shutdown(1)
                self.sock.close()

        def send(self, data):
                data = json.dumps(data).encode()
                if len(data)>16777215:
                        raise ValueError
                size=int.to_bytes(len(data), 3, 'big')
                totalsent = 0
                while totalsent<3:
                        sent=self.sock.send(size[totalsent:])
                        if not sent:
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
                        chunk = self.sock.recv(3)
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd += len(chunk)
                        chunks += chunk
                size = int.from_bytes(chunks[:3], 'big')
                chunks = chunks[3:]
                totalrecd -= 3
                while totalrecd<size:
                        chunk = self.sock.recv(min(2048, size-totalrecd))
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd += len(chunk)
                        chunks += chunk
                return json.loads(chunks.decode().strip())
        
        def readable(self):
                return bool(select.select([self.sock], [], [], 0)[0])

class P2Game(object):
        def __init__(self, p1, p2):
                self.p1 = p1
                self.p2 = p2
                self.p1wins = 0
                self.p2wins = 0
                self.p1ready = False
                self.p2ready = False

        def handle_msg(self, data, sock):
                if data=='ready':
                        if sock==self.p1:
                                self.p1ready = True
                        else:
                                self.p2ready = True
                        if self.p1ready and self.p2ready:
                                self.p1.send('openthegame')
                                self.p2.send('openthegame')
                elif data[:7]=='height ' and data[7:].isdigit():
                        if sock==self.p1:
                                self.p2.send(data)
                        else:
                                self.p1.send(data)
                elif data[:6]=='clear ' and data[6:].isdigit():
                        data = int(data[6:])
                        if sock==self.p1:
                                self.p2.send('lines '+str(data))
                        else:
                                self.p1.send('lines '+str(data))
                elif data=='gameover':
                        if sock==self.p1:
                                self.p2.send(data)
                                self.p2wins+=1
                        else:
                                self.p1.send(data)
                                self.p1wins+=1
                        self.p1ready=False
                        self.p2ready=False
                        if self.p1wins>3 or self.p2wins>3:
                                self.p1.game = None
                                self.p2.game = None
                elif data=='withdraw':
                        if sock==self.p1:
                                self.p2.send('withdraw')
                        else:
                                self.p1.send('withdraw')
                        self.p1.game=None
                        self.p2.game=None

def sock_by_nick(nick):
        for x in socks.values():
                if x.nick == nick:
                        return x
        return None

def handle_msg(sock):
        try:
                data = sock.receive()
                if isinstance(data, str):
                        data = data.strip()
        except (ConnectionResetError, BrokenPipeError):
                data = 'quit'
        print(data)
        if data == 'quit':
                if sock.nick:
                        for x in socks.values():
                                if x != sock:
                                        x.send('leave '+sock.nick)
                if sock.challenge:
                        challenged = sock.challenge
                        if challenged and (sock in challenged.challengers):
                                if sock==challenged.challengers[0]:
                                        challenged.send('recanted')
                                        if len(challenged.challengers)>1:
                                                challenged.send("challenged "+challenged.challengers[1].nick)
                                challenged.challengers.remove(sock.nick)
                for x in sock.challengers:
                        x.send("recanted")
                if sock.game:
                        sock.game.handle_msg('withdraw', sock)
                sock.sock.shutdown(1)
                sock.sock.close()
                del socks[sock.sock]
        elif data == 'isJTetris':
                sock.send('yes')
        elif data == 'nick':
                sock.send(sock.nick)
        elif data[:5] == 'nick ':
                if data[5:15].strip() == 'None' or not data[5:15].strip():
                        sock.send("BadNick")
                        return
                if sock_by_nick(data[5:15].strip()):
                        # Add some proper handling for this later
                        sock.send("NickInUse")
                        return
                for x in socks.values():
                        if x != sock:
                                x.send('join '+data[5:15].strip()+' '+str(sock.nick))
                sock.nick = data[5:15].strip()
        elif data == 'nicks':
                sock.send([x.nick for x in socks.values()])
        elif data[:10]=='challenge ':
                challenged = sock_by_nick(data[10:20].strip())
                if challenged:
                        if challenged.challenge or challenged.game:
                                sock.send("busy")
                                return
                        sock.challenge = challenged
                        sock.send("sent")
                        if not challenged.challengers:
                                challenged.send("challenged "+sock.nick)
                        challenged.challengers.append(sock)
                else:
                        sock.send("BadNick")
        elif data=='recant':
                challenged = sock.challenge
                if challenged and (sock in challenged.challengers):
                        if sock.nick==challenged.challengers[0]:
                                challenged.send('recanted')
                                if len(challenged.challengers)>1:
                                        challenged.send("challenged "+challenged.challengers[1].nick)
                        challenged.challengers.remove(sock)
                sock.challenge = None
                sock.send("rcsent")
        elif data=='reject':
                challenger = sock.challengers[0]
                if challenger:
                        challenger.send("rejected")
                        challenger.challenge = None
                sock.send("rjsent")
                sock.challengers.pop(0)
                if sock.challengers:
                        sock.send("challenged "+sock.challengers[0].nick)
        elif data=='accept':
                challenger = sock.challengers[0]
                if challenger:
                        challenger.send("accepted")
                        challenger.challenge = None
                        challenger.game = P2Game(challenger, sock)
                        sock.game = challenger.game
                        sock.send("acsent")
                        sock.challengers.pop(0)
                        for x in sock.challengers:
                                x.send("rejected")
                else:
                        sock.send("recanted")
        elif sock.game:
                sock.game.handle_msg(data, sock)

socks={}
listener = socket.socket()
listener.bind(('', _PORT))
listener.listen()
while True:
        rd, _, err = select.select([listener]+list(socks.keys()), [], [])
        for x in rd:
                if x == listener:
                        client = listener.accept()[0]
                        socks[client] = ClientSocket(client)
                        continue
                handle_msg(socks[x])
        
