#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

import pygame, os, time, random, sys, json, types, socket, select
from statistics import mean
from datetime import datetime

# The configuration
config = {
        'cell_size':    32,
        'songs':        ("dxa1.ogg", "dxa2.ogg", "dxa3.ogg", "danger.ogg"),
        'heights':      (19, 9, 6, 3),
        'music':        True,
        'sound':        True
}

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
        883,
        817,
        750,
        683,
        617,
        550,
        467,
        367,
        283,
        183,
        167,
        150,
        133,
        117,
        100, 100,
        67, 67,
        50
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
        return [[0 for _ in range(10)] for _ in range(19)]

def draw_matrix(matrix, offset, screen):
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        screen.blit(tiles[val],((off_x+x) * config['cell_size'],
                                                        (off_y+y) * config['cell_size']))

sound_library={}
def play_sound(path):
        if not config['sound']:
                return
        global sound_library
        sound=sound_library.get(path)
        if sound is None:
                sound=pygame.mixer.Sound("sound"+os.sep+path)
                sound_library[path]=sound
        sound.play()

_song=None
def play_song(song):
        global _song
        if not config['music'] or _song==song:
                return
        _song=song
        pygame.mixer.music.stop()
        pygame.mixer.music.load("music"+os.sep+song)
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
                dont_burn_my_cpu.tick(30)

def fade_in():
        fadebg = display.copy()
        fadeeffect = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadeeffect.fill((255,255,255))
        for x in range(265, 0, -24):
                fadeeffect.set_alpha(min(x, 255))
                display.blit(fadebg, (0,0))
                display.blit(fadeeffect, (0,0))
                pygame.display.flip()
                dont_burn_my_cpu.tick(30)
        pygame.time.set_timer(pygame.USEREVENT+3, 100)
        pygame.event.clear(pygame.KEYDOWN)

class TetrisClass(object):
        def draw(self):
                raise NotImplementedError

        def run(self):
                raise NotImplementedError

