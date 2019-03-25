#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Very simple tetris implementation
# 
# Control keys:
# Down - Drop stone faster
# Left/Right - Move stone
# Z - Rotate Stone clockwise
# X - Rotate Stone counterclockwise
# Escape - Quit game
# Enter - Pause game
#
# Have fun!

# Copyright (c) 2010 "Kevin Chabowski"<kevin@kch42.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import pygame, os, time, random

# The configuration
config = {
        'cell_size':    32,
        'maxfps':       30,
        'songs':        ("dxa1.ogg", "dxa2.ogg", "dxa3.ogg", "danger.ogg"),
        'heights':      (19, 10, 7, 3),
        'music':        True,
        'sound':        True,
        'debug':        True
}

display = pygame.display.set_mode((config['cell_size']*(20), config['cell_size']*18))
pygame.display.set_caption("Tetris DX")
tiles = [None]

tileset = pygame.image.load("tileset.png").convert()
for y in range(tileset.get_height()//8):
        for x in range(tileset.get_width()//8):
                tiles.append(pygame.transform.scale(tileset.subsurface((8*x, 8*y, 8, 8)), (config['cell_size'],config['cell_size'])))
del tileset
for x in range(7, 10):
        tiles.insert(x+3, pygame.transform.rotate(tiles[x], 90))
tiles.insert(13, pygame.Surface((config['cell_size'],config['cell_size'])))
tiles[13].fill((255,255,255))
#Uncomment this when new tiles are added
#Don't forget to delete the del statements
#del tiles[16]
#del tiles[15]
#tiles.insert(15, pygame.Surface((config['cell_size'],config['cell_size'])))
#tiles[15].fill((17, 83, 18))
#tiles.insert(16, pygame.Surface((config['cell_size'],config['cell_size'])))
#tiles[16].fill((135, 168, 123))
tiles.insert(17, pygame.Surface((config['cell_size'],config['cell_size'])))
tiles[17].fill((193, 221, 243))

bg_colors = [
(255, 240, 0  ),
(255, 45,  230),
(30,  200, 200),
(50,  155, 50 ),
(155, 155, 155),
(0,   0,   0  ),
(35,  25,  180)
]

# Define the shapes of the single parts
tetris_shapes = [
        [[5, 5, 5],
         [0, 5, 0]],
        
        [[0, 6, 6],
         [6, 6, 0]],
        
        [[3, 3, 0],
         [0, 3, 3]],
        
        [[4, 4, 4],
         [4, 0, 0]],
        
        [[1, 1, 1],
         [0, 0, 1]],
        
        [[7, 8, 8, 9]],
        
        [[2, 2],
         [2, 2]]
]

speeds = [
        800,
        717,
        633,
        550,
        467,
        383,
        300,
        216,
        133,
        100,
        83, 83, 83,
        67, 67, 67,
        50, 50, 50,
        33
]
        

def rotate_clockwise(shape, rot_center):
        if shape==tetris_shapes[6]:
                return (shape, rot_center)
        rot_center.insert(0, rot_center.pop())
        return ([ [ shape[y][x]
                        for y in range(len(shape)) ]
                for x in range(len(shape[0])-1, -1, -1) ], rot_center)

def rotate_counter(shape, rot_center):
        if shape==tetris_shapes[6]:
                return (shape, rot_center)
        rot_center.append(rot_center.pop(0))
        return ([ [ shape[y][x]
                        for y in range(len(shape)-1, -1, -1) ]
                for x in range(len(shape[0])) ], rot_center)

def check_collision(board, shape, offset):
        off_x, off_y = offset
        if not -1<off_x<10:
                return True
        for cy, row in enumerate(shape):
                for cx, cell in enumerate(row):
                        try:
                                if cell and board[ cy + off_y ][ cx + off_x ]:
                                        return True
                        except IndexError:
                                return True
        return False
        
def join_matrixes(mat1, mat2, mat2_off):
        off_x, off_y = mat2_off
        for cy, row in enumerate(mat2):
                for cx, val in enumerate(row):
                        mat1[cy+off_y-1 ][cx+off_x] += val
        return mat1

def new_board():
        board = [ [ 0 for x in range(10) ]
                        for y in range(19) ]
        board += [[ 1 for x in range(10)]]
        return board

def draw_matrix(matrix, offset, screen):
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        screen.blit(tiles[val],((off_x+x) * config['cell_size'],
                                                        (off_y+y) * config['cell_size']))

class TetrisApp(object):
        def __init__(self, off_x, off_y):
                self.width = config['cell_size']*10
                self.height = config['cell_size']*18
                self.screen = display.subsurface(pygame.Rect(off_x, off_y, self.width, self.height))
                self.off_x=off_x//config['cell_size']
                self.off_y=off_y//config['cell_size']
                play_song("dxa1.ogg")
                self.board = new_board()
                if config['debug']:
                        self.next_stone=[tetris_shapes[0]]
                else:
                        self.next_stone=[random.choice(tetris_shapes), random.choice(tetris_shapes)]
                self.new_stone()
                self.bgcolor=bg_colors[0]
                self.lines=0
                self.level=0
                self.score=0
                self.speed=speeds[0]
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                self.held={}
        
        def new_stone(self):
                self.stone=self.next_stone.pop(0)
                if config['debug']:
                        self.next_stone=[tetris_shapes[(tetris_shapes.index(self.stone)+1) % len(tetris_shapes)]]
                else:
                        self.next_stone.append(random.choice(tetris_shapes))
                        while self.next_stone[0]==self.next_stone[1]==self.stone:
                                self.next_stone[1]=random.choice(tetris_shapes)
                self.stone_x = int(10 / 2 - len(self.stone[0])/2)
                self.stone_y = 1
                self.rot_center=[0,1,1,1]
                self.dropdelay = True
                pygame.time.set_timer(pygame.USEREVENT+2, 250)
                if self.stone==tetris_shapes[5]:
                        self.rot_center[2]=0
                if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                        self.gameover = True
                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                        for x in range(5):
                                if (x % 2)==1:
                                        draw_matrix(self.stone, (self.stone_x, self.stone_y-1), self.screen)
                                else:
                                        self.screen.fill((200,0,0))
                                        draw_matrix(self.board, (0,-1), self.screen)
                                pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.4)
                        if config['music']:
                                pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(17, -1, -1):
                                draw_matrix([[4 for _ in range(10)]], (0, x), self.screen)
                                pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.02)
                        time.sleep(0.4)
                        self.screen.fill((0,0,0))
                        self.center_msg("Game Over!")
                        pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(2)

        def level_up(self):
                if self.level>29:
                        return
                play_sound("level.ogg")
                self.level+=1
                if self.level<len(speeds):
                        self.speed=speeds[self.level]
                        pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                if (self.level % 5)==0 and self.level/5<len(bg_colors)+1:
                        self.bgcolor=bg_colors[self.level//5]
        
        def center_msg(self, msg):
                for i, line in enumerate(msg.splitlines()):
                        msg_image =  pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(line, False, (255,255,255), (0,0,0))
                        msgim_center_x, msgim_center_y = msg_image.get_size()
                        msgim_center_x //= 2
                        msgim_center_y //= 2
                
                        self.screen.blit(msg_image, (
                          self.width // 2-msgim_center_x,
                          self.height // 2-msgim_center_y+i*22))
        
        def move(self, delta_x):
                if not self.gameover and not self.paused:
                        new_x = self.stone_x + delta_x
                        if new_x < 0:
                                new_x = 0
                        if new_x > 10 - len(self.stone[0]):
                                new_x = 10 - len(self.stone[0])
                        if not check_collision(self.board, self.stone,(new_x, self.stone_y)):
                                self.stone_x = new_x
        
        def drop(self, si=False):
                if not (self.gameover or self.paused or self.dropdelay):
                        self.stone_y += 1
                        if si:
                                self.score+=1
                        if check_collision(self.board,
                                           self.stone,
                                           (self.stone_x, self.stone_y)):
                                self.board = join_matrixes(
                                  self.board,
                                  self.stone,
                                  (self.stone_x, self.stone_y))
                                play_sound("drop.ogg")
                                rows=[]
                                for i in range(len(self.board[:-1])):
                                        if 0 not in self.board[i]:
                                                rows.append(i)
                                if len(rows)>0:
                                        self.lines+=len(rows)
                                        self.screen.fill(self.bgcolor)
                                        draw_matrix(self.board, (0,-1), self.screen)
                                        self.remove_rows(rows)
                                        if self.lines>10*(self.level+1):
                                                self.level_up()
                                self.new_stone()
                                if self.gameover:
                                        return
                                for x in range(len(self.board)):
                                        if self.board[x]!=[0 for x in range(10)]:
                                                height=x
                                                break
                                for x in range(len(config['heights'])-1, -1, -1):
                                        if height<config['heights'][x]:
                                                play_song(config['songs'][x])
                                                break

                                
        def remove_rows(self, rows):
                global bgoffset
                self.stone=[]
                if len(rows)>3:
                        play_sound("4lines.ogg")
                        self.score+=(self.level+1)*1200
                else:
                        if len(rows)==2:
                                self.score+=(self.level+1)*300
                        elif len(rows)==1:
                                self.score+=(self.level+1)*100
                        else:
                                self.score+=(self.level+1)*40
                        play_sound("line.ogg")
                pygame.time.set_timer(pygame.USEREVENT+3, 0)
                for x in range(16):
                        bgoffset = (bgoffset-len(rows)*1.5) % -config['cell_size']
                        self.draw()
                        for r in rows:
                                if (x//4 % 2) == 0:
                                        draw_matrix([[13 for i in range(10)]], (0, r-1), self.screen)
                        pygame.display.flip()
                        time.sleep(0.05)
                for r in rows:
                        del self.board[r]
                        self.board = [[0 for i in range(10)]] + self.board
                pygame.time.set_timer(pygame.USEREVENT+3, 100)
        
        def rotate_stone(self, direct):
                if not self.gameover and not self.paused:
                        if direct>0:
                                new_stone, center = rotate_clockwise(self.stone, self.rot_center.copy())
                        else:
                                new_stone, center = rotate_counter(self.stone, self.rot_center.copy())
                        if len(new_stone)==1:
                                for x in range(len(new_stone[0])):
                                        if new_stone[0][x]==10:
                                                if x==0:
                                                        new_stone[0][x]=7
                                                else:
                                                        new_stone[0][x]=9
                                        elif new_stone[0][x]==11:
                                                new_stone[0][x]=8
                                        elif new_stone[0][x]==12:
                                                if x==0:
                                                        new_stone[0][x]=7
                                                else:
                                                        new_stone[0][x]=9
                        elif len(new_stone[0])==1:
                                for x in range(len(new_stone)):
                                        if new_stone[x][0]==7:
                                                if x==0:
                                                        new_stone[x]=[12]
                                                else:
                                                        new_stone[x]=[10]
                                        elif new_stone[x][0]==8:
                                                new_stone[x]=[11]
                                        elif new_stone[x][0]==9:
                                                if x==0:
                                                        new_stone[x]=[12]
                                                else:
                                                        new_stone[x]=[10]
                        if not check_collision(self.board,
                                               new_stone,
                                               (self.stone_x+self.rot_center[1]-center[1], self.stone_y+self.rot_center[0]-center[0])):
                                self.stone = new_stone
                                self.stone_x+=self.rot_center[1]-center[1]
                                self.stone_y+=self.rot_center[0]-center[0]
                                self.rot_center = center
                                play_sound("rotate.ogg")
                        elif not check_collision(self.board,
                                               new_stone,
                                               (self.stone_x+self.rot_center[3]-center[3], self.stone_y+self.rot_center[2]-center[2])):
                                self.stone = new_stone
                                self.stone_x+=self.rot_center[3]-center[3]
                                self.stone_y+=self.rot_center[2]-center[2]
                                self.rot_center = center
                                play_sound("rotate.ogg")
        
        def toggle_pause(self):
                self.screen.fill((0,0,0))
                self.center_msg("Paused")
                pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                self.paused = not self.paused
                play_sound("pause.ogg")
                if not config['music']:
                        return
                if self.paused:
                        pygame.mixer.music.pause()
                else:
                        pygame.mixer.music.unpause()
        
        def quit(self, override=False):
                if self.paused or override:
                        self.gameover=True

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (config['cell_size']*10, 0))
                draw_matrix(self.next_stone[0], (self.off_x+13, self.off_y+3), display)
                if self.score>9999999:
                        self.score=9999999
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.score), False, (0,0,0)), (config['cell_size']*16.3, config['cell_size']*9.1))
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.level), False, (0,0,0)), (config['cell_size']*16.3, config['cell_size']*11.1))
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.lines), False, (0,0,0)), (config['cell_size']*16.3, config['cell_size']*13.1))
                draw_matrix([[14] for _ in range(18)], (self.off_x-1,0), display)
                draw_matrix([[14] for _ in range(18)], (10+self.off_x,0), display)
                self.screen.fill(self.bgcolor)
                draw_matrix(self.board, (0,-1), self.screen)
                draw_matrix(self.stone,(self.stone_x, self.stone_y-0.925), self.screen)
        
        def run(self):
                global bgoffset
                key_actions = {
                        'escape':       lambda:self.quit(True),
                        'left':         lambda:self.move(-1),
                        'right':        lambda:self.move(+1),
                        'down':         lambda:self.drop(True),
                        'z':            lambda:self.rotate_stone(-1),
                        'x':            lambda:self.rotate_stone(+1),
                        'return':       self.toggle_pause,
                        'space':        self.quit,
                        'y':            self.level_up
                }
                
                self.gameover = False
                self.paused = False
                
                self.UI=pygame.Surface((config['cell_size']*16, config['cell_size']*19))
                self.UI.fill((128,128,128))
                self.UI.set_colorkey((128,128,128))
                draw_matrix([[13, 13, 13, 13, 13] for _ in range(5)], (self.off_x+2, self.off_y+2), self.UI)
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+9), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Score:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+9.1)*config['cell_size']))
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+11), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Level:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+11.1)*config['cell_size']))
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+13), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Lines:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+13.1)*config['cell_size']))

                self.draw()
                fade_in(display)
                pygame.time.set_timer(pygame.USEREVENT+3, 100)
                while 1:
                        if self.gameover:
                                fade_out()
                                return
                        else:
                                if not self.paused:
                                        self.draw()
                                        pygame.display.flip()
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+1:
                                        self.drop()
                                elif event.type == pygame.USEREVENT+2:
                                        self.dropdelay=False
                                        pygame.time.set_timer(pygame.USEREVENT+2, 0)
                                elif event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.gameover=True
                                elif event.type == pygame.KEYDOWN:
                                        if pygame.key.name(event.key) in key_actions:
                                                key_actions[pygame.key.name(event.key)]()
                                        
                        dont_burn_my_cpu.tick(config['maxfps'])

