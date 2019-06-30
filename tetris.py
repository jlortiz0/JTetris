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

import pygame, os, time, random, sys, json, types, socket, select, math
from statistics import mean
from datetime import datetime

# The configuration
config = {
        'cell_size':    40,
        'songs':        ("dxa1.ogg", "dxa2.ogg", "dxa3.ogg", "danger.ogg"),
        'heights':      (19, 9, 6, 3)
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
        53,
        49,
        45,
        41,
        37,
        33,
        28,
        22,
        17,
        11,
        10,
        9,
        8,
        7,
        6, 6,
        4, 4,
        3
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

_sound_library={}
_snd_vol=60
def play_sound(path):
        global _sound_library
        sound=_sound_library.get(path)
        if sound is None:
                sound=pygame.mixer.Sound("sound"+os.sep+path)
                _sound_library[path]=sound
        sound.set_volume(_snd_vol/100)
        sound.play()

_song=None
_mus_vol=50
def play_song(song):
        global _song
        if _song==song:
                return
        _song=song
        pygame.mixer.music.stop()
        pygame.mixer.music.load("music"+os.sep+song)
        pygame.mixer.music.set_volume(_mus_vol/100)
        pygame.mixer.music.play(-1)

def fade_out():
        pygame.time.set_timer(pygame.USEREVENT+3, 0)
        fadebg = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadebg.blit(display, (0,0))
        fadeeffect = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadeeffect.fill((255,255,255))
        for x in range(0, 257, 16):
                fadeeffect.set_alpha(min(x, 255))
                display.blit(fadebg, (0,0))
                display.blit(fadeeffect, (0,0))
                pygame.display.flip()
                dont_burn_my_cpu.tick(60)

def fade_in():
        fadebg = display.copy()
        fadeeffect = pygame.Surface((config['cell_size']*20, config['cell_size']*18))
        fadeeffect.fill((255,255,255))
        for x in range(256, -1, -16):
                fadeeffect.set_alpha(min(x, 255))
                display.blit(fadebg, (0,0))
                display.blit(fadeeffect, (0,0))
                pygame.display.flip()
                dont_burn_my_cpu.tick(60)
        pygame.time.set_timer(pygame.USEREVENT+3, 100)
        pygame.event.clear(pygame.KEYDOWN)

_font=None
def draw_text(text, pos, surf, color=bg_colors[5], bg=None):
        global _font
        if not _font:
                _font=pygame.font.Font("joystix.ttf", config['cell_size']//2+4)
        surf.blit(_font.render(text, False, color, bg), [config['cell_size']*x for x in pos])

def screenshot():
        now = datetime.now()
        pygame.image.save(display, "screenshot"+os.sep+"{}-{:02}-{:02}_{:02}-{:02}-{:02}.png".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
        play_sound("screenshot.ogg")

class TetrisClass:
        def draw(self):
                raise NotImplementedError

        def drawUI(self):
                raise NotImplementedError

        def run(self):
                raise NotImplementedError

class TetrisApp(TetrisClass):
        def __init__(self, level=0):
                self.quit=False
                self.rage=False
                self.lineNums = [0,0,0,0]
                self.width = config['cell_size']*10
                self.height = config['cell_size']*18
                self.screen = display.subsurface(pygame.Rect(2*config['cell_size'], 0, self.width, self.height))
                self.board = new_board()
                self.next_stone=[random.choice(tetris_shapes), random.choice(tetris_shapes)]
                self.level=level
                self.speed=speeds[self.level]
                self.new_stone()
                self.lines=0
                self.bgcolor=bg_colors[self.level//5]
                self.score=0
        
        def new_stone(self):
                self.stone=self.next_stone.pop(0)
                self.next_stone.append(random.choice(tetris_shapes))
                while self.next_stone[0]==self.next_stone[1]==self.stone:
                        self.next_stone[1]=random.choice(tetris_shapes)
                self.stone_x = int(10 / 2 - len(self.stone[0])/2)
                self.stone_y = 1
                self.rot_center=[0,1,1,1]
                self.dropdelay = 15 + self.speed
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
                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.4)
                        pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(17, -1, -1):
                                draw_matrix([[4 for _ in range(10)]], (0, x), self.screen)
                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.02)
                        time.sleep(0.4)
                        self.screen.fill((0,0,0))
                        self.center_msg("Game Over!")
                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(2)

        def level_up(self):
                if self.level>29:
                        return
                play_sound("level.ogg")
                self.level+=1
                if self.level<len(speeds):
                        self.speed=speeds[self.level]
                if (self.level % 5)==0 and self.level/5<len(bg_colors)+1:
                        self.fade=[0, self.bgcolor, bg_colors[self.level//5]]
                draw_matrix([[13, 13, 13]], (4, 11), self.UI)
                draw_text(":"+str(self.level), (3.8, 11.1), self.UI)
        
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
                if (not (self.quit or self.paused)) and self.dropdelay < self.speed:
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
                                        if all(self.board[i]) and 14 not in self.board[i]:
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
                                        if any(self.board[x]):
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
                draw_matrix([[13, 13, 13, 13]], (4, 13), self.UI)
                draw_text(":"+str(self.lines), (3.8, 13.1), self.UI)
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
                        dont_burn_my_cpu.tick(20)
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
                                if check_collision(self.board,
                                           self.stone,
                                           (self.stone_x, self.stone_y+1)):
                                        self.dropdelay = self.speed
                                play_sound("rotate.ogg")
                        elif not check_collision(self.board,
                                               new_stone,
                                               (self.stone_x+self.rot_center[3]-center[3], self.stone_y+self.rot_center[2]-center[2])):
                                self.stone = new_stone
                                self.stone_x+=self.rot_center[3]-center[3]
                                self.stone_y+=self.rot_center[2]-center[2]
                                self.rot_center = center
                                if check_collision(self.board,
                                           self.stone,
                                           (self.stone_x, self.stone_y+1)):
                                        self.dropdelay = self.speed
                                play_sound("rotate.ogg")
        
        def toggle_pause(self):
                self.screen.fill((0,0,0))
                self.center_msg("Paused")
                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                self.paused = not self.paused
                play_sound("pause.ogg")
                if self.paused:
                        pygame.mixer.music.pause()
                else:
                        pygame.mixer.music.unpause()
        
        def exit(self):
                if self.paused:
                        self.quit=True
                        self.rage=True

        def drawUI(self):
                self.UI=pygame.Surface((config['cell_size']*8, config['cell_size']*18))
                self.UI.fill((128,128,128))
                self.UI.set_colorkey((128,128,128))
                draw_matrix([[14] for _ in range(18)], (0, 0), self.UI)
                draw_matrix([[13, 13, 13, 13, 13] for _ in range(5)], (2, 2), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 9), self.UI)
                draw_text("Score:", (1.3, 9.1), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 11), self.UI)
                draw_text("Level:", (1.3, 11.1), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 13), self.UI)
                draw_text("Lines:", (1.3, 13.1), self.UI)
                draw_text(str(self.level), (4.3, 11.1), self.UI)
                draw_text("0", (4.3, 13.1), self.UI)

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (config['cell_size']*12, 0))
                draw_matrix(self.next_stone[0], (15, 3), display)
                if self.score>9999999:
                        self.score=9999999
                draw_text(str(self.score), (16.3, 9.1), display)
                draw_matrix([[14] for _ in range(18)], (1,0), display)
                self.screen.fill(self.bgcolor)
                draw_matrix(self.board, (0,-1), self.screen)
                draw_matrix(self.stone,(self.stone_x, self.stone_y-1.1), self.screen)
        
        def run(self):
                global bgoffset
                key_actions = {
                        pygame.K_LEFT:  lambda:self.move(-1),
                        pygame.K_RIGHT: lambda:self.move(+1),
                        pygame.K_DOWN:  lambda:self.drop(True),
                        pygame.K_z:     lambda:self.rotate_stone(-1),
                        pygame.K_x:     lambda:self.rotate_stone(+1),
                        pygame.K_RETURN:self.toggle_pause,
                        pygame.K_ESCAPE:self.exit,
                        pygame.K_F12:   screenshot,
                        pygame.K_l:     self.level_up
                }

                self.paused = False
                self.fade=()
                debounce = dict.fromkeys(key_actions, False)
                
                self.drawUI()
                self.draw()
                play_song("dxa1.ogg")
                fade_in()
                while not self.quit:
                        if not self.paused:
                                self.draw()
                                pygame.display.flip()
                                if self.fade:
                                        self.fade[0]=self.fade[0]+1
                                        self.bgcolor=[x + (((y-x)/30)*self.fade[0]) for x,y in zip(self.fade[1], self.fade[2])]
                                        if self.fade[0]==30:
                                                self.bgcolor=self.fade[2]
                                                self.fade=()
                                if self.dropdelay:
                                        self.dropdelay -= 1
                                else:
                                        self.drop()
                                        self.dropdelay = self.speed
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.quit=True
                                elif event.type == pygame.KEYDOWN and event.key in key_actions and not debounce[event.key]:
                                        if not (273 < event.key < 277):
                                                debounce[event.key] = True
                                        key_actions[event.key]()
                                elif event.type == pygame.KEYUP and event.key in key_actions:
                                        debounce[event.key] = False
                                        
                        dont_burn_my_cpu.tick(60)
                fade_out()

