import pygame
import os
import random
import math

os.environ['SDL_VIDEO_WINDOW_POS'] = "300,30"                  # set window position

pygame.init()

# colors
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
BLUE = (0,0,255)

WIDTH = 700
HEIGHT = 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))               # set window height
pygame.display.set_caption('Space Game')

clock = pygame.time.Clock()

ROCKET = pygame.image.load('rocketship.png').convert_alpha()    # convert_alpha converts to correct pixel format for optimization
ROCKET = pygame.transform.scale(ROCKET, (30, 45))

UFO = pygame.image.load('ufo.png').convert_alpha()
UFO = pygame.transform.scale(UFO, (72, 45))

HEART = pygame.image.load('heart.png').convert_alpha()
HEART = pygame.transform.scale(HEART, (25, 25))

SHIELD = pygame.Surface([60, 60], pygame.SRCALPHA)
pygame.draw.circle(SHIELD, (0, 0, 255, 128), (30, 30), 30)

global level
level = 1

# change in time
dt = 0

# score
global score
score = 0

# misc?
powerups = ['heart', 'atkrate', 'explosion', 'rapidfire', 'supershield']    # explosion in progress, last one not done
angle = math.pi / 6
global exploding
global explodingRadius
exploding = False
explodingRadius = 0


class Ufo(pygame.sprite.Sprite):
    #variables in class belong here

    def __init__(self, pos, type):
        #variables to instance belong here
        super().__init__()
        self.type = type
        self.image = UFO
        self.rect = self.image.get_rect(center=pos)
        self.maxhorizontal = random.randrange(self.rect.x+1, WIDTH-36)
        self.direction = 1               # right side
        self.health = 3
        self.iframes = 0                 # invincibility frames
        self.speedDivisor = random.randrange(1, min(level, 5)+1)
        self.speed = max(1, random.randrange(1, min(level, 5)+1) / random.randrange(1, self.speedDivisor+1))
        self.reload_time = random.randrange(1000, 4000, 1000)          # milliseconds

    def update(self):
        if self.direction == 1:
            if self.rect.x < self.maxhorizontal:
                self.rect.x += self.speed
            else:
                self.maxhorizontal = random.randrange(36, self.rect.x+1)
                self.direction = 0
        else:
            if self.rect.x > self.maxhorizontal:
                self.rect.x -= self.speed
            else:
                self.maxhorizontal = random.randrange(max(self.rect.x, 36), WIDTH-36)
                self.direction = 1
        if self.iframes == 10:
            self.image = pygame.Surface([30,45])
        if self.iframes > 0:
            self.iframes -= 1
        elif self.iframes == 0:
            self.image = UFO


class Player(pygame.sprite.Sprite):

    def __init__(self, pos):
        super().__init__()                                        # call sprite constructor
        self.image = ROCKET
        self.rect = self.image.get_rect(center=pos)
        self.health = 5
        self.iframes = 0
        self.reload_time = 0         # milliseconds
        self.max_reload = 1000
        self.powerup = 0
        self.powerup_time = 0
        self.temp_max_reload = 80

    def update(self):
        if self.iframes > 0:
            self.iframes -= 1
            self.image = SHIELD
            self.image.blit(ROCKET, (15, 8))
        elif self.iframes == 0:
            self.image = ROCKET


class Bullet(pygame.sprite.Sprite):

    def __init__(self, pos, color, type, dx, dy):
        super().__init__()
        self.health = 1
        self.type = type
        self.dx = dx
        self.dy = dy
        if type == 'square':
            self.image = pygame.Surface([4, 10])
            self.rect = self.image.get_rect(center=pos)
            self.image.fill(color)
            self.speed = -7
        elif type == 'orb':
            orb = pygame.Surface([10,10], pygame.SRCALPHA)
            pygame.draw.circle(orb, color, (5, 5), 5)
            self.image = orb
            self.rect = self.image.get_rect(center=pos)
            self.speed = -5

    def update(self):
        self.rect.y += self.speed * self.dy
        self.rect.x += self.speed * self.dx


class Consumable(pygame.sprite.Sprite):
    def __init__(self, pos, powertype):
        super().__init__()
        self.powertype = powertype
        if powertype == 'heart':
            self.image = HEART
            self.rect = self.image.get_rect(center=pos)
        elif powertype == 'atkrate':
            self.image = pygame.Surface([15, 15])
            self.image.fill(BLUE)
            self.rect = self.image.get_rect(center=pos)
        elif powertype == 'rapidfire':
            orb = pygame.Surface([20, 20], pygame.SRCALPHA)
            pygame.draw.circle(orb, BLUE, (10, 10), 10)
            self.image = orb
            self.rect = self.image.get_rect(center=pos)
        self.health = 1