sound_library={}
def play_sound(path):
        if not config['sound']:
                return
        global sound_library
        sound=sound_library.get(path)
        if sound is None:
                path.replace('/', os.sep).replace('\\', os.sep)
                sound=pygame.mixer.Sound(path)
                sound_library[path]=sound
        sound.play()

_song=None
def play_song(song):
        global _song
        if not config['music'] or _song==song:
                return
        _song=song
        pygame.mixer.music.stop()
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(-1)

def fade_out():
        pygame.time.set_timer(pygame.USEREVENT+3, 0)
        fadebg = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadebg.blit(display, (0,0))
        fadeeffect = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadeeffect.fill((255,255,255))
        for x in range(0, 257, 32):
                fadeeffect.set_alpha(min(x, 255))
                display.blit(fadebg, (0,0))
                display.blit(fadeeffect, (0,0))
                pygame.display.flip()
                dont_burn_my_cpu.tick(config['maxfps'])

def fade_in(surf, off_x=0, off_y=0):
        fadebg = surf.copy()
        fadeeffect = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadeeffect.fill((255,255,255))
        for x in range(265, 0, -24):
                fadeeffect.set_alpha(min(x, 255))
                display.blit(fadebg, (off_x,off_y))
                display.blit(fadeeffect, (0,0))
                pygame.display.flip()
                dont_burn_my_cpu.tick(config['maxfps'])
        pygame.time.set_timer(pygame.USEREVENT+3, 100)

