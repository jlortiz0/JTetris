import pygame, sys

pygame.init()
pygame.key.set_repeat(250,25)
config = {
        'cell_size':    30,
        'cols':          5,
        'rows':          5
}
def draw_matrix(matrix, offset):
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        pygame.draw.rect(
                                                screen,
                                                colors[val],
                                                pygame.Rect(
                                                        (off_x+x) *
                                                          config['cell_size'],
                                                        (off_y+y) *
                                                          config['cell_size'], 
                                                        config['cell_size'],
                                                        config['cell_size']),0)

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

screen = pygame.display.set_mode((config['cell_size']*config['cols'], config['cell_size']*config['rows']))
pygame.event.set_blocked(pygame.MOUSEMOTION)

stone=tetris_shapes[0]
rot_center=[0,1,1,1]
cstone=0

def new_stone(direct):
    global stone, cstone, rot_center
    cstone+=direct
    if cstone<0:
        cstone+=len(tetris_shapes)
    elif cstone>=len(tetris_shapes):
        cstone-=len(tetris_shapes)
    rot_center=[0,1,1,1]
    if cstone==5:
        rot_center[2]=0
    stone=tetris_shapes[cstone]

def rotate_clockwise(shape):
        if shape==tetris_shapes[6]:
                return shape
        rot_center.insert(0, rot_center.pop())
        return [ [ shape[y][x]
                        for y in range(len(shape)) ]
                for x in range(len(shape[0])-1, -1, -1) ]

def rotate_counter(shape):
        if shape==tetris_shapes[6]:
                return shape
        rot_center.append(rot_center.pop(0))
        return [ [ shape[y][x]
                        for y in range(len(shape)-1, -1, -1) ]
                for x in range(len(shape[0])) ]

def rotate_stone(direct):
    global stone
    if direct>0:
        stone=rotate_clockwise(stone)
    else:
        stone=rotate_counter(stone)

def pquit():
    pygame.quit()
    sys.exit()
    
def run():
    key_actions = {
        'ESCAPE':pquit,
        'z':lambda:rotate_stone(-1),
        'x':lambda:rotate_stone(+1),
        'LEFT':lambda:new_stone(-1),
        'RIGHT':lambda:new_stone(+1)
    }
    while True:
        screen.fill((0,0,0))
        draw_matrix(stone, (0,0))
        draw_matrix([[8]], tuple(rot_center[:2][::-1]))
        draw_matrix([[9]], tuple(rot_center[2:][::-1]))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                for key in key_actions:
                    if event.key == eval("pygame.K_"+key):
                        key_actions[key]()
            elif event.type == pygame.QUIT:
                pquit()

if __name__=='__main__':
    run()