# temp not in use
def explosion():
    global exploding
    global explodingRadius
    if explodingRadius <= max(WIDTH, HEIGHT):
        explodingRadius += 10
    else:
        exploding = False
        explodingRadius = 0
        for ufo in enemy_list:
            ufo.health = 0
            checkDeath(ufo)


def outOfBounds(object):
    if (object.rect.x < 0) or (object.rect.y < 0) or (object.rect.x > WIDTH) or (object.rect.y > HEIGHT):
        return True
    else:
        return False


def checkDeath(object):
    global score
    if object.health == 0:
        if type(object) == Ufo:
            score += 400
        if type(object) == Consumable:
            score += 300
        object.kill()
        del object


def checkCollision(group1, group2):
    for object in group1:
        collided = pygame.sprite.spritecollide(object, group2, False)
        if len(collided) > 0:
            if type(object) == Bullet:
                object.health -= 1
                checkDeath(object)
            elif type(object) == Player:
                if type(collided[0]) != Consumable:
                    if object.iframes == 0:
                        object.health -= 1
                        object.iframes = 300
        for item in collided:
            item.health -= 1
            if type(item) == Ufo:
                item.iframes = 10
            elif type(item) == Consumable:
                if item.powertype == 'heart':
                    player.health += 1
                elif item.powertype == 'atkrate':
                    player.max_reload = player.max_reload / 2
                elif item.powertype == 'rapidfire':
                    player.powerup += 1
            checkDeath(item)


def updateLevel():
    global level
    level += 1
    for powerup in powerups_list:
        powerup.health = 0
        checkDeath(powerup)
    if level == 4:
        ufo = Ufo((random.randrange(36, WIDTH-36), random.randrange(50, int(HEIGHT/2))), 'spread')
        sprites_list.add(ufo)
        enemy_list.add(ufo)
    if level > 5:
        temp = level
        while temp > 0:
            temp -= 1
            heads = random.randrange(0, 2)
            if heads == 1:
                ufo = Ufo((random.randrange(36, WIDTH - 36), random.randrange(50, int(HEIGHT / 2))), 'spread')
                sprites_list.add(ufo)
                enemy_list.add(ufo)
    if level % 5 == 0:
        temp = level
        while temp != 0:
            temp = temp - 5
            ufo = Ufo((random.randrange(36, WIDTH-36), random.randrange(50, int(HEIGHT/2))), 'orb')
            sprites_list.add(ufo)
            enemy_list.add(ufo)
    if level % 5 == 0: #and player.health < 6
        powerup = Consumable((random.randrange(50, WIDTH - 50), random.randrange(100, HEIGHT - 50)), 'heart')
        powerups_list.add(powerup)
        sprites_list.add(powerup)
    if level == 3 or level == 7 or level == 13:
        powerup = Consumable((random.randrange(50, WIDTH - 50), random.randrange(100, HEIGHT - 50)), 'atkrate')
        powerups_list.add(powerup)
        sprites_list.add(powerup)
    if level % 4 == 0:
        powerup = Consumable((random.randrange(50, WIDTH - 50), random.randrange(100, HEIGHT - 50)), 'rapidfire')
        powerups_list.add(powerup)
        sprites_list.add(powerup)
        if player.health <= 3:
            powerup = Consumable((random.randrange(50, WIDTH - 50), random.randrange(100, HEIGHT - 50)), 'heart')
            powerups_list.add(powerup)
            sprites_list.add(powerup)
    for x in range(random.randrange(1, min(level, 12)+1)):
        ufo = Ufo((random.randrange(36, WIDTH-36), random.randrange(50, int(HEIGHT/2))), 'straight')
        sprites_list.add(ufo)
        enemy_list.add(ufo)


sprites_list = pygame.sprite.Group()
enemy_list = pygame.sprite.Group()
bluebullet_list = pygame.sprite.Group()
redbullet_list = pygame.sprite.Group()
bullet_list = pygame.sprite.Group()
powerups_list = pygame.sprite.Group()

# initial game state
player = Player((WIDTH/2, HEIGHT-50))
sprites_list.add(player)
ufo = Ufo((random.randrange(36, WIDTH-36), random.randrange(50, int(HEIGHT/2))), 'straight')
sprites_list.add(ufo)
enemy_list.add(ufo)
playerlist = [player]

# game over stuff
defaultfont = pygame.font.SysFont('comic_sans', 21)
gameoverfont = pygame.font.SysFont('comic_sans', 64)
endtext = gameoverfont.render('GAME OVER', True, WHITE)
endtext2 = defaultfont.render('To play again,press [ J ]', True, WHITE)
textRect = endtext.get_rect(center=(WIDTH/2, HEIGHT/2))
textRect2 = endtext2.get_rect(center=(WIDTH/2, HEIGHT/2))

running = True
game_start = True
while (running):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if player.health > 0 and player.powerup > 0:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.powerup_time <= 0:
                    player.powerup -= 1
                    player.powerup_time = 3000
                    player.iframes = 300
                    # following was an explosion powerup attempt
