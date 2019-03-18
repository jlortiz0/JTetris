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
        'cell_size':    32,
        'cols':         10,
        'rows':         18,
        'delay':        750,
        'maxfps':       30,
        'music':        True,
        'sound':        True,
        'debug':        -1
}

tiles = [None]

bg_colors = [
(255, 238, 0  ),
(255, 46,  230),
(80,  255, 232),
(47,  156, 49 ),
(153, 153, 153),
(0,   0,   0  ),
(36,  25,  179)
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
                                if cell and board[ cy + off_y ][ cx + off_x ]:
                                        return True
                        except IndexError:
                                return True
        return False

def remove_rows(board, rows, draw, screen):
        for x in range(4):
                for r in rows:
                        if (x % 2) == 0:
                                draw([[13 for i in range(config['cols'])]], (0, r))
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
        def __init__(self, off_x, off_y):
                pygame.init()
                if config['music']:
                        pygame.mixer.init()
                        self._song=""
                pygame.key.set_repeat(250,25)
                self.width = config['cell_size']*config['cols']
                self.height = config['cell_size']*config['rows']
                self.screen = display.subsurface(pygame.Rect(off_x, off_y, self.width, self.height))
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                self.off_x=off_x//config['cell_size']
                self.off_y=off_y//config['cell_size']
                self.init_game()
        
        def new_stone(self):
                if config['debug']==-1:
                        self.stone = self.next_stone
                        self.next_stone=tetris_shapes[rand(len(tetris_shapes))]
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
                        self.screen.fill((0,0,0))
        
        def init_game(self):
                self.play_song("dxa1.ogg")
                self.board = new_board()
                self.next_stone=tetris_shapes[rand(len(tetris_shapes))]
                self.new_stone()
                self.bgcolor=bg_colors[0]
                self.lines=0
                self.level=0
                self.speed=config['delay']
                pygame.time.set_timer(pygame.USEREVENT+1, self.speed)

        def level_up(self):
                self.level+=1
                play_sound("level.ogg")
                self.speed-=22
                if self.speed>0:
                        pygame.time.set_timer(pygame.USEREVENT+1, self.speed)
                if (self.level % 5)==0 and self.level/5<len(bg_colors)+1:
                        self.bgcolor=bg_colors[self.level//5]

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
        
        def draw_matrix(self, matrix, offset, screen=None):
                if not screen:
                        screen=self.screen
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        screen.blit(tiles[val],((off_x+x) * config['cell_size'],
                                                        (off_y+y) * config['cell_size'], 
                                                        ))
        
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
                                if height<3:
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
                bgscroll=pygame.Surface((config['cell_size']*(config['cols']+11), self.height+config['cell_size']))
                self.draw_matrix([ [ 15+((x+y)%2) for x in range(config['cols']+11) ] for y in range(config['rows']+config['cell_size'])
                        ], (0,0), bgscroll)
                bgoffset=0
                
                pygame.time.set_timer(pygame.USEREVENT+3, 100)
                dont_burn_my_cpu = pygame.time.Clock()
                while 1:
                        if self.gameover:
                                self.center_msg("Game Over!\nPress space\nto retry")
                        else:
                                if self.paused:
                                        self.center_msg("Paused")
                                else:
                                        display.blit(bgscroll, (bgoffset, bgoffset))
                                        self.draw_matrix([[13, 13, 13, 13, 13] for _ in range(5)], (self.off_x+config['cols']+2, self.off_y+2), display)
                                        self.draw_matrix(self.next_stone, (self.off_x+config['cols']+3, self.off_y+3), display)
                                        self.draw_matrix([[14] for _ in range(config['rows'])], (1,0), display)
                                        self.draw_matrix([[14] for _ in range(config['rows'])], (config['cols']+self.off_x,0), display)
                                        self.screen.fill(self.bgcolor)
                                        self.draw_matrix(self.board, (0,0))
                                        self.draw_matrix(self.stone,
                                                         (self.stone_x,
                                                          self.stone_y))
                        pygame.display.update()
                        
                        for event in pygame.event.get():
                                if event.type == pygame.USEREVENT+1:
                                        self.drop()
                                elif event.type == pygame.USEREVENT+2:
                                        self.dropdelay=False
                                        pygame.time.set_timer(pygame.USEREVENT+2, 0)
                                elif event.type == pygame.USEREVENT+3:
                                        bgoffset = (bgoffset-1) % -config['cell_size']
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
        display = pygame.display.set_mode((config['cell_size']*(config['cols']+10), config['cell_size']*config['rows']))
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
        tiles[15].fill((17, 83, 18))
        tiles.insert(16, pygame.Surface((config['cell_size'],config['cell_size'])))
        tiles[16].fill((135, 168, 123))
        if config['debug']>-1:
                for x in range(1, len(tiles)):
                        display.blit(tiles[x], (0, x*config['cell_size']))
                pygame.display.update()
                time.sleep(3)
        App = TetrisApp(config['cell_size']*2, 0)
        App.run()
