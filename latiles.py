import pygame, sys
from datetime import datetime

config = {
    'cell_size': 32,
    'height':    18,
    'width':     18
}

pygame.init()
display = pygame.display.set_mode((config['cell_size']*config['height'], config['cell_size']*config['width']))
pygame.event.set_blocked(pygame.MOUSEMOTION)
tiles=[pygame.Surface((config['cell_size'], config['cell_size']))]
tiles[0].fill((0,0,0))
tileset = pygame.image.load("latiles.png").convert()
for y in range(tileset.get_height()//16):
    for x in range(tileset.get_width()//16):
        tiles.append(pygame.transform.scale(tileset.subsurface((16*x, 16*y, 16, 16)), (config['cell_size'],config['cell_size'])))
del tileset

setting = [[0 for _ in range(config['width'])] for _ in range(config['height'])]
selx=0
sely=0
dont_burn_my_cpu = pygame.time.Clock()
cursor=tiles[0].copy()
pygame.draw.rect(cursor, (128,128,128), pygame.Rect(0,0,config['cell_size'],config['cell_size']), 4)
cursor.set_colorkey((0,0,0))
drawTiles = 0
while True:
    drawTiles = (drawTiles+1) % 4
    if (drawTiles % 2):
        for y in range(len(setting)):
            for x in range(len(setting[y])):
                display.blit(tiles[setting[y][x]], (x*config['cell_size'], y*config['cell_size']))
    else:
        display.blit(cursor, (selx*config['cell_size'], sely*config['cell_size']))
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        elif event.type == pygame.KEYDOWN:
                if event.key==pygame.K_F12:
                    display.blit(tiles[setting[sely][selx]], (selx*config['cell_size'], sely*config['cell_size']))
                    now = datetime.now()
                    pygame.image.save(display, "{}-{:02}-{:02}_{:02}-{:02}-{:02}.png".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
                key=pygame.key.name(event.key)
                if key=='escape':
                    pygame.quit()
                    sys.exit()
                elif key=='z':
                    setting[sely][selx] = (setting[sely][selx]+1) % len(tiles)
                elif key=='x':
                    setting[sely][selx] = (setting[sely][selx]-1) % len(tiles)
                elif key=='up':
                    sely = (sely-1) % config['height']
                elif key=='down':
                    sely = (sely+1) % config['height']
                elif key=='left':
                    selx = (selx-1) % config['width']
                elif key=='right':
                    selx = (selx+1) % config['width']
                elif key=='f':
                    temp=setting[sely][selx]
                    setting = [[temp for _ in range(config['width'])] for _ in range(config['height'])]
                elif key=='w':
                    setting[sely-1 % config['height']][selx]=setting[sely][selx]
                elif key=='s':
                    setting[sely+1 % config['height']][selx]=setting[sely][selx]
                elif key=='a':
                    setting[sely][selx-1 % config['width']]=setting[sely][selx]
                elif key=='d':
                    setting[sely][selx+1 % config['width']]=setting[sely][selx]
                    
    dont_burn_my_cpu.tick(15)
                    