#                    exploding = True
#                    radius = 1
        if player.health == 0:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j:
                    player.health = 5
                    player.rect.x = WIDTH/2
                    player.rect.y = HEIGHT-50
                    player.iframes = 300
                    player.max_reload = 1000
                    player.powerup = 0
                    for ufo in enemy_list:
                        ufo.health = 0
                        checkDeath(ufo)
                    score = 0
                    level = 0
    if player.health > 0:
        keys = pygame.key.get_pressed()             # checking pressed keys
        if keys[pygame.K_UP] and (player.rect.y >= 5):
            player.rect.y -= 4
        if keys[pygame.K_LEFT] and (player.rect.x >= 5):
            player.rect.x -= 4
        if keys[pygame.K_DOWN] and (player.rect.y <= 655):
            player.rect.y += 4
        if keys[pygame.K_RIGHT] and (player.rect.x <= 670):
            player.rect.x += 4
        if player.reload_time <= 0:
            if player.powerup_time > 0:
                player.reload_time = player.temp_max_reload
                for value in range(2, 5):
                    x = math.cos(angle*value)
                    y = math.sin(angle*value)
                    bullet = Bullet(player.rect.midtop, BLUE, 'orb', x, y)
                    bluebullet_list.add(bullet)
                    bullet_list.add(bullet)
                    sprites_list.add(bullet)
            else:
                player.reload_time = player.max_reload
                bullet = Bullet((player.rect.x + 15, player.rect.y + 10), BLUE, 'square', 0, 1)
                bluebullet_list.add(bullet)
                bullet_list.add(bullet)
                sprites_list.add(bullet)
    player.reload_time -= dt
    player.powerup_time -= dt

    # ufo attack
    for ufo in enemy_list:
        if ufo.reload_time <= 0:
            if ufo.type == 'orb':
                ufo.reload_time = 1000
                for value in range(1, 13):
                    x = math.cos(angle*value)
                    y = math.sin(angle*value)
                    bullet = Bullet(ufo.rect.center, RED, 'orb', x, y)
                    redbullet_list.add(bullet)
                    bullet_list.add(bullet)
                    sprites_list.add(bullet)
            elif ufo.type == 'spread':
                ufo.reload_time = random.randrange(1000, 4000, 1000)
                for value in range(2, 5):
                    x = math.cos(angle*-value)
                    y = math.sin(angle*-value)
                    bullet = Bullet(ufo.rect.center, RED, 'orb', x, y)
                    redbullet_list.add(bullet)
                    bullet_list.add(bullet)
                    sprites_list.add(bullet)
            else:
                ufo.reload_time = random.randrange(1000, 4000, 1000)
                bullet = Bullet(ufo.rect.midbottom, RED, 'square', 0, -1)
                redbullet_list.add(bullet)
                bullet_list.add(bullet)
                sprites_list.add(bullet)
        else:
            ufo.reload_time -= dt

    for bullet in bullet_list:
        if outOfBounds(bullet):
            bullet.kill()
            del bullet

    checkCollision(bluebullet_list, enemy_list)
    #checkCollision(bluebullet_list, redbullet_list)
    checkCollision(playerlist, powerups_list)
    if player.iframes == 0 and player.health > 0:
        checkCollision(playerlist, enemy_list)
        checkCollision(playerlist, redbullet_list)
    if len(enemy_list.sprites()) == 0:
        updateLevel()
    screen.fill(BLACK)

    # calls update() method of sprites
    sprites_list.update()

    # requires each sprite to have a surface.image attr. and surface.rect
    sprites_list.draw(screen)                                       # draw can only be called by groups?

#    if exploding:
#        explosion()
#        explode = pygame.draw.circle(screen, BLUE, player.rect.center, explodingRadius)
#        pygame.display.update(explode)

    # game over
    if player.health <= 0:
        screen.blit(endtext, textRect)
        screen.blit(endtext2, (textRect2.x, textRect2.y+32))

    # stuff to display at top
    for x in range(player.health):
        screen.blit(HEART, (10+(x*30), 10))
    ability_text = defaultfont.render('ABILITIES: ' + str(player.powerup), True, WHITE)
    screen.blit(ability_text, (10, 40))
    score_text = defaultfont.render('SCORE: ' + str(score), True, WHITE)
    screen.blit(score_text, (WIDTH*3/4, 10))
    level_text = defaultfont.render('LEVEL: ' + str(level), True, WHITE)
    screen.blit(level_text, (WIDTH/2, 10))

    # clock.tick(60)  # limits to 60 fps
    # returns time that has passed since the last frame
    dt = clock.tick(60)          # /1000 for seconds

    pygame.display.flip()                                       # screen update

for sprite in sprites_list:                                     # double checking everything is deleted on exit I hope...
    sprite.kill()
    del sprite

pygame.quit()