class TetrisApp(TetrisClass):
        def __init__(self, off_x, off_y, level=0):
                self.quit=False
                self.rage=False
                self.lineNums = [0,0,0,0]
                self.width = config['cell_size']*10
                self.height = config['cell_size']*18
                self.screen = display.subsurface(pygame.Rect(off_x, off_y, self.width, self.height))
                self.off_x=off_x//config['cell_size']
                self.off_y=off_y//config['cell_size']
                self.board = new_board()
                self.next_stone=[random.choice(tetris_shapes), random.choice(tetris_shapes)]
                self.new_stone()
                self.lines=0
                self.level=level
                self.bgcolor=bg_colors[self.level//5]
                self.score=0
                self.speed=speeds[self.level]
        
        def new_stone(self):
                self.stone=self.next_stone.pop(0)
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
                        self.quit = True
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
                        self.fade=[0, self.bgcolor, bg_colors[self.level//5]]
                draw_matrix([[13, 13, 13, 13]], (self.off_x+4, self.off_y+11), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.level), False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*11.1))
        
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
                if not self.quit and not self.paused:
                        new_x = self.stone_x + delta_x
                        if new_x < 0:
                                new_x = 0
                        if new_x > 10 - len(self.stone[0]):
                                new_x = 10 - len(self.stone[0])
                        if not check_collision(self.board, self.stone,(new_x, self.stone_y)):
                                self.stone_x = new_x
        
        def drop(self, si=False):
                if not (self.quit or self.paused or self.dropdelay):
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
                                for i in range(len(self.board)):
                                        if 0 not in self.board[i] and 14 not in self.board[i]:
                                                rows.append(i)
                                if len(rows)>0:
                                        self.lines+=len(rows)
                                        self.screen.fill(self.bgcolor)
                                        draw_matrix(self.board, (0,-1), self.screen)
                                        self.remove_rows(rows)
                                        if self.lines>10*(self.level+1):
                                                self.level_up()
                                self.new_stone()
                                if self.quit:
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
                self.lineNums[len(rows)-1]+=1
                draw_matrix([[13, 13, 13, 13]], (self.off_x+4, self.off_y+13), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.lines), False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*13.1))
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
                if not self.quit and not self.paused:
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
        
        def exit(self):
                if self.paused:
                        self.quit=True
                        self.rage=True

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (config['cell_size']*10, 0))
                draw_matrix(self.next_stone[0], (self.off_x+13, self.off_y+3), display)
                if self.score>9999999:
                        self.score=9999999
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.score), False, (0,0,0)), (config['cell_size']*16.3, config['cell_size']*9.1))
                draw_matrix([[14] for _ in range(18)], (self.off_x-1,0), display)
                draw_matrix([[14] for _ in range(18)], (10+self.off_x,0), display)
                self.screen.fill(self.bgcolor)
                draw_matrix(self.board, (0,-1), self.screen)
                draw_matrix(self.stone,(self.stone_x, self.stone_y-0.925), self.screen)
        
        def run(self):
                global bgoffset
                key_actions = {
                        'left':         lambda:self.move(-1),
                        'right':        lambda:self.move(+1),
                        'down':         lambda:self.drop(True),
                        'z':            lambda:self.rotate_stone(-1),
                        'x':            lambda:self.rotate_stone(+1),
                        'return':       self.toggle_pause,
                        'space':        self.exit,
                        'y':            self.level_up
                }

                self.paused = False
                self.fade=()
                
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
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.level), False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*11.1))
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("0", False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*13.1))

                self.draw()
                play_song("dxa1.ogg")
                fade_in()
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                while not self.quit:
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
                                        self.quit=True
                                elif event.type == pygame.KEYDOWN:
                                        if event.key==pygame.K_F12:
                                                now = datetime.now()
                                                pygame.image.save(display, "screenshot"+os.sep+"{}-{:02}-{:02}_{:02}-{:02}-{:02}.png".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
                                                play_sound("screenshot.ogg")
                                        elif pygame.key.name(event.key) in key_actions:
                                                key_actions[pygame.key.name(event.key)]()
                                        
                        if len(self.fade)>0:
                                self.fade[0]=self.fade[0]+1
                                self.bgcolor=[x + (((y-x)/15)*self.fade[0]) for x,y in zip(self.fade[1], self.fade[2])]
                                if self.fade[0]==15:
                                        self.bgcolor=self.fade[2]
                                        self.fade=()
                        dont_burn_my_cpu.tick(30)
                fade_out()
                pygame.time.set_timer(pygame.USEREVENT+1, 0)

class TetrisTimed(TetrisApp):
        def __init__(self, off_x, off_y, level=0, time=0, lines=0, height=0):
                super().__init__(off_x, off_y, level)
                self.count = (time>0)
                self.timer = time
                self.linec = (lines>0)
                self.linesClear=lines
                if height>0:
                        self.board=self.board[height:]+[[14 for _ in range(10)] for _ in range(height)]

        def remove_rows(self, rows):
                super().remove_rows(rows)
                if self.linec and self.linesClear-1<self.lines:
                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                        play_sound("timeup.ogg")
                        self.bgcolor=bg_colors[2]
                        self.next_stone=[[[]], [[]]]
                        self.draw()
                        pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(1)
                        if config['music']:
                                pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(17, -1, -1):
                                draw_matrix([[1 for _ in range(10)]], (0, x), self.screen)
                                pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.02)
                        time.sleep(0.4)
                        self.screen.fill((0,0,0))
                        self.center_msg("Cleared!")
                        pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(2)
                        self.quit=True

        def level_up(self):
                pass

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                if self.linec:
                        draw_matrix([[13, 13, 13, 13]], (self.off_x+4, self.off_y+13), self.UI)
                        self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(max(0, self.linesClear-self.lines)), False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*13.1))
                display.blit(self.UI, (config['cell_size']*10, 0))
                draw_matrix(self.next_stone[0], (self.off_x+13, self.off_y+3), display)
                if self.score>9999999:
                        self.score=9999999
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(str(self.score), False, (0,0,0)), (config['cell_size']*16.3, config['cell_size']*9.1))
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("{0}:{1:02}".format(self.timer//1800, self.timer//30 % 60), False, (0,0,0)), (config['cell_size']*15.7, config['cell_size']*11.1))
                draw_matrix([[14] for _ in range(18)], (self.off_x-1,0), display)
                draw_matrix([[14] for _ in range(18)], (10+self.off_x,0), display)
                self.screen.fill(self.bgcolor)
                draw_matrix(self.board, (0,-1), self.screen)
                draw_matrix(self.stone,(self.stone_x, self.stone_y-0.925), self.screen)

        def run(self):
                global bgoffset
                key_actions = {
                        'left':         lambda:self.move(-1),
                        'right':        lambda:self.move(+1),
                        'down':         lambda:self.drop(True),
                        'z':            lambda:self.rotate_stone(-1),
                        'x':            lambda:self.rotate_stone(+1),
                        'return':       self.toggle_pause,
                        'space':        self.exit,
                        'y':            self.level_up
                }

                self.paused = False
                
                self.UI=pygame.Surface((config['cell_size']*16, config['cell_size']*19))
                self.UI.fill((128,128,128))
                self.UI.set_colorkey((128,128,128))
                draw_matrix([[13, 13, 13, 13, 13] for _ in range(5)], (self.off_x+2, self.off_y+2), self.UI)
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+9), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Score:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+9.1)*config['cell_size']))
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+11), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Time:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+11.1)*config['cell_size']))
                draw_matrix([[17, 13, 13, 13, 13, 13, 13]], (self.off_x+1, self.off_y+13), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Lines:", False, (0,0,0)), ((self.off_x+1.3)*config['cell_size'], (self.off_y+13.1)*config['cell_size']))
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("0", False, (0,0,0)), (config['cell_size']*6.3, config['cell_size']*13.1))

                self.draw()
                play_song("dxa1.ogg")
                fade_in()
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                while not self.quit:
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
                                        self.quit=True
                                elif event.type == pygame.KEYDOWN:
                                        if event.key==pygame.K_F12:
                                                now = datetime.now()
                                                pygame.image.save(display, "screenshot"+os.sep+"{}-{:02}-{:02}_{:02}-{:02}-{:02}.png".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
                                                play_sound("screenshot.ogg")
                                        elif pygame.key.name(event.key) in key_actions:
                                                key_actions[pygame.key.name(event.key)]()
                                        
                        if self.count and not self.paused:
                                self.timer-=1
                                if self.timer==0:
                                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                                        play_sound("timeup.ogg")
                                        self.bgcolor=bg_colors[2]
                                        self.next_stone=[[]]
                                        self.stone=self.next_stone
                                        self.draw()
                                        pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(1)
                                        if config['music']:
                                                pygame.mixer.music.stop()
                                        play_sound("gameover.ogg")
                                        for x in range(17, -1, -1):
                                                draw_matrix([[1 for _ in range(10)]], (0, x), self.screen)
                                                pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                                time.sleep(0.02)
                                        time.sleep(0.4)
                                        self.screen.fill((0,0,0))
                                        self.center_msg("Time Up!")
                                        pygame.display.update(pygame.Rect(self.off_x*config['cell_size'], self.off_y*config['cell_size'], 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(2)
                                        self.quit=True
                                elif self.timer<301 and self.timer%30 == 0:
                                        play_sound("countdown.ogg")
                                        
                        elif not self.paused:
                                self.timer+=1
                        if not (self.quit or self.paused) and (self.timer%1800 == 0 or (self.count and self.timer==900)):
                                play_sound("minute.ogg")
                        dont_burn_my_cpu.tick(30)
                fade_out()
                pygame.time.set_timer(pygame.USEREVENT+1, 0)

class ClientSocket(object):
        def __init__(self, sock=None, port=None):
                if isinstance(sock, socket.socket):
                        self.sock = sock
                elif sock and port:
                        self.sock = socket.create_connection((host, port))
                else:
                        self.sock = socket.socket()

        def connect(self, host, port):
                self.sock = socket.create_connection((host, port))

        def connect_raw(self, host, port):
                self.sock.connect((host, port))

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
                        chunk=self.sock.recv(2048)
                        if not chunk:
                                raise BrokenPipeError
                        totalrecd+=len(chunk)
                        chunks+=chunk
                return json.loads(chunks)
                
class TetrisMenu(TetrisClass):
        def __init__(self, menu, actions, title=None):
                self.menu=menu
                self.actions=actions
                self.quit=False
                self.selected=0
                self.title=title

        def add(self, option, action):
                self.menu.append(option)
                self.actions.append(action)

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (self.length, (9-len(self.menu)/2)*config['cell_size']))
                draw_matrix([[17]], (self.length/config['cell_size'], self.selected+9-len(self.menu)/2) , display)
                if self.title:
                        display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.title, False, (0,0,0), (255,255,255)), ((10.5-len(self.title)/4)*config['cell_size'], (7-len(self.menu)/2)*config['cell_size']))

        def handle_key(self, key):
                global bgoffset
                if key=='return' or key=='z':
                        if isinstance(self.actions[self.selected], TetrisClass):
                                play_sound("ok.ogg")
                                fade_out()
                                self.actions[self.selected].run()
                                time.sleep(0.1)
                                self.draw()
                                fade_in()
                        elif self.actions[self.selected]==None:
                                play_sound("cancel.ogg")
                        elif isinstance(self.actions[self.selected], types.FunctionType) or isinstance(self.actions[self.selected], tuple):
                                play_sound("ok.ogg")
                                fade_out()
                                self.actions[self.selected]()
                                time.sleep(0.1)
                                self.draw()
                                fade_in()
                elif key=='escape' or key=='x':
                        self.quit=True
                elif key=='down':
                        play_sound("select.ogg")
                        self.selected = (self.selected+1) % len(self.menu)
                elif key=='up':
                        play_sound("select.ogg")
                        self.selected-=1
                        if self.selected<0:
                                self.selected=len(self.menu)-1

        def drawUI(self):
                longest=0
                for x in self.menu:
                        if longest<len(x):
                                longest=len(x)
                self.length=9.5-(longest/4)
                self.length*=config['cell_size']
                self.UI=pygame.Surface(((longest//2+2)*config['cell_size'], len(self.menu)*config['cell_size']))
                for x in range(len(self.menu)):
                        draw_matrix([[13 for _ in range(longest//2+2)]], (0, x), self.UI)
                        self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.menu[x], False, (0,0,0)), (1.5*config['cell_size'], x*config['cell_size']))
                        
        def run(self):
                global bgoffset
                self.drawUI()
                self.draw()
                fade_in()
                while not self.quit:
                        self.draw()
                        pygame.display.flip()

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        fade_out()
                                        pygame.quit()
                                        sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                        if event.key==pygame.K_F12:
                                                now = datetime.now()
                                                pygame.image.save(display, "screenshot"+os.sep+"{}-{:02}-{:02}_{:02}-{:02}-{:02}.png".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
                                                play_sound("screenshot.ogg")
                                        else:
                                                self.handle_key(pygame.key.name(event.key))
                                elif event.type == pygame.USEREVENT+4:
                                        play_song("menu.ogg")
                                        pygame.mixer.music.set_endevent()

                        dont_burn_my_cpu.tick(30)
                play_sound("cancel.ogg")
                self.quit=False
                self.selected=0
                fade_out()

class TLevelSelect(TetrisMenu):
        def __init__(self, action, levels=9, heights=[0], title=""):
                self.quit=False
                self.levels=levels+1
                self.heights=heights
                self.selLevel=0
                self.selHeight=0
                self.action=action
                self.title=title

        def handle_key(self, key):
                global bgoffset
                if key=='return' or key=='z':
                        temp=list(self.action)
                        if "LVL" in temp:
                                temp[temp.index("LVL")]=self.selLevel
                        if "HIGH" in temp:
                                temp[temp.index("HIGH")]=self.heights[self.selHeight]
                        play_sound("ok.ogg")
                        fade_out()
                        if temp[0]=="App":
                                game=TetrisApp(*temp[1:])
                        elif temp[0]=="Timed":
                                game=TetrisTimed(*temp[1:])
                        game.run()
                        if not game.rage:
                                if saveFile!="Guest":
                                        saveData=None
                                        with open("saves"+os.sep+saveFile) as f:
                                                saveData=json.load(f)
                                        saveData[3]+=game.lineNums[0]
                                        saveData[4]+=game.lineNums[1]
                                        saveData[5]+=game.lineNums[2]
                                        saveData[6]+=game.lineNums[3]
                                if not isinstance(game, TetrisTimed):
                                        score=game.score
                                        if saveFile!="Guest":
                                                saveData[0].append(score)
                                        highscores[0][self.selLevel].append((saveFile, score))
                                        for x in range(len(highscores[0][self.selLevel])):
                                                if score>highscores[0][self.selLevel][x][1]:
                                                        highscores[0][self.selLevel].insert(x, (saveFile, score))
                                                        highscores[0][self.selLevel].pop()
                                                        break
                                        while len(highscores[0][self.selLevel])>3:
                                                highscores[0][self.selLevel].pop()
                                elif game.linec:
                                        if game.lines>game.linesClear-1:
                                                score=game.timer
                                                if saveFile!="Guest":
                                                        saveData[2].append(score)
                                                highscores[2][self.selLevel][self.selHeight].append((saveFile, score))
                                                for x in range(len(highscores[2][self.selLevel][self.selHeight])):
                                                        if score<highscores[2][self.selLevel][self.selHeight][x][1]:
                                                                highscores[2][self.selLevel][self.selHeight].insert(x, (saveFile, score))
                                                                highscores[2][self.selLevel][self.selHeight].pop()
                                                                break
                                                while len(highscores[2][self.selLevel][self.selHeight])>3:
                                                       highscores[2][self.selLevel][self.selHeight].pop()
                                else:
                                        if game.timer<1:
                                                score=game.score
                                                if saveFile!="Guest":
                                                        saveData[1].append(score)
                                                highscores[1][self.selLevel].append((saveFile, score))
                                                for x in range(len(highscores[1][self.selLevel])):
                                                        if score>highscores[1][self.selLevel][x][1]:
                                                                highscores[1][self.selLevel].insert(x, (saveFile, score))
                                                                highscores[1][self.selLevel].pop()
                                                                break
                                                while len(highscores[1][self.selLevel])>3:
                                                       highscores[1][self.selLevel].pop()
                                if saveFile!="Guest":
                                        with open("saves"+os.sep+saveFile, 'w') as f:
                                                json.dump(saveData, f)
                                save_highscores()
                        del game
                        time.sleep(0.1)
                        play_song("menu.ogg")
                        self.drawUI()
                        self.draw()
                        fade_in()
                elif key=='escape' or key=='x':
                        self.quit=True
                elif key=='right':
                        play_sound("select.ogg")
                        self.selLevel = (self.selLevel+1) % self.levels
                elif key=='left':
                        play_sound("select.ogg")
                        self.selLevel-=1
                        if self.selLevel<0:
                                self.selLevel=self.levels-1
                elif key=='up' and len(self.heights)>1:
                        play_sound("select.ogg")
                        self.selHeight = (self.selHeight+1) % len(self.heights)
                elif key=='down' and len(self.heights)>1:
                        play_sound("select.ogg")
                        self.selHeight-=1
                        if self.selHeight<0:
                                self.selHeight=len(self.heights)-1
                self.drawUI()

        def drawUI(self):
                self.UI=pygame.Surface((10*config['cell_size'], 6*config['cell_size']))
                draw_matrix([[13 for _ in range(10)] for _ in range(6)], (0, 0), self.UI)
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Level: "+str(self.selLevel), False, (0,0,0)), (3*config['cell_size'], 0.5*config['cell_size']))
                if len(self.heights)>1:
                        self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render("Height: "+str(self.selHeight), False, (0,0,0)), (2.75*config['cell_size'], 1.5*config['cell_size']))
                if self.action[0]=="App":
                        for x in range(len(highscores[0][self.selLevel])):
                                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(highscores[0][self.selLevel][x][0]+": "+str(highscores[0][self.selLevel][x][1]), False, (0,0,0)), (0.5*config['cell_size'], (2.5+x)*config['cell_size']))
                elif len(self.heights)==1:
                        for x in range(len(highscores[1][self.selLevel])):
                                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(highscores[1][self.selLevel][x][0]+": "+str(highscores[1][self.selLevel][x][1]), False, (0,0,0)), (0.5*config['cell_size'], (2.5+x)*config['cell_size']))
                else:
                        for x in range(len(highscores[2][self.selLevel][self.selHeight])):
                                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(highscores[2][self.selLevel][self.selHeight][x][0]+": "+"{0}:{1:02}".format(highscores[2][self.selLevel][self.selHeight][x][1]//1800, highscores[2][self.selLevel][self.selHeight][x][1]//30 % 60), False, (0,0,0)), (0.5*config['cell_size'], (3+x)*config['cell_size']))
                        return

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (5*config['cell_size'], 6*config['cell_size']))
                display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.title, False, (0,0,0), (255,255,255)), ((10-len(self.title)/4)*config['cell_size'], 4*config['cell_size']))

class FileDeletedException(Exception):
        pass

class TFileSelect(TetrisMenu):
        def __init__(self, files, action):
                if "highscore" in files:
                        files.remove("highscore")
                super().__init__(files + ["New File...", "Guest"], action, "File Select")

        def handle_key(self, key):
                global bgoffset
                if key=='return' or key=='z':
                        play_sound("ok.ogg")
                        if self.selected+2==len(self.menu):
                                fade_out()
                                name=TTextInput("Name Entry").run()
                                if name and not (name=="Guest" or os.path.exists("saves"+os.sep+name)):
                                        with open("saves"+os.sep+name, 'w') as f:
                                                json.dump([[],[],[],0,0,0,0], f)
                                        self.menu.insert(-2, name)
                                        self.drawUI()
                                self.draw()
                                fade_in()
                        else:
                                global saveFile
                                saveFile = self.menu[self.selected]
                                fade_out()
                                self.actions.title=saveFile
                                try:
                                        self.actions.run()
                                except FileDeletedException:
                                        self.menu.pop(self.selected)
                                        self.selected-=1
                                        self.drawUI()
                                self.draw()
                                fade_in()
                elif key=='escape' or key=='x':
                        self.quit=True
                elif key=='down':
                        play_sound("select.ogg")
                        self.selected = (self.selected+1) % len(self.menu)
                elif key=='up':
                        play_sound("select.ogg")
                        self.selected-=1
                        if self.selected<0:
                                self.selected=len(self.menu)-1

class TTextInput(TetrisMenu):
        def __init__(self, title=None, text=""):
                self.quit=False
                self.title=title
                self.text=text

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, ((10-len(self.text)/4)*config['cell_size'], 9*config['cell_size']))
                if self.title:
                        display.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.title, False, (0,0,0), (255,255,255)), ((10.5-len(self.title)/4)*config['cell_size'], 7*config['cell_size']))

        def drawUI(self):
                self.UI=pygame.Surface(((len(self.text)+1)/2*config['cell_size'], 1.5*config['cell_size']))
                self.UI.fill((255, 255, 255))
                self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(self.text, False, (0,0,0)), (config['cell_size']/4, config['cell_size']/2))

        def handle_key(self, key, unicode):
                if key=="return" or key=="escape":
                        self.quit=True
                        if key=="escape":
                                self.text=False
                elif key=="backspace":
                        self.text=self.text[:-1]
                        self.drawUI()
                elif len(unicode)==1:
                        self.text+=unicode
                        self.drawUI()

        def run(self):
                global bgoffset
                self.drawUI()
                self.draw()
                fade_in()
                while not self.quit:
                        self.draw()
                        pygame.display.flip()

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        fade_out()
                                        pygame.quit()
                                        sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                        self.handle_key(pygame.key.name(event.key), event.unicode)
                                elif event.type == pygame.USEREVENT+4:
                                        play_song("menu.ogg")
                                        pygame.mixer.music.set_endevent()

                        dont_burn_my_cpu.tick(30)
                play_sound("cancel.ogg")
                self.quit=False
                self.selected=0
                fade_out()
                return self.text

