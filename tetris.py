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
        'maxfps':       30
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

def rotate_clockwise(shape):
        if shape==tetris_shapes[6]:
                return shape
        return [ [ shape[y][x]
                        for y in range(len(shape)) ]
                for x in range(len(shape[0])-1, -1, -1) ]

def rotate_counter(shape):
        if shape==tetris_shapes[6]:
                return shape
        return [ [ shape[y][x]
                        for y in range(len(shape)-1, -1, -1) ]
                for x in range(len(shape[0])) ]

def check_collision(board, shape, offset):
        off_x, off_y = offset
        for cy, row in enumerate(shape):
                for cx, cell in enumerate(row):
                        try:
                                if cell and board[ cy + off_y ][ cx + off_x ]:
                                        return True
                        except IndexError:
                                return True
        return False

def remove_row(board, row, draw):
        del board[row]
        return [[0 for i in range(config['cols'])]] + board
        
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
                pygame.key.set_repeat(250,25)
                self.width = config['cell_size']*config['cols']
                self.height = config['cell_size']*config['rows']
                
                self.screen = pygame.display.set_mode((self.width, self.height))
                pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
                                                             # mouse movement
                                                             # events, so we
                                                             # block them.
                self.init_game()
        
        def new_stone(self):
                self.stone = tetris_shapes[rand(len(tetris_shapes))]
                self.stone_x = int(config['cols'] / 2 - len(self.stone[0])/2)
                self.stone_y = 0
                
                if check_collision(self.board,
                                   self.stone,
                                   (self.stone_x, self.stone_y)):
                        self.gameover = True
                        time.sleep(2)
                        pygame.mixer.music.stop()
                        play_sound("gameover.ogg")
        
        def init_game(self):
                self.board = new_board()
                self.new_stone()
                pygame.mixer.music.play(-1)
        
        def center_msg(self, msg):
                for i, line in enumerate(msg.splitlines()):
                        msg_image =  pygame.font.Font(
                                pygame.font.get_default_font(), 12).render(
                                        line, False, (255,255,255), (0,0,0))
                
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
                                                        (off_x+x) *
                                                          config['cell_size'],
                                                        (off_y+y) *
                                                          config['cell_size'], 
                                                        config['cell_size'],
                                                        config['cell_size']),0)
        
        def move(self, delta_x):
                if not self.gameover and not self.paused:
                        new_x = self.stone_x + delta_x
                        if new_x < 0:
                                new_x = 0
                        if new_x > config['cols'] - len(self.stone[0]):
                                new_x = config['cols'] - len(self.stone[0])
                        if not check_collision(self.board,
                                               self.stone,
                                               (new_x, self.stone_y)):
                                self.stone_x = new_x
        def quit(self):
                self.center_msg("Exiting...")
                pygame.display.update()
                pygame.quit()
                sys.exit()
        
        def drop(self):
                if not self.gameover and not self.paused:
                        self.stone_y += 1
                        if check_collision(self.board,
                                           self.stone,
                                           (self.stone_x, self.stone_y)):
                                self.board = join_matrixes(
                                  self.board,
                                  self.stone,
                                  (self.stone_x, self.stone_y))
                                play_sound("drop.ogg")
                                self.new_stone()
                                if self.gameover:
                                        return
                                for x in self.board[4]:
                                        if x!=0:
                                                play_sound("siren.ogg")
                                                break
                                times=0
                                while True:
                                        for i, row in enumerate(self.board[:-1]):
                                                if 0 not in row:
                                                        self.board = remove_row(
                                                          self.board, i, self.draw_matrix)
                                                        times+=1
                                                        break
                                        else:
                                                break
                                if times>3:
                                        play_sound("4lines.ogg")
                                elif times>0:
                                        play_sound("line.ogg")
        
        def rotate_stone(self, direct):
                if not self.gameover and not self.paused:
                        new_stone = None
                        if direct==1:
                                new_stone = rotate_clockwise(self.stone)
                        else:
                                new_stone = rotate_counter(self.stone)
                        if not check_collision(self.board,
                                               new_stone,
                                               (self.stone_x, self.stone_y)):
                                self.stone = new_stone
                                play_sound("Rotate.ogg")
        
        def toggle_pause(self):
                play_sound("pause.ogg")
                self.paused = not self.paused
                if self.paused:
                        pygame.mixer.music.pause()
                else:
                        pygame.mixer.music.unpause()
        
        def start_game(self):
                if self.gameover:
                        self.init_game()
                        self.gameover = False
        
        def run(self):
                key_actions = {
                        'ESCAPE':       self.quit,
                        'LEFT':         lambda:self.move(-1),
                        'RIGHT':        lambda:self.move(+1),
                        'DOWN':         self.drop,
                        'z':            lambda:self.rotate_stone(-1),
                        'x':            lambda:self.rotate_stone(+1),
                        'p':            self.toggle_pause,
                        'SPACE':        self.start_game
                }
                
                self.gameover = False
                self.paused = False
                
                pygame.time.set_timer(pygame.USEREVENT+1, config['delay'])
                dont_burn_my_cpu = pygame.time.Clock()
                while 1:
                        self.screen.fill((0,0,0))
                        if self.gameover:
                                self.center_msg("""Game Over!
Press space to continue""")
                        else:
                                if self.paused:
                                        self.center_msg("Paused")
                                else:
                                        self.draw_matrix(self.board, (0,0))
                                        self.draw_matrix(self.stone,
                                                         (self.stone_x,
                                                          self.stone_y))
                        pygame.display.update()
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+1:
                                        self.drop()
                                elif event.type == pygame.QUIT:
                                        self.quit()
                                elif event.type == pygame.KEYDOWN:
                                        for key in key_actions:
                                                if event.key == eval("pygame.K_"
                                                +key):
                                                        key_actions[key]()
                                        
                        dont_burn_my_cpu.tick(config['maxfps'])

sound_library={}
def play_sound(path):
        global sound_library
        sound=sound_library.get(path)
        if sound is None:
                path.replace('/', os.sep).replace('\\', os.sep)
                sound=pygame.mixer.Sound(path)
                sound_library[path]=sound
        sound.play()

if __name__ == '__main__':
        pygame.mixer.init()
        pygame.mixer.music.load("Tetris.ogg")
        App = TetrisApp()
        App.run()
