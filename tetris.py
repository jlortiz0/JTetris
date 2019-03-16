#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Very simple tetris implementation
# 
# Control keys:
# Down - Drop stone faster
# Left/Right - Move stone
# Up - Rotate Stone clockwise
# Escape - Quit game
# P - Pause game
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

from random import randrange as rand
import pygame, sys, os, time

# The configuration
config = {
        'cell_size':    30,
        'cols':         10,
        'rows':         18,
        'delay':        750,
        'maxfps':       30,
        'music':        True,
        'sound':        True,
        'debug':        -1,
        'center':       False
}

colors = [
(0,   0,   0  ),
(255, 0,   0  ),
(0,   150, 0  ),
(0,   0,   255),
(255, 120, 0  ),
(255, 255, 0  ),
(180, 0,   255),
(0,   220, 220),
(255, 255, 255),
(153, 204, 255)
]

# Define the shapes of the single parts
tetris_shapes = [
        [[1, 1, 1],
         [0, 1, 0]],
        
        [[0, 2, 2],
         [2, 2, 0]],
        
        [[3, 3, 0],
         [0, 3, 3]],
        
        [[4, 4, 4],
         [4, 0, 0]],
        
        [[5, 5, 5],
         [0, 0, 5]],
        
        [[6, 6, 6, 6]],
        
        [[7, 7],
         [7, 7]]
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
        if not -1<off_x<config['cols']:
                return True
        for cy, row in enumerate(shape):
                for cx, cell in enumerate(row):
                        try:
                                #print(cx, cy, cell, board[cy+off_y][cx+off_x], off_y, off_x)
                                if cell and board[ cy + off_y ][ cx + off_x ]:
                                        return True
                        except IndexError:
                                return True
        return False

def remove_rows(board, rows, draw, screen):
        for x in range(4):
                for r in rows:
                        if (x % 2) == 0:
                                draw([[8 for i in range(config['cols'])]], (0, r))
                        else:
                                draw([board[r]], (0,r))
                pygame.display.update()
                time.sleep(0.2)
        for r in rows:
                del board[r]
                board = [[0 for i in range(config['cols'])]] + board
        return board
        
def join_matrixes(mat1, mat2, mat2_off):
        off_x, off_y = mat2_off
        for cy, row in enumerate(mat2):
                for cx, val in enumerate(row):
                        mat1[cy+off_y-1 ][cx+off_x] += val
        return mat1

def new_board():
        board = [ [ 0 for x in range(config['cols']) ]
                        for y in range(config['rows']) ]
        board += [[ 1 for x in range(config['cols'])]]
        return board

class TetrisApp(object):
        def __init__(self):
                pygame.init()
                if config['music']:
                        pygame.mixer.init()
                        self._song=""
                pygame.key.set_repeat(250,25)
                self.width = config['cell_size']*config['cols']
                self.height = config['cell_size']*config['rows']
                self.screen = pygame.display.set_mode((self.width, self.height))
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                self.init_game()
        
        def new_stone(self):
                if config['debug']==-1:
                        self.stone = tetris_shapes[rand(len(tetris_shapes))]
                else:
                        self.stone=tetris_shapes[config['debug']]
                self.stone_x = int(config['cols'] / 2 - len(self.stone[0])/2)
                self.stone_y = 0
                self.rot_center=[0,1,1,1]
                self.dropdelay = True
                pygame.time.set_timer(pygame.USEREVENT+2, 250)
                if self.stone==tetris_shapes[5]:
                        self.rot_center[2]=0
                if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                        pygame.display.update()
                        self.gameover = True
                        pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
                        for x in range(5):
                                if (x % 2)==0:
                                        self.draw_matrix(self.stone, (self.stone_x, self.stone_y))
                                else:
                                        self.screen.fill(self.bgcolor)
                                        self.draw_matrix(self.board, (0,0))
                                pygame.display.update()
                                time.sleep(0.4)
        
        def init_game(self):
                self.play_song("dxa1.ogg")
                self.board = new_board()
                self.new_stone()
                self.bgcolor=colors[0]
                self.lines=0
                self.level=0
                self.speed=config['delay']

        def level_up(self):
                self.level+=1
                play_sound("level.ogg")
                if self.level>29:
                        return
                self.speed-=24.7
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                if (self.level % 4)==0:
                        pass

        def play_song(self, song):
                if not config['music'] or self._song==song:
                        return
                self._song=song
                pygame.mixer.music.stop()
                pygame.mixer.music.load(song)
                pygame.mixer.music.play(-1)
        
        def center_msg(self, msg):
                for i, line in enumerate(msg.splitlines()):
                        msg_image =  pygame.font.Font("joystix.ttf", 18).render(line, False, (255,255,255), (0,0,0))
                        msgim_center_x, msgim_center_y = msg_image.get_size()
                        msgim_center_x //= 2
                        msgim_center_y //= 2
                
                        self.screen.blit(msg_image, (
                          self.width // 2-msgim_center_x,
                          self.height // 2-msgim_center_y+i*22))
        
        def draw_matrix(self, matrix, offset):
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        pygame.draw.rect(
                                                self.screen,
                                                colors[val],
                                                pygame.Rect(
                                                        (off_x+x) * config['cell_size'],
                                                        (off_y+y) * config['cell_size'], 
                                                        config['cell_size'],
                                                        config['cell_size']),0)
        
        def move(self, delta_x):
                if not self.gameover and not self.paused:
                        new_x = self.stone_x + delta_x
                        if new_x < 0:
                                new_x = 0
                        if new_x > config['cols'] - len(self.stone[0]):
                                new_x = config['cols'] - len(self.stone[0])
                        if not check_collision(self.board, self.stone,(new_x, self.stone_y)):
                                self.stone_x = new_x
        def quit(self):
                self.center_msg("Exiting...")
                pygame.display.update()
                pygame.quit()
                sys.exit()
        
        def drop(self):
                if not (self.gameover or self.paused or self.dropdelay):
                        self.stone_y += 1
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
                                if len(rows)>3:
                                        play_sound("4lines.ogg")
                                elif len(rows)>0:
                                        play_sound("line.ogg")
                                if len(rows)>0:
                                        if (self.lines % 10)+len(rows)>9:
                                                self.level_up()
                                        self.lines+=len(rows)
                                        self.screen.fill(self.bgcolor)
                                        self.draw_matrix(self.board, (0,0))
                                        self.board=remove_rows(self.board, rows, self.draw_matrix, self.screen)
                                for x in range(len(self.board)):
                                        if self.board[x]!=[0 for x in range(config['cols'])]:
                                                height=x
                                                break
                                if height<4:
                                        self.play_song("danger.ogg")
                                elif height<6:
                                        self.play_song("dxa3.ogg")
                                elif height<9:
                                        self.play_song("dxa2.ogg")
                                else:
                                        self.play_song("dxa1.ogg")
                                self.new_stone()
        
        def rotate_stone(self, direct):
                if not self.gameover and not self.paused:
                        if direct>0:
                                new_stone, center = rotate_clockwise(self.stone, self.rot_center.copy())
                        else:
                                new_stone, center = rotate_counter(self.stone, self.rot_center.copy())
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
                play_sound("pause.ogg")
                self.paused = not self.paused
                if self.paused:
                        pygame.mixer.music.pause()
                else:
                        pygame.mixer.music.unpause()
        
        def start_game(self):
                if self.gameover or self.paused:
                        self.init_game()
                        self.gameover = False
                        self.paused = False
        
        def run(self):
                key_actions = {
                        'ESCAPE':       self.quit,
                        'LEFT':         lambda:self.move(-1),
                        'RIGHT':        lambda:self.move(+1),
                        'DOWN':         self.drop,
                        'z':            lambda:self.rotate_stone(-1),
                        'x':            lambda:self.rotate_stone(+1),
                        'RETURN':       self.toggle_pause,
                        'SPACE':        self.start_game,
                        'y':            self.level_up
                }
                
                self.gameover = False
                self.paused = False
                
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                dont_burn_my_cpu = pygame.time.Clock()
                while 1:
                        self.screen.fill(self.bgcolor)
                        if self.gameover:
                                self.center_msg("Game Over!\nPress space\nto retry")
                        else:
                                if self.paused:
                                        self.center_msg("Paused")
                                else:
                                        self.draw_matrix(self.board, (0,0))
                                        self.draw_matrix(self.stone,
                                                         (self.stone_x,
                                                          self.stone_y))
                                        if config['center']:
                                                self.draw_matrix([[8]], (self.stone_x+self.rot_center[1], self.stone_y+self.rot_center[0]))
                                                self.draw_matrix([[9]], (self.stone_x+self.rot_center[3], self.stone_y+self.rot_center[2]))
                        pygame.display.update()
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+1:
                                        self.drop()
                                elif event.type == pygame.USEREVENT+2:
                                        self.dropdelay=False
                                        pygame.time.set_timer(pygame.USEREVENT+2, 0)
                                elif event.type == pygame.QUIT:
                                        self.quit()
                                elif event.type == pygame.KEYDOWN:
                                        for key in key_actions:
                                                if event.key == eval("pygame.K_"+key):
                                                        key_actions[key]()
                                        
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

if __name__ == '__main__':
        App = TetrisApp()
        App.run()