class TetrisTimed(TetrisApp):
        def __init__(self, level=0, time=0, lines=0, height=0):
                super().__init__(level)
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
                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(1)
                        pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(17, -1, -1):
                                draw_matrix([[1 for _ in range(10)]], (0, x), self.screen)
                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.02)
                        time.sleep(0.4)
                        self.screen.fill((0,0,0))
                        self.center_msg("Cleared!")
                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(2)
                        self.quit=True

        def level_up(self):
                pass

        def drawUI(self):
                self.UI=pygame.Surface((config['cell_size']*8, config['cell_size']*18))
                self.UI.fill((128,128,128))
                self.UI.set_colorkey((128,128,128))
                draw_matrix([[14] for _ in range(18)], (0, 0), self.UI)
                draw_matrix([[13, 13, 13, 13, 13] for _ in range(5)], (2, 2), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 9), self.UI)
                draw_text("Score:", (1.3, 9.1), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 11), self.UI)
                draw_text("Time:", (1.3, 11.1), self.UI)
                draw_matrix([[15, 13, 13, 13, 13, 13, 13]], (1, 13), self.UI)
                draw_text("Lines:", (1.3, 13.1), self.UI)
                draw_text("0", (4.3, 13.1), self.UI)

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                if self.linec:
                        draw_matrix([[13, 13, 13, 13]], (4, 13), self.UI)
                        draw_text(str(max(0, self.linesClear-self.lines)), (4.3, 13.1), self.UI)
                display.blit(self.UI, (config['cell_size']*12, 0))
                draw_matrix(self.next_stone[0], (15, 3), display)
                if self.score>9999999:
                        self.score=9999999
                draw_text(str(self.score), (16.3, 9.1), display)
                draw_text("{0}:{1:02}".format(self.timer//3600, self.timer//60 % 60), (15.7, 11.1), display)
                draw_matrix([[14] for _ in range(18)], (1,0), display)
                self.screen.fill(self.bgcolor)
                draw_matrix(self.board, (0,-1), self.screen)
                draw_matrix(self.stone,(self.stone_x, self.stone_y-0.925), self.screen)

        def run(self):
                global bgoffset
                key_actions = {
                        pygame.K_LEFT:  lambda:self.move(-1),
                        pygame.K_RIGHT: lambda:self.move(+1),
                        pygame.K_DOWN:  lambda:self.drop(True),
                        pygame.K_z:     lambda:self.rotate_stone(-1),
                        pygame.K_x:     lambda:self.rotate_stone(+1),
                        pygame.K_RETURN:self.toggle_pause,
                        pygame.K_ESCAPE:self.exit,
                        pygame.K_F12:   screenshot
                }
                
                self.paused = False
                debounce = dict.fromkeys(key_actions, False)

                self.drawUI()
                self.draw()
                play_song("dxa1.ogg")
                fade_in()
                while not self.quit:
                        if not self.paused:
                                self.draw()
                                pygame.display.flip()
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.quit=True
                                elif event.type == pygame.KEYDOWN and event.key in key_actions and not debounce[event.key]:
                                        if not (273 < event.key < 277):
                                                debounce[event.key] = True
                                        key_actions[event.key]()
                                elif event.type == pygame.KEYUP and event.key in key_actions:
                                        debounce[event.key] = False
                                        
                        if self.count and not self.paused:
                                self.timer-=1
                                if self.timer==0:
                                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                                        play_sound("timeup.ogg")
                                        self.bgcolor=bg_colors[2]
                                        self.next_stone=[[]]
                                        self.stone=self.next_stone
                                        self.draw()
                                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(1)
                                        pygame.mixer.music.stop()
                                        play_sound("gameover.ogg")
                                        for x in range(17, -1, -1):
                                                draw_matrix([[1 for _ in range(10)]], (0, x), self.screen)
                                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                                time.sleep(0.02)
                                        time.sleep(0.4)
                                        self.screen.fill((0,0,0))
                                        self.center_msg("Time Up!")
                                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(2)
                                        self.quit=True
                                elif self.timer<601 and self.timer%60 == 0:
                                        play_sound("countdown.ogg")
                                        
                        elif not self.paused:
                                self.timer+=1
                        if not (self.quit or self.paused) and (self.timer%1800 == 0 or (self.count and self.timer==900)):
                                play_sound("minute.ogg")
                        if self.dropdelay:
                                self.dropdelay -= 1
                        else:
                                self.drop()
                                self.dropdelay = self.speed
                        dont_burn_my_cpu.tick(60)
                fade_out()

class ClientSocket(object):
        def __init__(self, sock=None, port=None):
                if isinstance(sock, socket.socket):
                        self.sock = sock
                elif sock and port:
                        self.sock = socket.create_connection((sock, port))
                else:
                        self.sock = socket.socket()

        def connect(self, host, port):
                self.sock = socket.create_connection((host, port))

        def connect_raw(self, host, port):
                self.sock.connect((host, port))

        def close(self):
                try:
                        self.send("quit")
                        self.sock.shutdown(1)
                        self.sock.close()
                except ConnectionError:
                        pass

        def readable(self):
                return bool(select.select([self.sock], [], [], 0)[0])

        def send(self, data):
                data = json.dumps(data).encode()
                if len(data)>16777215:
                        raise ValueError
                size=int.to_bytes(len(data), 3, 'big')
                totalsent = 0
                while totalsent<3:
                        sent=self.sock.send(size[totalsent:])
                        if sent==0:
                                raise BrokenPipeError
                        totalsent+=sent
                totalsent = 0
                size = len(data)
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
                draw_matrix([[15]], (self.length/config['cell_size'], self.selected+9-len(self.menu)/2) , display)
                if self.title:
                        draw_text(self.title, (10.5-len(self.title)/4, 7-len(self.menu)/2), display, bg=(255, 255, 255))

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
                        elif isinstance(self.actions[self.selected], types.FunctionType):
                                play_sound("ok.ogg")
                                fade_out()
                                self.actions[self.selected]()
                                time.sleep(0.1)
                                self.draw()
                                fade_in()
                        elif type(self.actions[self.selected]==type) and issubclass(self.actions[self.selected], TetrisClass):
                                play_sound("ok.ogg")
                                fade_out()
                                self.actions[self.selected]().run()
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
                        draw_text(self.menu[x], (1.3, x), self.UI)
                        
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
                                                screenshot()
                                        else:
                                                self.handle_key(pygame.key.name(event.key))
                                elif event.type == pygame.USEREVENT+4:
                                        play_song("menu.ogg")
                                        pygame.mixer.music.set_endevent()

                        dont_burn_my_cpu.tick(60)
                play_sound("cancel.ogg")
                self.quit=False
                self.selected=0
                fade_out()

class TLevelSelect(TetrisMenu):
        def __init__(self, action, levels=9, heights=[0], title=""):
                if type(action[0])!=type or not issubclass(action[0], TetrisClass):
                        raise TypeError("Expected action[0] to be subclass of TetrisClass")
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
                        game=temp[0](*temp[1:])
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
                draw_text("Level: "+str(self.selLevel), (3, 0.5), self.UI)
                if len(self.heights)>1:
                        draw_text("Height: "+str(self.selHeight), (2.75, 1.5), self.UI)
                if self.action[0]==TetrisApp:
                        for x in range(len(highscores[0][self.selLevel])):
                                draw_text(highscores[0][self.selLevel][x][0]+": "+str(highscores[0][self.selLevel][x][1]), (0.5, 2.5+x), self.UI)
                elif len(self.heights)==1:
                        for x in range(len(highscores[1][self.selLevel])):
                                draw_text(highscores[1][self.selLevel][x][0]+": "+str(highscores[1][self.selLevel][x][1]), (0.5, 2.5+x), self.UI)
                else:
                        for x in range(len(highscores[2][self.selLevel][self.selHeight])):
                                draw_text(highscores[2][self.selLevel][self.selHeight][x][0]+": "+"{0}:{1:02}".format(highscores[2][self.selLevel][self.selHeight][x][1]//1800, highscores[2][self.selLevel][self.selHeight][x][1]//60 % 60), (0.5, 3+x), self.UI)

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (5*config['cell_size'], 6*config['cell_size']))
                draw_text(self.title, (10-len(self.title)/4, 4), display, bg=(255,255,255))

class FileDeletedException(Exception):
        pass

class TFileSelect(TetrisMenu):
        def __init__(self, files, action):
                if "highscore" in files:
                        files.remove("highscore")
                super().__init__(files + ["New File...", "Guest"], action, "File Select")

        def handle_key(self, key):
                global _mus_vol, _snd_vol
                if key=='return' or key=='z':
                        play_sound("ok.ogg")
                        if self.selected+2==len(self.menu):
                                fade_out()
                                name=TTextInput("Name Entry").run()
                                if name:
                                        name=name[:10].strip()
                                        if not (name=="Guest" or os.path.exists("saves"+os.sep+name)):
                                                with open("saves"+os.sep+name, 'w') as f:
                                                        json.dump([[],[],[],0,0,0,0,_mus_vol,_snd_vol], f)
                                                self.menu.insert(-2, name)
                                                self.drawUI()
                                self.draw()
                                fade_in()
                        else:
                                global saveFile
                                saveFile = self.menu[self.selected]
                                if saveFile != "Guest":
                                        with open("saves"+os.sep+saveFile) as f:
                                                saveData = json.load(f)
                                        _mus_vol=saveData[7]
                                        pygame.mixer.music.set_volume(_mus_vol/100)
                                        _snd_vol=saveData[8]
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
                display.blit(self.UI, ((10.25-len(self.text)/4)*config['cell_size'], 9*config['cell_size']))
                if self.title:
                        draw_text(self.title, (10.5-len(self.title)/4, 7), display, bg=(255, 255, 255))

        def drawUI(self):
                self.UI=pygame.Surface(((len(self.text)+1)/2*config['cell_size'], 1.5*config['cell_size']))
                self.UI.fill((255, 255, 255))
                draw_text(self.text, (0.25, 0.5), self.UI)

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

                        dont_burn_my_cpu.tick(60)
                play_sound("cancel.ogg")
                fade_out()
                return self.text

class TMessage(TetrisMenu):
        def __init__(self, msg):
                self.msg = msg.strip()
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
                self.UI=pygame.Surface(((longest+1)/2*config['cell_size'], (len(split)+1)*config['cell_size']))
                self.UI.fill((255,255,255))
                for x in range(len(split)):
                        draw_text(split[x], (longest/4-len(split[x])/4+0.25, 0.5+x), self.UI)

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
                totalLines = sum(saveData[3:7])
                if totalLines==0:
                        TMessage("Your stats will\nappear here after\nyou play a game.").run()
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
                        TMessage("Save deleted\nReturning to title").run()
                        raise FileDeletedException()
                super().__init__(["Music Volume: ", "Sound Volume: ", "Erase Highscores", "Erase My File"], ["MUS", "SND", erase_highscores, erase_my_file], "Options")

        def handle_key(self, key):
                global bgoffset, _mus_vol, _snd_vol
                if key=='return' or key=='z':
                        if isinstance(self.actions[self.selected], types.FunctionType):
                                play_sound("ok.ogg")
                                fade_out()
                                self.actions[self.selected]()
                                self.draw()
                                fade_in()
                        else:
                                play_sound("cancel.ogg")
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
                elif key=='left' and isinstance(self.actions[self.selected], str):
                        if self.selected==0 and _mus_vol:
                                _mus_vol-=1
                                pygame.mixer.music.set_volume(_mus_vol/100)
                                self.drawUI()
                        elif _snd_vol:
                                _snd_vol-=1
                                self.drawUI()
                elif key=='right' and isinstance(self.actions[self.selected], str):
                        if self.selected==0 and _mus_vol<100:
                                _mus_vol+=1
                                pygame.mixer.music.set_volume(_mus_vol/100)
                                self.drawUI()
                        elif _snd_vol<100:
                                _snd_vol+=1
                                self.drawUI()

        def drawUI(self):
                temp = self.menu[:2]
                self.menu[0]=self.menu[0]+str(_mus_vol)
                self.menu[1]=self.menu[1]+str(_snd_vol)
                super().drawUI()
                self.menu = temp + self.menu[2:]

        def run(self):
                if saveFile=="Guest":
                        TMessage("Guests cannot\nchange settings").run()
                        return
                super().run()
                with open("saves"+os.sep+saveFile) as f:
                        saveData = json.load(f)
                saveData[7] = _mus_vol
                saveData[8] = _snd_vol
                with open("saves"+os.sep+saveFile, 'w') as f:
                        json.dump(saveData, f)

class ServerMenu(TetrisMenu):
        def __init__(self, sock=None):
                self.quit=False
                if isinstance(sock, ClientSocket):
                        self.sock=sock
                elif isinstance(sock, str):
                        port=7777
                        if ':' in sock:
                                port=int(sock.split(':')[1])
                                sock=sock.split(':')[0]
                        self.sock=ClientSocket(sock, port)
                else:
                        try:
                                ip = TTextInput("Server IP:", "127.0.0.1").run()
                                if ip:
                                        self.__init__(ip)
                                else:
                                        self.quit = True
                        except ConnectionError as e:
                                self.quit=True
                                TMessage("There was an\nerror connecting").run()
                        return
                self.sock.send('isJTetris')
                time.sleep(1)
                if self.sock.readable():
                        if self.sock.receive()!="yes":
                                self.sock.sock.shutdown(1)
                                self.sock.sock.close()
                                raise ConnectionAbortedError
                else:
                        self.sock.sock.shutdown(1)
                        self.sock.sock.close()
                        raise ConnectionRefusedError
                self.sock.send('nick '+saveFile)
                self.sock.send('nicks')
                self.users = self.sock.receive()
                if type(self.users) is str:
                        self.sock.receive()
                        # Handle this better
                        TMessage("You are already\non the server!").run()
                        self.quit=True
                self.selected=[0,0]
                self.status = "Welcome!"

        def drawUI(self):
                self.UI=pygame.Surface((17*config['cell_size'], 16*config['cell_size']))
                self.UI.fill(bg_colors[4])
                self.UI.set_colorkey(bg_colors[4])
                draw_matrix([[13,13,13,13,13,0,13,13,13,13,13,0,13,13,13,13,13] for _ in range(14)], (0,0), self.UI)
                draw_matrix([[13 for _ in range(17)]], (0,15), self.UI)
                for x in range(len(self.users[:14])):
                        draw_text(self.users[x], (1, 0.25+x), self.UI)
                for x in range(len(self.users[15:29])):
                        draw_text(self.users[14+x], (7, 0.25+x), self.UI)
                for x in range(len(self.users[29:43])):
                        draw_text(self.users[28+x], (13, 0.25+x), self.UI)
                
        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (1.5*config['cell_size'], config['cell_size']))
                draw_matrix([[15]], (1.5+self.selected[0]*6, 1+self.selected[1]), display)
                draw_text(self.status, (10-len(self.status)/4, 16), display)

        def handle_key(self, key):
                if key=="escape":
                        self.quit=True
                elif key=="return":
                        selected=self.selected[1]+self.selected[0]*15
                        if len(self.users)<=selected:
                                self.status="That's a blank space"
                                play_sound("cancel.ogg")
                        elif self.users[selected]==saveFile:
                                self.status="Cannot challenge yourself!"
                                play_sound("cancel.ogg")
                        else:
                                self.status = ""
                                self.sock.send("challenge "+self.users[selected])
                                data = self.sock.receive()
                                if data=="busy":
                                        self.status=self.users[selected]+" is busy"
                                        play_sound("cancel.ogg")
                                elif data=="BadNick":
                                        self.status="Just missed 'em! "+self.users[selected]+" left"
                                        play_sound("cancel.ogg")
                                else:
                                        fade_out()
                                        result = ChallengeMessage(self.sock, False, self.users[selected]).run()
                                        if isinstance(result, ConnectionError):
                                                self.quit=True
                                        elif result and isinstance(result, bool):
                                                P2Mngr(self.sock, self.users[selected]).run()
                                                pass
                                        fade_in()
                elif key=="left":
                        self.selected[0]-=1
                        self.selected[0]%=3
                        play_sound("select.ogg")
                elif key=="right":
                        self.selected[0]+=1
                        self.selected[0]%=3
                        play_sound("select.ogg")
                elif key=="down":
                        self.selected[1]+=1
                        self.selected[1]%=14
                        play_sound("select.ogg")
                elif key=="up":
                        self.selected[1]-=1
                        self.selected[1]%=14
                        play_sound("select.ogg")

        def run(self):
                if self.quit:
                        return
                global bgoffset
                pygame.mixer.music.set_endevent()
                pygame.mixer.music.fadeout(1000)
                self.drawUI()
                self.draw()
                fade_in()
                while not self.quit:
                        self.draw()
                        pygame.display.flip()
                        if self.sock.readable():
                                try:
                                        msg=self.sock.receive()
                                except ConnectionError:
                                        TMessage("The connection\nwas interrupted").run()
                                        break
                                print(msg)
                                if msg[:5]=='join ':
                                        msg=msg.split(' ')
                                        if msg[2]=='None' or not msg[2] in self.users:
                                                self.users.append(msg[1])
                                                self.status = msg[1]+" joined"
                                        else:
                                                self.users[self.users.index(msg[2])]=msg[1]
                                                self.status = msg[2]+" is now "+msg[1]
                                        self.drawUI()
                                elif msg[:6]=='leave ':
                                        msg=msg[6:]
                                        if msg!='None' and msg in self.users:
                                                self.users.remove(msg)
                                                self.status = msg+" left"
                                                self.drawUI()
                                elif msg[:11]=='challenged ':
                                        msg=msg[11:]
                                        if msg in self.users:
                                                play_sound("challenger.ogg")
                                                fade_out()
                                                result=ChallengeMessage(self.sock, True, msg).run()
                                                if isinstance(result, ConnectionError):
                                                        _song=None
                                                        play_song("menu.ogg")
                                                        return
                                                elif isinstance(result, str):
                                                        pass
                                                elif result:
                                                        self.sock.send("accept")
                                                        P2Mngr(self.sock, msg).run()
                                                else:
                                                        self.sock.send("reject")
                                                self.sock.send('nicks')
                                                self.users = self.sock.receive()
                                                self.drawUI()
                                                self.draw()
                                                fade_in()

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.sock.close()
                                        fade_out()
                                        pygame.quit()
                                        sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                        self.handle_key(pygame.key.name(event.key))

                        dont_burn_my_cpu.tick(60)
                play_sound("cancel.ogg")
                fade_out()
                self.sock.close()
                _song=None
                play_song("menu.ogg")

class TempMessage(TMessage):
        def __init__(self, msg, time=120):
                super().__init__(msg)
                self.timer = time

        def run(self):
                global bgoffset
                self.drawUI()
                self.draw()
                fade_in()
                while self.timer:
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
                                        self.timer=1

                        dont_burn_my_cpu.tick(60)
                        self.timer-=1
                play_sound("cancel.ogg")
                self.quit=False
                fade_out()

class ChallengeMessage(TMessage):
        def __init__(self, sock, incoming, challenger):
                if incoming:
                        super().__init__(challenger+" has challenged\nyou to a match!\nZ - Accept  X - Don't")
                else:
                        super().__init__("Waiting for "+challenger+"...")
                self.sock = sock
                self.mode = incoming
                self.name = challenger

        def run(self):
                if self.quit:
                        return
                global bgoffset
                self.drawUI()
                self.draw()
                fade_in()
                while not self.quit:
                        self.draw()
                        pygame.display.flip()
                        if self.sock.readable():
                                try:
                                        msg=self.sock.receive()
                                except ConnectionError as e:
                                        TMessage("The connection\nwas interrupted").run()
                                        return e
                                print(msg)
                                if msg=='recanted':
                                        play_sound("cancel.ogg")
                                        fade_out()
                                        TempMessage(self.name+" withdrew").run()
                                        return msg
                                elif msg=='rejected' and not self.mode:
                                        play_sound("cancel.ogg")
                                        fade_out()
                                        TempMessage(self.name+" rejected\nyour challenge.").run()
                                        return False
                                elif msg=='accepted' and not self.mode:
                                        play_sound("ok.ogg")
                                        fade_out()
                                        TempMessage(self.name+" accepted\nyour challenge").run()
                                        return True

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.sock.close()
                                        fade_out()
                                        pygame.quit()
                                        sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                        if self.mode:
                                                self.handle_key(pygame.key.name(event.key))
                                        else:
                                                self.quit=True
                                                self.sock.send("recant")

                        dont_burn_my_cpu.tick(60)
                if self.yn:
                        play_sound("ok.ogg")
                else:
                        play_sound("cancel.ogg")
                fade_out()
                return self.yn

class P2Mngr(TMessage):
        def __init__(self, sock, ename):
                self.sock=sock
                self.wins=0
                self.ewins=0
                self.ename=ename
                self.quit=False
                self.ready=False

        def drawUI(self):
                self.UI=pygame.Surface((config['cell_size']*12, config['cell_size']*6))
                self.UI.fill((255,255,255))
                draw_matrix([[17,0,17,0,17],[0],[17,0,17,0,17]], (5.5, 0.5), self.UI)
                for x in range(self.wins):
                        draw_matrix([[16]], (5.5+x*2, 0.5), self.UI)
                for x in range(self.ewins):
                        draw_matrix([[16]], (5.5+x*2, 2.5), self.UI)
                draw_text(saveFile, (0.5, 0.5), self.UI)
                draw_text(self.ename, (0.5, 2.5), self.UI)
                if self.wins>2:
                        if self.ewins:
                                draw_text("You win!", (4, 5), self.UI)
                        else:
                                draw_text("Flawless victory!", (1.5, 5), self.UI)
                elif self.ewins>2:
                        if self.wins:
                                draw_text("You lose...", (3.25, 5), self.UI)
                        else:
                                draw_text("You stink!", (3.5, 5), self.UI)
                elif self.ready:
                        draw_text("Waiting on opponent...", (0.5, 5), self.UI)
                else:
                        draw_text("Press Z when ready...", (0.75, 5), self.UI)

        def draw(self):
                display.blit(bgscroll, (bgoffset, bgoffset))
                display.blit(self.UI, (4*config['cell_size'], 6*config['cell_size']))

        def run(self):
                global bgoffset
                self.drawUI()
                self.draw()
                fade_in()
                while not self.quit:
                        pygame.display.flip()
                        if self.sock.readable():
                                try:
                                        data=self.sock.receive()
                                except ConnectionError:
                                        self.quit=True
                                        break
                                if data=='openthegame':
                                        fade_out()
                                        game=P2Game(self.sock)
                                        game.run()
                                        if game.quit=='withdraw':
                                                fade_out()
                                                TempMessage("For shame!\nYou withdrew").run()
                                                return
                                        elif game.quit=='ewithdrew':
                                                fade_out()
                                                TempMessage(self.ename+" withdrew").run()
                                                return
                                        elif isinstance(game.quit, ConnectionError):
                                                fade_out()
                                                TempMessage("Lost connection\nto the server").run()
                                                self.quit=e
                                                return
                                        elif game.quit=='gameover':
                                                self.ewins+=1
                                        else:
                                                self.wins+=1
                                        self.ready=False
                                        self.drawUI()
                                        self.draw()
                                        if self.wins>2:
                                                pygame.mixer.music.load("music"+os.sep+"win_intro.ogg")
                                                pygame.mixer.music.set_volume(_mus_vol/100)
                                                pygame.mixer.music.play(0)
                                                pygame.mixer.music.set_endevent(pygame.USEREVENT+4)
                                        elif self.ewins>2:
                                                pygame.mixer.music.load("music"+os.sep+"loss_intro.ogg")
                                                pygame.mixer.music.set_volume(_mus_vol/100)
                                                pygame.mixer.music.play(0)
                                                pygame.mixer.music.set_endevent(pygame.USEREVENT+4)
                                        else:
                                                play_sound("star.ogg")
                                        del game
                                        fade_in()
                                elif data=='withdraw':
                                        fade_out()
                                        TempMessage(self.ename+" withdrew").run()
                                        return

                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.sock.send('withdraw')
                                        self.sock.close()
                                        fade_out()
                                        pygame.quit()
                                        sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                        if self.wins>2 or self.ewins>2:
                                                self.quit=True
                                        elif event.key==pygame.K_z:
                                                self.ready=True
                                                play_sound("ok.ogg")
                                                self.sock.send('ready')
                                                self.drawUI()
                                elif event.type == pygame.USEREVENT+4:
                                        if self.wins>2:
                                                play_song("win.ogg")
                                        else:
                                                play_song("loss.ogg")
                                                
                        dont_burn_my_cpu.tick(60)
                        self.draw()
                play_sound("ok.ogg")
                fade_out()
                pygame.mixer.music.fadeout(1000)

class P2Game(TetrisTimed):
        def __init__(self, sock, level=0):
                self.sock = sock
                self.incoming = 0
                super().__init__(level)
                self.elvl = 0
                self.incol = random.randint(0,9)
                
        def remove_rows(self, rows):
                if len(rows)>3:
                        self.sock.send("clear "+str(len(rows)+self.incoming))
                elif len(rows):
                        self.sock.send("clear "+str(len(rows)-1+self.incoming))
                if self.incoming:
                        self.incol = random.randint(0,9)
                        self.incoming=0
                super().remove_rows(rows)

        def new_stone(self):
                for x in range(len(self.board)):
                        if any(self.board[x]):
                                self.sock.send("height "+str(19-x))
                                break
                self.stone=self.next_stone.pop(0)
                self.next_stone.append(random.choice(tetris_shapes))
                while self.next_stone[0]==self.next_stone[1]==self.stone:
                        self.next_stone[1]=random.choice(tetris_shapes)
                self.stone_x = int(10 / 2 - len(self.stone[0])/2)
                self.stone_y = 1
                self.rot_center=[0,1,1,1]
                self.dropdelay = 15 + self.speed
                if self.stone==tetris_shapes[5]:
                        self.rot_center[2]=0
                for _ in range(self.incoming):
                        new = [2 for _ in range(10)]
                        new[self.incol] = 0
                        self.board.append(new)
                        del self.board[0]
                if self.incoming:
                        play_sound("incominglines.ogg")
                        self.incoming=0
                if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                        self.sock.send("gameover")
                        self.quit='gameover'
                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                        for x in range(5):
                                if (x % 2)==1:
                                        draw_matrix(self.stone, (self.stone_x, self.stone_y-1), self.screen)
                                else:
                                        self.screen.fill((200,0,0))
                                        draw_matrix(self.board, (0,-1), self.screen)
                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.4)
                        pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(17, -1, -1):
                                draw_matrix([[4 for _ in range(10)]], (0, x), self.screen)
                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                time.sleep(0.02)
                        time.sleep(0.4)
                        self.screen.fill((0,0,0))
                        self.center_msg("Game Over!")
                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                        time.sleep(2)

        def drop(self, si=False):
                if (not (self.quit or self.paused)) and self.dropdelay < self.speed:
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
                                        if all(self.board[i]) and 14 not in self.board[i]:
                                                rows.append(i)
                                if len(rows)>0:
                                        self.lines+=len(rows)
                                        self.screen.fill(self.bgcolor)
                                        draw_matrix(self.board, (0,-1), self.screen)
                                        self.remove_rows(rows)
                                        if self.lines>10*(self.level+1):
                                                self.level_up()
                                self.new_stone()

        def draw(self):
                super().draw()
                draw_matrix([[4] for _ in range(self.elvl)], (0, 18-self.elvl), display)

        def run(self):
                global bgoffset, _song
                key_actions = {
                        pygame.K_LEFT:  lambda:self.move(-1),
                        pygame.K_RIGHT: lambda:self.move(+1),
                        pygame.K_DOWN:  lambda:self.drop(True),
                        pygame.K_z:     lambda:self.rotate_stone(-1),
                        pygame.K_x:     lambda:self.rotate_stone(+1),
                        pygame.K_F12:   screenshot
                }

                self.paused = False
                self.fade=()
                debounce = dict.fromkeys(key_actions, False)
                
                self.drawUI()
                self.draw()
                _song=None
                play_song("2player.ogg")
                fade_in()
                while not self.quit:
                        self.draw()
                        pygame.display.flip()
                        if self.fade:
                                self.fade[0]=self.fade[0]+1
                                self.bgcolor=[x + (((y-x)/30)*self.fade[0]) for x,y in zip(self.fade[1], self.fade[2])]
                                if self.fade[0]==30:
                                        self.bgcolor=self.fade[2]
                                        self.fade=()
                        if self.dropdelay:
                                self.dropdelay -= 1
                        else:
                                self.drop()
                                self.dropdelay = self.speed
                        self.timer+=1

                        if self.sock.readable():
                                try:
                                        msg=self.sock.receive()
                                except ConnectionError as e:
                                        TMessage("The connection\nwas interrupted").run()
                                        self.quit = e
                                        return
                                print(msg)
                                if msg=='gameover':
                                        pygame.time.set_timer(pygame.USEREVENT+3, 0)
                                        play_sound("timeup.ogg")
                                        self.bgcolor=bg_colors[2]
                                        self.next_stone=[[[]], [[]]]
                                        self.draw()
                                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(1)
                                        pygame.mixer.music.stop()
                                        play_sound("gameover.ogg")
                                        for x in range(17, -1, -1):
                                                draw_matrix([[1 for _ in range(10)]], (0, x), self.screen)
                                                pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                                time.sleep(0.02)
                                        time.sleep(0.4)
                                        self.screen.fill((0,0,0))
                                        self.center_msg("Cleared!")
                                        pygame.display.update(pygame.Rect(2*config['cell_size'], 0, 10*config['cell_size'], 18*config['cell_size']))
                                        time.sleep(2)
                                        self.quit=True
                                elif msg[:7]=='height ':
                                        self.elvl=int(msg[7:])
                                elif msg[:6]=='lines ':
                                        self.incoming += int(msg[6:])
                                        if self.incoming>3:
                                                play_sound("siren3.ogg")
                                        elif self.incoming:
                                                play_sound("siren.ogg")
                                elif msg=='withdraw':
                                        self.quit='ewithdrew'
                                        return
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
                                elif event.type == pygame.QUIT:
                                        self.sock.send('withdraw')
                                        self.quit='withdraw'
                                elif event.type == pygame.KEYDOWN and event.key in key_actions and not debounce[event.key]:
                                        if not (273 < event.key < 277):
                                                debounce[event.key] = True
                                        key_actions[event.key]()
                                elif event.type == pygame.KEYUP and event.key in key_actions:
                                        debounce[event.key] = False
                                        
                        dont_burn_my_cpu.tick(60)
                fade_out()

if __name__=="__main__":                        
        pygame.init()
        pygame.mixer.init()
        display = pygame.display.set_mode((config['cell_size']*20, config['cell_size']*18))
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
        tiles.insert(15, pygame.Surface((config['cell_size'],config['cell_size'])))
        tiles[15].fill((193, 221, 243))
        temp = pygame.Surface((config['cell_size']*2, config['cell_size']*2))
        temp.fill((255,255,255))
        temp.blit(tiles[16], (0,0))
        temp.blit(pygame.transform.flip(tiles[16], True, False), (config['cell_size']*7/8,0))
        temp.blit(tiles[19], (0,config['cell_size']))
        temp.blit(pygame.transform.flip(tiles[19], True, False), (config['cell_size']*7/8,config['cell_size']))
        tiles[16]=temp
        del tiles[19]
        temp = pygame.Surface((config['cell_size']*2, config['cell_size']*2))
        temp.fill((255,255,255))
        temp.blit(pygame.transform.flip(tiles[17], True, False), (0,0))
        temp.blit(tiles[17], (config['cell_size']*7/8,0))
        temp.blit(pygame.transform.flip(tiles[19], True, False), (0,config['cell_size']))
        temp.blit(tiles[19], (config['cell_size']*7/8,config['cell_size']))
        tiles[17]=temp
        del tiles[19]

        pygame.key.set_repeat(200, 33)
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
        bgscroll.fill((17,83,18))
        temp = pygame.Surface((config['cell_size'],config['cell_size']))
        temp.fill((135, 168, 123))
        for y in range(19):
                for x in range(21):
                        if (x+y) % 2:
                                bgscroll.blit(temp, (x*config['cell_size'], y*config['cell_size']))
        del temp
        bgoffset=0
        dont_burn_my_cpu = pygame.time.Clock()
        MarathonLevel = TLevelSelect((TetrisApp, "LVL"), title="Marathon")
        UltraLevel = TLevelSelect((TetrisTimed, "LVL", 10800), title="Time Attack")
        LinesLevel = TLevelSelect((TetrisTimed, "LVL", 0, 40, "HIGH"), 9, (0, 2, 4, 6, 8, 10), "40 Lines")
        onePMode = TetrisMenu(["Marathon", "Time Attack", "40 Lines"], [MarathonLevel, UltraLevel, LinesLevel])
        menu = TetrisMenu(["1 Player", "2P Test", "Options", "Scorecard"], [onePMode, ServerMenu, TOptionsMenu(), TPlayerCard()], saveFile)
        pygame.mixer.music.load("music"+os.sep+"menu_intro.ogg")
        pygame.mixer.music.set_volume(_mus_vol/100)
        pygame.mixer.music.play(0)
        pygame.mixer.music.set_endevent(pygame.USEREVENT+4)
        TFileSelect([x for x in os.listdir("saves")], menu).run()
        pygame.quit()