class TetrisMenu(object):
        def __init__(self, menu, actions):
                pygame.time.set_timer(pygame.USEREVENT+3, 100)
                self.quit=False
                self.menu=menu
                self.actions=actions
                self.selected=0

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                start=9-len(self.menu)/2
                longest=0
                for x in self.menu:
                        if longest<len(x):
                                longest=len(x)
                length=9.5-(longest/4)
                for x in range(len(self.menu)):
                        draw_matrix([[13 for _ in range(longest//2+2)]], (length, start+x), display)
                        if self.selected==x:
                                draw_matrix([[17]], (length, start+x), display)
                        display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.menu[x], False, (0,0,0)), ((length+1.5)*config['cell_size'], (start+x)*config['cell_size']))

        def handle_key(self, key):
                global bgoffset
                if key=='return' or key=='z':
                        if self.actions[self.selected]=="1P":
                                fade_out()
                                TetrisApp(config['cell_size']*2, 0).run()
                                time.sleep(0.1)
                                fade_in(bgscroll, bgoffset, bgoffset)
                        elif self.actions[self.selected]=="QUIT":
                                self.quit=True
                elif key=='escape' or key=='x':
                        self.quit=True
                elif key=='up':
                        self.selected = (self.selected+1) % len(self.menu)
                elif key=='down':
                        self.selected-=1
                        if self.selected<0:
                                self.selected=len(self.menu)-1
        
        def run(self):
                global bgoffset
                while not self.quit:
                        self.draw()
                        pygame.display.flip()

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3 and not config['debug']:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.quit=True
                                elif event.type == pygame.KEYDOWN:
                                        self.handle_key(pygame.key.name(event.key))

                        dont_burn_my_cpu.tick(config['maxfps'])
                fade_out()

                        

if __name__ == '__main__':
        pygame.init()
        if config['music']:
                pygame.mixer.init()
        pygame.key.set_repeat(200,25)
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        _song=None
        if config['debug']:
                for x in range(1, len(tiles)):
                        display.blit(tiles[x], (0, (x-1)*config['cell_size']))
                pygame.display.update(pygame.Rect(0, 0, config['cell_size'], len(tiles)*config['cell_size']))
                time.sleep(3)
        bgscroll=pygame.Surface((config['cell_size']*21, config['cell_size']*19))
        draw_matrix([ [ 15+((x+y)%2) for x in range(21) ] for y in range(18+config['cell_size'])
        ], (0,0), bgscroll)
        bgoffset=0
        dont_burn_my_cpu = pygame.time.Clock()
        for x in range(20):
                TetrisMenu(["x"*x, "Quit"], ["1P", "QUIT"]).run()
                if not config['debug']:
                        break
        pygame.quit()