class TMessage(TetrisMenu):
        def __init__(self, msg):
                self.msg = msg
                self.quit = False
                self.yn = False

        def drawUI(self):
                longest=0
                split = self.msg.split('\n')
                self.height=8.5-len(split)/2
                self.height*=config['cell_size']
                for x in split:
                        if longest<len(x):
                                longest=len(x)
                self.length=10-longest/4
                self.length*=config['cell_size']
                self.UI=pygame.Surface((longest/2*config['cell_size'], (len(split)+1)*config['cell_size']))
                self.UI.fill((255,255,255))
                for x in range(len(split)):
                        self.UI.blit(pygame.font.Font("joystix.ttf", config['cell_size']//2+2).render(split[x], False, (0,0,0)), ((longest/4-len(split[x])/4+0.25)*config['cell_size'], (0.5+x)*config['cell_size']))

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (self.length, self.height))

        def handle_key(self, key):
                if key=="return" or key=="z":
                        self.quit=True
                        self.yn=True
                elif key=="escape" or key=="x":
                        self.quit=True

        def run(self):
                super().run()
                return self.yn

class TPlayerCard(TMessage):
        def __init__(self):
                super().__init__("")

        def run(self):
                if saveFile=="Guest":
                        TMessage("Guests cannot\nuse scorecard").run()
                        return
                with open("saves"+os.sep+saveFile) as f:
                        saveData = json.load(f)
                totalLines = sum(saveData[3:])
                if totalLines==0:
                        TMessage("Not enough data!\nYour stats will\nappear here after\nyou play for a bit.").run()
                        return
                if not saveData[0]:
                        saveData[0]=[0]
                if not saveData[1]:
                        saveData[1]=[0]
                if not saveData[2]:
                        saveData[2]=[0]
                power = mean(saveData[0])+mean(saveData[1])+mean(saveData[2])
                self.msg=("Player "+saveFile+"\nPower: "+str(round(power/100))
                          +"\nLines: "+str(sum((saveData[3], saveData[4]*2, saveData[5]*3, saveData[6]*4)))
                          +"\nSingle: "+str(round(saveData[3]/totalLines*100, 2))
                          +"%\nDouble: "+str(round(saveData[4]/totalLines*100, 2))
                          +"%\nTriple: "+str(round(saveData[5]/totalLines*100, 2))
                          +"%\nTetris: "+str(round(saveData[6]/totalLines*100, 2))+"%")
                super().run()

class TOptionsMenu(TetrisMenu):
        def __init__(self):
                def toggle_cfg(option):
                        config[option]=not config[option]
                        if option=="music":
                                if config[option]:
                                        pygame.mixer.init()
                                        play_song("menu.ogg")
                                else:
                                        pygame.mixer.music.fadeout(1000)
                        
                def erase_highscores():
                        global highscores
                        if not TMessage("Ok to delete\nhighscore data?\nZ-Yes X-No").run():
                                return
                        os.remove("saves"+os.sep+"highscore")
                        highscores=[[[] for x in range(10)] for x in range(2)]
                        highscores.append([[[] for x in range (6)] for x in range(10)])
                        save_highscores()
                        TMessage("Highscores cleared").run()
                        
                def erase_my_file():
                        global saveFile
                        if not TMessage("Ok to delete\nfile "+saveFile+"?\nZ-Yes X-No").run():
                                return
                        os.remove("saves"+os.sep+saveFile)
                        saveFile="Guest"
                        TMessage("Save deleted\nReturning to\nfile select...").run()
                        raise FileDeletedException()
                super().__init__(["Toggle Music", "Toggle Sound", "Erase Highscores", "Erase My File"], [lambda:toggle_cfg("music"), lambda:toggle_cfg("sound"), erase_highscores, erase_my_file], "Options")

        def run(self):
                if saveFile=="Guest":
                        TMessage("Guests cannot\nchange settings").run()
                        return
                super().run()

if __name__=="__main__":                        
        pygame.init()
        if config['music']:
                pygame.mixer.init()
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
        #tiles.insert(15, pygame.Surface((config['cell_size'],config['cell_size'])))
        #tiles[15].fill((17, 83, 18))
        #tiles.insert(16, pygame.Surface((config['cell_size'],config['cell_size'])))
        #tiles[16].fill((135, 168, 123))
        tiles.insert(17, pygame.Surface((config['cell_size'],config['cell_size'])))
        tiles[17].fill((193, 221, 243))

        pygame.key.set_repeat(200,25)
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        _song=None
        highscores=[]
        saveFile=None
        if not os.path.exists("saves"):
                os.mkdir("saves")
        if not os.path.exists("screenshot"):
                os.mkdir("screenshot")
        if not os.path.exists("saves"+os.sep+"highscore"):
                with open("saves"+os.sep+"highscore", 'w') as f:
                        x=[[[] for x in range(10)] for x in range(2)]
                        x.append([[[] for x in range (6)] for x in range(10)])
                        json.dump(x, f)
        with open("saves"+os.sep+"highscore") as f:
                highscores=json.load(f)
        def save_highscores():
                with open("saves"+os.sep+"highscore", 'w') as f:
                        json.dump(highscores, f)

        bgscroll=pygame.Surface((config['cell_size']*21, config['cell_size']*19))
        draw_matrix([[15+((x+y)%2) for x in range(21)] for y in range(18+config['cell_size'])], (0,0), bgscroll)
        bgoffset=0
        dont_burn_my_cpu = pygame.time.Clock()
        MarathonLevel = TLevelSelect(("App", config['cell_size']*2, 0, "LVL"), title="Marathon")
        UltraLevel = TLevelSelect(("Timed", config['cell_size']*2, 0, "LVL", 5400), title="Time Attack")
        LinesLevel = TLevelSelect(("Timed", config['cell_size']*2, 0, "LVL", 0, 40, "HIGH"), 9, (0, 2, 4, 6, 8, 10), "40 Lines")
        onePMode = TetrisMenu(["Marathon", "Time Attack", "40 Lines"], [MarathonLevel, UltraLevel, LinesLevel])
        menu = TetrisMenu(["1 Player", "Options", "Scorecard"], [onePMode, TOptionsMenu(), TPlayerCard()], saveFile)
        if config['music']:
                pygame.mixer.music.load("music"+os.sep+"menu_intro.ogg")
                time.sleep(0.25)
                pygame.mixer.music.play(0)
                pygame.mixer.music.set_endevent(pygame.USEREVENT+4)
        TFileSelect([x for x in os.listdir("saves")], menu).run()
        pygame.quit()
