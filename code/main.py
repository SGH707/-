import pygame
import os
import random
import math
import time
import sys
from pygame.locals import *
import sqlite3 as s3

is_title_music_playing = False

# 현재 스크립트 파일의 위치를 기준으로 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'DB', 'rank.db')

# DB 폴더가 존재하지 않으면 생성
if not os.path.exists(os.path.join(BASE_DIR, "DB")):
    os.makedirs(os.path.join(BASE_DIR, "DB"))

# DB 연결
con = s3.connect(db_path)
cur = con.cursor()

# 테이블 생성
try:
    cur.execute("CREATE TABLE rank (id TEXT PRIMARY KEY, time REAL NOT NULL);")
except:
    pass

# 음악 파일 로드
title_music = "sounds/title.mp3"  # 시작화면 음악
stage_music = "sounds/stage12.mp3"  # 게임플레이 음악
die_music = "sounds/die.mp3"  # 게임 오버 음악
complete_music = "sounds/complete.mp3" # 게임 클리어 음악, 아직 미구현이라 넣지 않음
stage3_music = "sounds/stage3.mp3"

# 효과음 파일 경로
choice_sound= "sounds/choice.mp3"  # 버튼 클릭 효과음

# 충돌 효과음 파일 경로
hit_music = "sounds/hit.mp3"  # 충돌 효과음

# 아이템 획득 효과음 파일 경로
have_music = "sounds/have.mp3"  # 아이템 획득 효과음

FONT_PATH = "code/NanumGothic.ttf" # 한글 폰트 파일

# 전역 상태 변수
isDead = False  # 플레이어가 죽었는지 여부
is_title_music_playing = False
# 전역 변수로 게임 오버 음악 상태 관리
is_music_playing = False  # 음악 재생 상태를 관리
is_returned_from_instructions = False  # 게임 설명 화면에서 돌아왔는지 여부

FONT_PATH = "code/NanumGothic.ttf" # 한글 폰트 파일

pygame.init()


screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
#WIDTH, HEIGHT = screen.get_width(), screen.get_height()
WIDTH,HEIGHT = 1920, 1080
WORLD_WIDTH, WORLD_HEIGHT = 5000, 5000

GREEN = (34, 139, 34) # 색깔
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
play_time=0
screen = pygame.display.set_mode((WIDTH, HEIGHT)) #화면 해상도

pygame.display.set_caption('PROJECT : SURVOID') # 윈도우 창에 뜨는 게임제목

def reset_game():
    global is_title_music_playing, player, all_sprites, obstacles, bullets, enemies, bosses, items, boss_spawned
    global isDead, is_music_playing, start_time, is_boss_spawned, first_boss_spawn_time, first_boss_death_time, current_map, stage_level

    # 전역 변수들 초기화
    isDead = False
    is_title_music_playing = False
    is_music_playing = False
    is_boss_spawned = False
    first_boss_spawn_time = None
    first_boss_death_time = None
    boss_spawned = False
    current_map = 'plain_tile'
    stage_level = 1
    start_time = time.time()

    # 스프라이트 그룹 초기화
    all_sprites = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bosses = pygame.sprite.Group()
    items = pygame.sprite.Group()

    # 플레이어 초기화 및 스프라이트 그룹 추가
    player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
    all_sprites.add(player)

    # 장애물 생성
    for _ in range(0):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        obstacle = Obstacle(x, y)
        all_sprites.add(obstacle)
        obstacles.add(obstacle)

    for _ in range(70): #몬스터 생성
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        if not_mix_Player_other(x, y, player):
            enemy_type = random.choice(['bat', 'blob', 'skeleton'])
            enemy = Enemy(x, y, enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)

    for _ in range(5): #아이템 생성
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        item_type = random.choice(['bullet_speed', 'bullet_count'])
        item = Item(x, y, item_type)
        all_sprites.add(item)
        items.add(item)

# 효과음을 로드하는 함수
def play_sound(sound_path, volume = 0.5):
    """효과음을 재생하는 함수"""
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.set_volume(volume)  # 볼륨 설정
        sound.play()
    except pygame.error as e:
        print(f"효과음 재생 실패: {e}")

def draw_text(text, font, color, surface, x, y): # 시작화면 버튼 
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

# 시작화면
def start_screen():
    global start_time, is_returned_from_instructions, is_title_music_playing
    #타이틀 음악이 재생중이 아니면 로드 및 재생
    if not is_title_music_playing:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(title_music)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        is_title_music_playing = True

    #현재 창의 크기 (어떤해상도로 설정했는지 확인)
    current_width, current_height = screen.get_size()
    
    background_image = pygame.image.load("images/start_screen/start_screen.png")
    background_image = pygame.transform.scale(background_image, (current_width, current_height)) #현재 해상도에맞게 비율 전환
    screen.blit(background_image, (0, 0))
    
    #텍스트, 버튼크기 비율 설정(1920*1080을 기준)
    title_font_size = int(105 * (current_width / 1920))
    button_font_size = int(55 * (current_width / 1920))
    button_width = int(400 * (current_width / 1920))
    button_height = int(100 * (current_height / 1080))
    button_x = current_width // 2 - button_width // 2
    button_y_start = current_height // 2
    
    #타이틀 텍스트 중앙에 그리기
    button_font = pygame.font.Font(FONT_PATH, button_font_size)
    buttons = ['       시작', '   게임 설명', '       랭킹'] #버튼 텍스트
    button_rects = []

    for i, text in enumerate(buttons):
        button_rect = pygame.Rect(button_x, button_y_start + i * (button_height + 20), button_width, button_height)
        button_rects.append(button_rect)
        pygame.draw.rect(screen, GREEN, button_rect)
        draw_text(text, button_font, BLACK, screen, button_rect.x + 50, button_rect.y + 20)

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, button_rect in enumerate(button_rects):
                    if button_rect.collidepoint(mouse_pos):
                        play_sound(choice_sound)  # 버튼 클릭 효과음재생
                        if i == 0:  # 게임 시작
                            input_n()
                            reset_game()
                            waiting = False
                            pygame.mixer.music.stop()
                        elif i == 1:  # 게임 설명
                            show_instructions(screen)
                            return
                        elif i == 2:  # 랭킹
                            rank()
                            start_screen()
                            return


def input_n():  # 닉네임 입력 창
    global name
    # 색상 정의
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)

    # 글꼴 설정
    FONT_PATH = "code/NanumGothic.ttf"  # 실제 폰트 경로로 변경
    title_font = pygame.font.Font(FONT_PATH, 60)  # 안내문구 글꼴
    input_font = pygame.font.Font(FONT_PATH, 40)  # 입력 텍스트 글꼴

    # 입력받은 텍스트를 저장할 변수
    input_text = ""
    nope = ""

    # 화면 크기 및 중심 설정
    screen_width, screen_height = screen.get_size()
    center_x = screen_width // 2
    center_y = screen_height // 2

    # 메인 루프
    waiting = True
    pygame.key.set_text_input_rect(pygame.Rect(center_x - 150, center_y, 300, 50))  # 입력 필드 위치 설정
    pygame.key.start_text_input()  # 텍스트 입력 시작

    while waiting:
        # 화면 초기화
        screen.fill(BLACK)
        
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.TEXTINPUT:  # 텍스트 입력 이벤트
                input_text += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Enter 키를 누르면 입력 종료
                    name = input_text.strip()
                    if len(name) > 16:
                        nope = "닉네임이 너무 깁니다!"
                    elif not name:
                        nope = "닉네임을 입력해주세요!"
                    else:
                        print(f"최종 입력: {name}")
                        waiting = False
                elif event.key == pygame.K_BACKSPACE:  # 백스페이스로 텍스트 지우기
                    nope = ""
                    input_text = input_text[:-1]

        # 텍스트와 안내 문구 표시
        title_surface = title_font.render("닉네임을 입력하세요:", True, WHITE)
        input_surface = input_font.render(input_text, True, WHITE)
        nope_surface = input_font.render(nope, True, RED)  # 빨간색 오류 메시지

        # 화면에 그리기
        screen.blit(title_surface, (center_x - title_surface.get_width() // 2, center_y - 100))
        pygame.draw.rect(screen, WHITE, (center_x - 150, center_y, 300, 50), 2)  # 입력 칸 테두리
        screen.blit(input_surface, (center_x - 145, center_y + 5))  # 입력 텍스트 표시
        screen.blit(nope_surface, (center_x - nope_surface.get_width() // 2, center_y + 70))

        pygame.display.flip()  # 화면 업데이트

    pygame.key.stop_text_input()  # 텍스트 입력 종료

def rank():  # 랭킹
    global is_title_music_playing
    screen.fill(BLACK)
    waiting = True

    # 현재 창의 크기
    current_width, current_height = screen.get_size()

    # 글꼴 설정 (폰트 크기 비율 조정)
    font_size = int(40 * (current_width / 1920))
    font = pygame.font.Font(FONT_PATH, font_size)

    # 데이터베이스에서 랭킹 가져오기
    cur.execute('SELECT * FROM rank ORDER BY time;')
    count = 0
    li = []
    for i in cur:
        if count < 5:
            li.append(i)
            count += 1
        else:
            break

    rankli = []
    for i in range(5):
        try:
            rankli.append(f"{i + 1}위: {li[i][0]} - {li[i][1]}")
        except:
            pass

    # 랭킹 텍스트 표시 (해상도 비율에 따른 Y 오프셋 조정)
    y_offset = int(300 * (current_height / 1080))
    for line in rankli:
        instruction_text = font.render(line, True, WHITE)
        text_rect = instruction_text.get_rect(center=(current_width // 2, y_offset))  # 중앙 정렬
        screen.blit(instruction_text, text_rect)
        y_offset += int(70 * (current_height / 1080))

    # 돌아가기 안내문구
    instruction_text = font.render("엔터키를 눌러 돌아가기", True, WHITE)
    text_rect = instruction_text.get_rect(center=(current_width // 2, y_offset + int(140 * (current_height / 1080))))  # 중앙 정렬
    screen.blit(instruction_text, text_rect)

    pygame.display.update()

    # 음악 관리: title_music 중복 재생 방지
    if not is_title_music_playing:
        pygame.mixer.music.load(title_music)  # 배경음악 로드
        pygame.mixer.music.set_volume(0.5)  # 볼륨 설정
        pygame.mixer.music.play(-1)  # 반복 재생
        is_title_music_playing = True

    # 입력 대기 루프
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_RETURN:
                waiting = False


def show_instructions(screen):
    global is_returned_from_instructions

    # 현재 창의 크기
    current_width, current_height = screen.get_size()
    # 검정색 배경
    screen.fill(BLACK)
    # 글꼴 설정
    font_size = int(40 * (current_width / 1920))
    font = pygame.font.Font(FONT_PATH, font_size)
    # 설명 텍스트
    instructions = [
        "                   조작키 : W, A, S, D",
        "",
        "캐릭터가 향하는 방향으로 총알을 발사합니다.",
        "         보스를 물리치고 오래 살아남으세요!",
        "",
        "",  # 아이템 이미지가 들어갈 공간
        "",
        "",
        "",
        "",
        "   \' 엔터키를 입력하여 시작화면으로 이동\'"
    ]

    # 텍스트 표시 (해상도 비율에 따른 Y 오프셋 조정)
    y_offset = int(230 * (current_height / 1080))
    for line in instructions:
        instruction_text = font.render(line, True, WHITE)
        screen.blit(instruction_text, (int(600 * (current_width / 1920)), y_offset))
        y_offset += int(70 * (current_height / 1080))

    # 아이템 이미지 로드
    bullet_speed_img = pygame.image.load(r'data\graphics\objects\bullet_speed.png')  # 경로 수정 필요
    bullet_count_img = pygame.image.load(r'data\graphics\objects\bullet_count.png')  # 경로 수정 필요
    hp_restore_img = pygame.image.load(r'data\graphics\objects\hp_restore.png')  # 경로 수정 필요

    # 아이템 이미지 크기 조정 (해상도 비율에 맞게 크기 조절)
    item_size = (int(100 * (current_width / 1920)), int(100 * (current_height / 1080)))
    bullet_speed_img = pygame.transform.scale(bullet_speed_img, item_size)
    bullet_count_img = pygame.transform.scale(bullet_count_img, item_size)
    hp_restore_img = pygame.transform.scale(hp_restore_img, item_size)

    # 화면 크기와 위치 계산 (해상도 비율에 맞게 조정)
    item_y = int(600 * (current_height / 1080))  # 이미지 Y 위치
    description_y = item_y + int(125 * (current_height / 1080))  # 설명 텍스트 Y 위치 (이미지 아래)

    # 각 아이템의 중앙 위치 계산 (1.5배 간격)
    item_positions = [
        (current_width // 2 - int(375 * (current_width / 1920)), item_y),  # 왼쪽: 총알 발사속도 증가
        (current_width // 2, item_y),  # 중앙: 총알 개수 증가
        (current_width // 2 + int(375 * (current_width / 1920)), item_y)  # 오른쪽: HP 회복
    ]

    descriptions = [
        "총알 발사속도 증가",  # 왼쪽 아이템 설명
        "총알 개수 증가",  # 중앙 아이템 설명
        "HP 회복"  # 오른쪽 아이템 설명
    ]

    # 아이템 이미지와 설명 배치
    for i, (pos, desc) in enumerate(zip(item_positions, descriptions)):
        # 이미지 표시
        if i == 0:
            screen.blit(bullet_speed_img, pos)
        elif i == 1:
            screen.blit(bullet_count_img, pos)
        elif i == 2:
            screen.blit(hp_restore_img, pos)

        # 설명 텍스트 표시 (설명 텍스트의 위치도 조정)
        desc_text = font.render(desc, True, WHITE)
        text_x = pos[0] + item_size[0] // 2 - desc_text.get_width() // 2  # 텍스트 중앙 정렬
        screen.blit(desc_text, (text_x, description_y))

    pygame.display.update()

    # 입력 대기 루프
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_RETURN:
                waiting = False
                is_returned_from_instructions = True
                start_screen()  # 시작화면으로 돌아가기

#이미지 로드 함수
def load_images(path):
    images = []
    for i in range(4): # 0.png에서 3.png까지
        img = pygame.image.load(os.path.join(path, f"{i}.png")).convert_alpha()
        images.append(img)
    return images

player_images = { #플레이어 이미지
    'up': load_images(os.path.join('images', 'player', 'up')), #올라가는
    'down' : load_images(os.path.join('images', 'player', 'down')), #내려가는
    'left' : load_images(os.path.join('images', 'player', 'left')), #왼쪽
    'right' : load_images(os.path.join('images', 'player', 'right')), #오른쪽
}

obstacle_images = [ #장애물 이미지
    pygame.image.load('data\graphics\objects\grassrock1.png'),
    pygame.image.load('data\graphics\objects\green_tree_small.png'),
]

enemy_images = { #적 이미지
    'bat': load_images(os.path.join('images', 'enemies', 'stage1_monster','bat')), 
    'blob' : load_images(os.path.join('images', 'enemies', 'stage1_monster', 'blob')), 
    'skeleton' : load_images(os.path.join('images', 'enemies', 'stage1_monster','skeleton')),
    'blueblob' : load_images(os.path.join('images', 'enemies', 'stage2_monster', 'blueblob')),
    'cow' : load_images(os.path.join('images', 'enemies', 'stage2_monster', 'cow')),
    'goblin' : load_images(os.path.join('images', 'enemies', 'stage2_monster', 'goblin')),
    'ghost' : load_images(os.path.join('images', 'enemies', 'stage3_monster', 'ghost')),
    'purpleskeleton' : load_images(os.path.join('images', 'enemies', 'stage3_monster', 'purpleskeleton')),
    'imp' : load_images(os.path.join('images', 'enemies', 'stage3_monster', 'imp'))
}

boss_images = { #보스 이미지
    '1stage_boss' : load_images(os.path.join('images', 'enemies', 'stage1_monster', '1stage_boss')),
    '2stage_boss' : load_images(os.path.join('images', 'enemies', 'stage2_monster', '2stage_boss')),
    '3stage_boss' : load_images(os.path.join('images', 'enemies', 'stage3_monster', '3stage_boss'))
}   

item_images = { #아이템 이미지
    'bullet_count' : pygame.image.load(r'data\graphics\objects\bullet_count.png'),
    'bullet_speed' : pygame.image.load(r'data\graphics\objects\bullet_speed.png'),
    'hp_restore' : pygame.image.load(r'data\graphics\objects\hp_restore.png')
}
                #총알 이미지

bullet_images = pygame.image.load(r'images\gun\bullet.png')

                #맵 타일 이미지
map_tile_images = {
    'plain_tile' : pygame.image.load(r'images\map_tile\plain_tile.png').convert(),
    'desert_tile' : pygame.image.load(r'images\map_tile\desert_tile.png').convert(),
    'corruption_tile' : pygame.image.load(r'images\map_tile\corruption_tile.png').convert(),
}

#기본 타일 설정
tile_width = map_tile_images['plain_tile'].get_width()
tile_height = map_tile_images['plain_tile'].get_height()

class Player(pygame.sprite.Sprite): # 스프라이트 클래스 상속
    def __init__(self, x, y): # 플레이어의 초기 위치 x,y좌표
        super().__init__() # 초기화해줌

        self.image = player_images['down'][0]
        self.rect = self.image.get_rect()#캐릭터의 위치
        self.rect.center = (x, y) # 초기위치 x, y값
        self.speed =5 # 플레이어가 움직이는 속도
        self.direction = pygame.Vector2() # 2차원 벡터. 대각선으로 움직일때 위로 1의속도, 옆으로 1의속도 합이 루트2의 속도로 움직이기때문에 쓰는 함수
        self.state = 'down'
        self.HP = 5

        self.animation_index = 0 # 애니메이션 재생 인덱스. 0번부터 시작
        self.animation_time = 0 
        
        self.extra_bullet_count = 0
        self.extra_bullet_timer = 0

        self.shoot_timer = 0
        self.shoot_delay = 500

    def update(self, dt):
        if self.direction.length():
            self.animation_time += dt

            if self.animation_time > 0.1: # 애니메이션을 n초마다 바뀔수있게 설정
                self.animation_time = 0 # 애니메이션 타임을 0으로 초기화 해줌
                self.animation_index += 1 # 업데이트가 콜 될때마다 1씩 늘림
                self.animation_index = self.animation_index % 4 # 4프레임이니까 4로 나눔
                self.image = player_images[self.state][self.animation_index] # 이미지 업데이트
        else:
            self.animation_index = 0
            self.image = player_images[self.state][self.animation_index]

    def move(self, dx, dy): # 플레이어의 방향을 받는 메소드
        if dx > 0:
            self.state = 'right'
        elif dx < 0:
            self.state = 'left'
        elif dy > 0: 
            self.state = 'down'
        elif dy < 0:
            self.state = 'up'

        self.direction.x = dx
        self.direction.y = dy

        if self.direction.length() > 0: # 처음에 0으로 시작하기에 0으로 노멀라이즈(나누려고)하면 오류가 뜸 그래서 조건문 작성
            self.direction = self.direction.normalize() # 어느방향으로 움직이든 1만큼 움직이도록 해주는 함수.(대각선에서 가속 안됨)

        new_x = self.rect.x + self.direction.x * self.speed # 현재 위치에서 이동한 위치를 계산
        new_y = self.rect.y + self.direction.y * self.speed

        if 0 <= new_x <= WORLD_WIDTH - self.rect.width:
            self.rect.x = new_x
        
        if 0 <= new_y <= WORLD_HEIGHT - self.rect.height:
            self.rect.y = new_y
        
    def shoot(self):
        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        bullets = []

        if self.state in direction_map:
            # 기본 발사
            direction = direction_map[self.state]
            bullet = Bullet(self.rect.centerx, self.rect.centery, direction)
            bullets.append(bullet)

            # 발사 각도 제한
            max_angle = 30
            if self.extra_bullet_count > 0:
                angle_step = max_angle / (self.extra_bullet_count + 1) # 각도를 추가 발사수에 맞게 나눔
                current_angle = math.atan2(direction[1], direction[0]) # 현재 방향의 각도(라디안)
            
                # bullet_count 아이템 충돌시 n각도 차이로 총알+1발 발사
                angle_offset = 5 # 각도 차이 설정
                current_angle = math.atan2(direction[1], direction[0])

                for i in range(1, self.extra_bullet_count + 1):
                    # 첫번째 추가 총알
                    new_angle1 = current_angle - math.radians(angle_step * i)
                    direction1 = (math.cos(new_angle1), math.sin(new_angle1))
                    bullet1 = Bullet(self.rect.centerx, self.rect.centery, direction1)
                    bullets.append(bullet1)
                    
                    # 두번째 추가 총알
                    new_angle2 = current_angle + math.radians(angle_step * i)
                    direction2 = (math.cos(new_angle2), math.sin(new_angle2))
                    bullet2 = Bullet(self.rect.centerx, self.rect.centery, direction2)
                    bullets.append(bullet2)

        return bullets
    
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = random.choice(obstacle_images)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Camera():
    def __init__(self):
        self.camera = pygame.Rect(0, 0, WIDTH, HEIGHT)

    def apply(self, entity):
        # 월드 좌표를 화면 좌표로 변환하는 방식으로 수정
        return entity.rect.move(-self.camera.left, -self.camera.top)

    def apply_rect(self, rect):
        return rect.move(-self.camera.left, -self.camera.top)

    def update(self, player):
        # 카메라 위치 업데이트 (플레이어 기준)
        x = player.rect.centerx - WIDTH // 2
        y = player.rect.centery - HEIGHT // 2

        # 맵의 경계 설정 (카메라가 월드 밖으로 나가지 않게 제한)
        x = max(0, min(x, WORLD_WIDTH - WIDTH))
        y = max(0, min(y, WORLD_HEIGHT - HEIGHT))

        # 카메라의 위치 업데이트
        self.camera = pygame.Rect(x, y, WIDTH, HEIGHT)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = bullet_images
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 50 # 총알이 날아가는 속도
        self. direction = direction
        self.lifetime = 1 # 총알이 살아있는 시간
        self.dtt = 0 # 몇 초 동안 살아있었는지 계산

    def update(self, dt):
        self.rect.x += self.direction[0] * self.speed # 총알이 움직이는 함수
        self.rect.y += self.direction[1] * self.speed

        self.dtt += dt

        if self.dtt > self.lifetime:
            self.kill() # 총알 없애기

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, stage_level = 1):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = enemy_images[enemy_type][0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = pygame.Vector2()
        
        self.animation_index = 0
        self.animation_speed = 0.2
        self.animation_time = 0
        self.speed = 1
        self.collide_time = 0

        self.HP = self.get_health_by_stage(stage_level)

    def get_health_by_stage(self, stage_level):
        if stage_level == 1:
            return 1
        elif stage_level == 2:
            return 3
        elif stage_level == 3:
            return 5
        else:
            return 2

    def update(self, dt):
        self.move()

        if self.direction.length():
            self.animation_time += dt

            if self.animation_time > self.animation_speed: # 애니메이션을 0.2초마다 바뀔수있게 설정
                self.animation_time = 0 # 애니메이션 타임을 0으로 초기화 해줌
                self.animation_index += 1 # 업데이트가 콜 될때마다 1씩 늘림
                self.animation_index = self.animation_index % 4 # 4프레임이니까 4로 나눔
                self.image = enemy_images[self.enemy_type][self.animation_index] # 이미지 업데이트
        else:
            self.animation_index = 0
            self.image = enemy_images[self.enemy_type][self.animation_index]

    def move(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        self.direction.x = dx
        self.direction.y = dy

        if self.direction.length() > 0: # 처음에 0으로 시작하기에 0으로 노멀라이즈(나누려고)하면 오류가 뜸 그래서 조건문 작성
            self.direction = self.direction.normalize() # 어느방향으로 움직이든 1만큼 움직이도록 해주는 함수.(대각선에서 가속 안됨)

        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        if pygame.sprite.spritecollide(self, obstacles, False):
            self.rect.x -= self.direction.x * self.speed
            self.rect.y -= self.direction.y * self.speed

    def nuck(self):
        self.rect.x += -self.direction.x * 15
        self.rect.y += -self.direction.y * 15

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, boss_type, stage_level = 1):
        super().__init__()
        self.boss_type = boss_type
        self.image = boss_images[boss_type][0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = pygame.Vector2()

        self.animation_index = 0
        self.animation_speed = 0.2
        self.animation_time = 0
        self.speed = 3
        self.HP = self.get_health_by_stage(stage_level)


    def get_health_by_stage(self, stage_level):
        if stage_level == 1:
            return 200
        elif stage_level == 2:
            return 400
        elif stage_level == 3:
            return 600
        else:
            return 10

    def update(self, dt):
        self.move()

        if self.direction.length():
            self.animation_time += dt

            if self.animation_time > self.animation_speed: # 애니메이션을 0.2초마다 바뀔수있게 설정
                self.animation_time = 0 # 애니메이션 타임을 0으로 초기화 해줌
                self.animation_index += 1 # 업데이트가 콜 될때마다 1씩 늘림
                self.animation_index = self.animation_index % 4 # 4프레임이니까 4로 나눔
                self.image = boss_images[self.boss_type][self.animation_index] # 이미지를 업데이트
        else:
            self.animation_index = 0
            self.image = boss_images[self.boss_type][self.animation_index]
        
        # 보스가 죽었을 때 맵 타일을 변경
        if self.HP <= 0:
            self.on_death()


    def move(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        self.direction.x = dx
        self.direction.y = dy

        if self.direction.length() > 0: # 처음에 0으로 시작하기에 0으로 노멀라이즈(나누려고)하면 오류가 뜸 그래서 조건문 작성
            self.direction = self.direction.normalize() # 어느방향으로 움직이든 1만큼 움직이도록 해주는 함수.(대각선에서 가속 안됨)

        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        if pygame.sprite.spritecollide(self, obstacles, False):
            self.rect.x -= self.direction.x * self.speed
            self.rect.y -= self.direction.y * self.speed

    def nuck(self):
        self.rect.x += -self.direction.x * 10
        self.rect.y += -self.direction.y * 10

    def on_death(self):
        global first_boss_spawn_time, first_boss_death_time, stage_level, boss_spawned
        boss_spawned = False
        
        self.kill()
        first_boss_death_time = time.time()  # 보스가 죽은 시간 기록
        stage_level = min(stage_level + 1, 3)  # 보스가 죽을 때마다 스테이지 레벨을 증가시킴

        if  self.boss_type == '3stage_boss':
            display_complete()
        elif self.boss_type == '2stage_boss':
            hp_restore_drop(boss)
            update_map_tile('corruption_tile')
            pygame.mixer.music.load(stage3_music)  # 게임 클리어 음악 로드
            pygame.mixer.music.set_volume(0.1)  # 볼륨을 50%로 조정
            pygame.mixer.music.play()  # 게임 클리어 음악 1번만 재생
        elif self.boss_type == '1stage_boss':
            hp_restore_drop(boss)
            update_map_tile('desert_tile')

def update_map_tile(new_map):
    global current_map
    current_map = new_map
    # 기존의 모든 첫 번째 스테이지 몬스터와 보스 제거
    for enemy in enemies:
        if current_map == 'desert_tile' and enemy.enemy_type in ['bat', 'blob', 'skeleton']:
            enemy.kill()
        elif current_map == 'corruption_tile' and enemy.enemy_type in ['blueblob', 'cow', 'goblin']:
            enemy.kill()
    for boss in bosses:
        if current_map == 'desert_tile' and boss.boss_type == '1stage_boss':
            boss.kill()
        elif current_map == 'corruption_tile' and boss.boss_type == '2stage_boss':
            boss.kill()
    spawn_enemies_for_new_map()  # 새로운 맵으로 변경 시 몬스터 스폰

# 새로운 맵에서 몬스터 스폰하는 함수
def spawn_enemies_for_new_map():
    global current_map
    global stage_level
    if current_map == 'desert_tile':
        for _ in range(70): # 새로운 맵에서 몬스터 랜덤생성
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            if not_mix_Player_other(x, y, player):
                enemy_type = random.choice(['blueblob', 'cow', 'goblin'])
                enemy = Enemy(x, y, enemy_type, stage_level)
                all_sprites.add(enemy)
                enemies.add(enemy)
    elif current_map == 'corruption_tile':
        for _ in range(70): # 새로운 맵에서 몬스터 랜덤생성
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            if not_mix_Player_other(x, y, player):
                enemy_type = random.choice(['ghost', 'purpleskeleton', 'imp'])
                enemy = Enemy(x, y, enemy_type, stage_level)
                all_sprites.add(enemy)
                enemies.add(enemy)

def hp_restore_drop(boss):  
    boss_x, boss_y = boss.rect.center  # 보스의 중심 좌표 가져오기
    item = Item(boss_x, boss_y, 'hp_restore')  # hp_restore 아이템 생성
    all_sprites.add(item)  # 스프라이트 그룹에 추가
    items.add(item)  # 아이템 그룹에 추가

class Item(pygame.sprite.Sprite): # 아이템
    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type
        self.image = item_images[item_type]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

# ----------------------------------------------------------
player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2) # 플레이어의 초기위치를 위드 헤이트 나누기 2씩하면 중앙이될것

camera = Camera()

def not_mix_Player_other(x, y, player, min_distance=1000): # 플레이어와 (x, y) 위치의 거리를 계산
    distance = math.sqrt((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2)
    return distance > min_distance     # 거리가 최소값보다 크면 True 반환 (스폰 가능), 아니면 False 반환


# 스프라이트 그룹
all_sprites = pygame.sprite.Group() # 스프라이트 그룹을 만들어줌
obstacles = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bosses = pygame.sprite.Group()
items = pygame.sprite.Group()

all_sprites.add(player) # 플레이어의 스프라이트를 추가해줌

for _ in range(30): # 장애물 랜덤생성
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    obstacle = Obstacle(x, y)
    all_sprites.add(obstacle)
    obstacles.add(obstacle)

for _ in range(70): # 몬스터 랜덤생성 ##########
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        if not_mix_Player_other(x, y, player):
            enemy_type = random.choice(['bat', 'blob', 'skeleton'])
            enemy = Enemy(x, y, enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)
            break

for _ in range(5): # 아이템 랜덤생성
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    #item_type = random.choice(['bullet_speed', 'bullet_speed'])
    item_type = random.choice(['bullet_speed'])
    item = Item(x, y, item_type)
    all_sprites.add(item)
    items.add(item)

#loop #전역변수
running = True 
clock = pygame.time.Clock()
enemy_timer = 0
boss_timer = 0
isCollide = time.time() # 플레이어와 몬스터 충돌이 발생한 시간을 기록하는 용도
start_time = time.time() # 게임플레이타임 표시에 사용
isDead = False

is_boss_spawned = False
first_boss_spawn_time = None
first_boss_death_time = None
second_boss_spawn_delay = 60 #두번째 보스를 n초후에 생성
third_boss_spawn_delay = 60 # 세번째 보스를 n초후에 생성
boss_spawn_interval = 9999

current_map = 'plain_tile'
font = pygame.font.Font(None, 74) # 폰트

stage_level = 1 # 스테이지 레벨 초기화

def hp_check(obj): # hp가 0이되면 
    if obj.HP <= 0:
        return True
    return False

def check_and_spawn_next_boss():
    global first_boss_death_time, second_boss_spawn_delay, third_boss_spawn_delay, boss_spawned
    
    current_time = time.time()
    
    # 첫 번째 보스가 죽고 두 번째 보스 스폰
    if first_boss_death_time and current_map == 'desert_tile':
        elapsed_time = current_time - first_boss_death_time
        if elapsed_time >= second_boss_spawn_delay:
            boss_type = '2stage_boss'
            while True:
                x = random.randint(0, WORLD_WIDTH)
                y = random.randint(0, WORLD_HEIGHT)
                if not_mix_Player_other(x, y, player):
                    new_boss = Boss(x, y, boss_type, stage_level = stage_level)
                    all_sprites.add(new_boss)
                    bosses.add(new_boss)
                    boss_spawned = True
                    first_boss_death_time = None
                    break

    # 두 번째 보스가 죽고 세 번째 보스 스폰
    elif first_boss_death_time and current_map == 'corruption_tile':
        elapsed_time = current_time - first_boss_death_time
        if elapsed_time >= third_boss_spawn_delay:
            boss_type = '3stage_boss'
            while True:
                x = random.randint(0, WORLD_WIDTH)
                y = random.randint(0, WORLD_HEIGHT)
                if not_mix_Player_other(x, y, player):
                    new_boss = Boss(x, y, boss_type, stage_level = stage_level)
                    all_sprites.add(new_boss)
                    bosses.add(new_boss)
                    boss_spawned = True
                    first_boss_death_time = None  # 보스를 스폰한 후 초기화
                    break

def check_and_change_map(): #보스가 죽으면 맵 전환하는 함수
    global current_map
    for boss in bosses:
        if hp_check(boss):
            boss.on_death()
            current_map = 'desert_tile'#맵을 desert로 바꿈


def display_complete():  # 엔딩화면
    global running, is_returned_from_instructions

    # 현재 창의 크기 가져오기
    current_width, current_height = screen.get_size()

    # 폰트 크기 비율 조정 (기본 해상도 1920x1080에 맞춰 비례)
    large_font_size = int(150 * (current_width / 1920))
    small_font_size = int(70 * (current_width / 1920))

    # 플레이 타임 기록
    play_time = round(elapsed_time, 2)
    try:
        cur.execute("INSERT INTO rank values(?, ?);", (name, play_time))
        con.commit()
    except:
        cur.execute("update rank set time=? where id=? and time<?;", (play_time, name, play_time))
        con.commit()

    # 음악 재생
    pygame.mixer.music.stop()
    pygame.mixer.music.load(complete_music)  # 게임 클리어 음악 로드
    pygame.mixer.music.set_volume(0.7)
    pygame.mixer.music.play()  # 게임 클리어 음악 1번만 재생

    # 화면 초기화 및 텍스트 설정
    screen.fill(BLACK)  # 배경색을 검정으로 변경
    large_font = pygame.font.Font(FONT_PATH, large_font_size)  # 큰 폰트 설정
    text_surface = large_font.render('GAME COMPLETE', True, GREEN)  # 엔딩 텍스트
    text_rect = text_surface.get_rect(center=(current_width // 2, current_height // 2))
    screen.blit(text_surface, text_rect)

    # Q, R, S 키 안내문구 추가
    small_font = pygame.font.Font(FONT_PATH, small_font_size)  # 작은 폰트 설정
    restart_quit_surface = small_font.render('Q : 게임종료       R : 재시작       E : 시작화면', True, GREEN)
    restart_quit_rect = restart_quit_surface.get_rect(center=(current_width // 2, current_height // 2 + int(300 * (current_height / 1080))))
    screen.blit(restart_quit_surface, restart_quit_rect)

    pygame.display.update()

    # 사용자 입력 대기 루프
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_q:  # Q 입력 시 게임 종료
                    pygame.quit()
                    sys.exit()
                elif event.key == K_r:  # R 입력 시 게임 재시작
                    reset_game()
                    running = True
                    waiting = False
                elif event.key == K_e:  # E 입력 시 시작화면으로 돌아가기
                    is_returned_from_instructions = False
                    start_screen()
                    waiting = False

def display_game_over():  # 게임 종료 문구
    global is_music_playing

    # 현재 창의 크기 가져오기
    current_width, current_height = screen.get_size()

    # 폰트 크기 비율 조정 (기본 해상도 1920x1080에 맞춰 비례)
    large_font_size = int(300 * (current_width / 1920))
    small_font_size = int(70 * (current_width / 1920))

    # 큰 폰트 설정 및 게임 오버 텍스트
    large_font = pygame.font.Font(None, large_font_size)
    game_over_surface = large_font.render('YOU DIED', True, RED)
    game_over_rect = game_over_surface.get_rect(center=(current_width // 2, current_height // 2))
    screen.blit(game_over_surface, game_over_rect)

    # Q, R, S 키 안내문구 추가
    small_font = pygame.font.Font(FONT_PATH, small_font_size)
    restart_quit_surface = small_font.render('Q : 게임종료        R : 재시작        E : 시작화면', True, RED)
    restart_quit_rect = restart_quit_surface.get_rect(center=(current_width // 2, current_height // 2 + int(300 * (current_height / 1080))))
    screen.blit(restart_quit_surface, restart_quit_rect)

    # 음악 재생 확인 후 게임 오버 음악 재생
    if not is_music_playing:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(die_music)  # die_music 로드
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play()  # 게임 오버 음악 재생
        is_music_playing = True

def display_player_HP(): # 플레이어 HP 문구
    player_HP_surface = font.render('HP 'f'{player.HP}', True, BLACK)
    player_HP_rect = player_HP_surface.get_rect(center=(WIDTH // 1.2, HEIGHT // 10))
    screen.blit(player_HP_surface, player_HP_rect)

def display_game_playtime(): # 플레이타임 문구
    elapsed_time = time.time() - start_time  # 현재 시간에서 시작 시간 뺀 시간(초 단위)
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    play_time_surface = font.render(f'{minutes:02}:{seconds:02}', True, BLACK)
    play_time_rect = play_time_surface.get_rect(center=(WIDTH // 2, HEIGHT // 10))
    screen.blit(play_time_surface, play_time_rect)

#while loop문
start_screen()
pygame.mixer.music.load(stage_music)  # 게임플레이 음악 로드
pygame.mixer.music.set_volume(0.5) 
pygame.mixer.music.play(-1)  # 반복 재생
boss_spawned = False  # 보스 스폰 여부를 관리하는 변수 추가

while running: # 게임실행할 때, while loop문
    dt = clock.tick(120) / 1000 # 밀리세컨드. 초당 60프레임으로 계산하는 코드
    global currentTime
    currentTime = time.time()

    for event in pygame.event.get(): # 이벤트중에서 선택
        if event.type == pygame.QUIT: # 윈도우에서 x버튼 누르면 꺼지도록 활성화
            running = False # 종료
        if event.type == pygame.KEYDOWN and isDead:
            if event.key == pygame.K_r: #r 입력시 게임 재시작
                reset_game() #게임 재시작
                runnign = True
                isDead = False

                # 음악을 멈추고 새로운 음악 재생
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(stage_music)
                pygame.mixer.music.set_volume(0.5) 
                pygame.mixer.music.play(-1)

            elif event.key == pygame.K_q: # q 입력시 게임 종료
                pygame.quit() # 게임종료
                sys.exit()

            elif event.key == pygame.K_e: # e 입력시 시작화면으로 돌아가기
                is_returned_from_instructions = False 
                start_screen()
                running = True
                isDead = False
                is_music_playing = False

    # 게임 시작 화면에서 게임이 시작될 때의 음악 처리
    if not isDead and not pygame.mixer.music.get_busy() and running:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(stage_music)
        pygame.mixer.music.play(-1)

    keys = pygame.key.get_pressed() # 키를 입력받는 변수 
    dx = keys[pygame.K_d] - keys[pygame.K_a] # d(오른쪽)에서 a(왼쪽)을 빼서 양수면 오른쪽으로 이동한것.
    dy = keys[pygame.K_s] - keys[pygame.K_w] # s(아래)에서 w(위)를 빼서 양수면 아래로 이동한 것

    if not isDead:
        player.update(dt) # 플레이어 애니메이션 업데이트
        player.move(dx, dy) # 플레이어 이동
        bullets.update(dt) # 총알 업데이트(움직임)
        enemies.update(dt) # 몬스터 업데이트(움직임)
        bosses.update(dt) # 보스 업데이트
        camera.update(player)

    check_and_spawn_next_boss()

    # 플레이어와 장애물 충돌체크
    if pygame.sprite.spritecollide(player, obstacles, False): #3번째 변수 dokill:닿으면 없앨것인가.
        player.rect.x -= dx * player.speed
        player.rect.y -= dy * player.speed

    # 플레이어와 몬스터 충돌체크
    isPlayer_enemies = pygame.sprite.spritecollide(player, enemies, False)
    if isPlayer_enemies:
        if abs(isCollide - time.time()) > 1: # (부딛힌 시점의 시간) - (시간)이 1보다 크면
            player.HP -= 1 # 피 -1
            if not isDead:  # isDead가 아닌 경우에만 효과음 재생
                play_sound(hit_music)  # 충돌 효과음 재생
            isCollide = time.time() # 초기화
        if hp_check(player):
           all_sprites.remove(player)
           isDead = True

    # 플레이어와 보스 충돌체크
    isPlayer_bosses = pygame.sprite.spritecollide(player, bosses, False)
    if isPlayer_bosses:
        if abs(isCollide - time.time()) > 1:
            player.HP -= 3
            if not isDead:  # isDead가 아닌 경우에만 효과음 재생
                play_sound(hit_music)  # 충돌 효과음 재생
            isCollide = time.time()
        if hp_check(player):
           all_sprites.remove(player)
           isDead = True

    # 총알과 적의 충돌 체크
    for bullet in bullets:
        hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False) # spritecollide = 충돌 하면 사라지게하는것
        if hit_enemies:
            bullet.kill()
            for enemy in hit_enemies:
                enemy.HP -= 1
                if not hp_check(enemy):
                    enemy.nuck()
                if enemy.HP == 0:
                    hit_enemies = pygame.sprite.spritecollide(bullet, enemies, True)
                # aaall_sprites.remove(enemy)

    # 총알과 보스의 충돌 체크
    for bullet in bullets:
        hit_bosses = pygame.sprite.spritecollide(bullet, bosses, False)
        if hit_bosses:
            bullet.kill()
            for boss in hit_bosses:
                boss.HP -= 1
                if not hp_check(boss): 
                    boss.nuck() # 넉백 구현
                if boss.HP == 0:
                    boss.on_death()
    # 총알발사
    if not isDead:
        player.shoot_timer += dt * 1000 # 밀리세컨드로 계산
        if player.shoot_timer >= player.shoot_delay:
            player.shoot_timer = 0
            new_bullets = player.shoot()
            bullets.add(new_bullets)
            all_sprites.add(new_bullets)

    # 플레이어와 아이템 충돌 체크  
    getItem = pygame.sprite.spritecollide(player, items, True)
    for item in  getItem:
        play_sound(have_music, 0.2)  # 아이템 획득 효과음 재생
        if item.item_type == 'bullet_speed':
            player.shoot_delay = player.shoot_delay // 1.6
        if item.item_type == 'bullet_count':
            player.extra_bullet_count += 1
        if item.item_type == 'hp_restore':
            if player.HP < 5:
                player.HP += 1


    # 무작위 적 생성
    enemy_timer += dt

    if enemy_timer > 0.3:
        enemy_timer = 0
        if current_map == 'plain_tile':
            enemy_type = random.choice(['bat', 'blob', 'skeleton'])
        elif current_map == 'desert_tile':
            enemy_type = random.choice(['blueblob', 'cow', 'goblin'])
        elif current_map == 'corruption_tile':
            enemy_type = random.choice(['ghost', 'purpleskeleton', ])
        while True:
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            if not_mix_Player_other(x, y, player):
                new_enemy = Enemy(x, y, enemy_type, stage_level)
                all_sprites.add(new_enemy)
                enemies.add(new_enemy)
                break

    #배경 타일 반복해서 그리기
    for x in range(0, WORLD_WIDTH, tile_width):
        for y in range(0, WORLD_HEIGHT, tile_height):
            screen.blit(map_tile_images['plain_tile'], camera.apply_rect(pygame.Rect(x, y, tile_width, tile_height)))

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    # 첫번째 보스 생성 조건
    if current_map == 'plain_tile' and minutes == 1 and seconds == 0  and not is_boss_spawned: #조건을 n초로 설정
        boss_type = random.choice(['1stage_boss'])
        while True:
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            if not_mix_Player_other(x, y, player):
                new_boss = Boss(x, y, boss_type, stage_level=stage_level)
                all_sprites.add(new_boss)
                bosses.add(new_boss)
                is_boss_spawned = True  # 첫번째 보스가 생성되었음을 기록
                boss_spawned = True  # BOSS SPAWN 문구를 표시하기 위해 추가
                break

    if first_boss_spawn_time is not None:
        elapsed_since_first_boss = time.time() - first_boss_spawn_time
        if elapsed_since_first_boss >= boss_spawn_interval:
            if current_map == 'plain_tile':
                boss_type = '1stage_boss'
            elif current_map == 'desert_tile':
                boss_type = '2stage_boss'
            elif current_map == 'corruption_tile':
                boss_type = '3stage_boss'
            while True:
                x = random.randint(0, WORLD_WIDTH)
                y = random.randint(0, WORLD_HEIGHT)
                if not_mix_Player_other(x, y, player):
                    new_boss = Boss(x, y, boss_type, stage_level=stage_level)
                    all_sprites.add(new_boss)
                    bosses.add(new_boss)
                    first_boss_spawn_time = time.time()  # 새로운 보스를 생성한 시간을 기록
                    boss_spawned = True  # BOSS SPAWN 문구를 표시하기 위해 추가
                    print(f"{boss_type} 생성, boss_spawned: ", boss_spawned)
                    break 

    for boss in bosses:
        if hp_check(boss):
            boss.on_death()
            boss_spawned = False  # 보스가 죽으면 BOSS SPAWN 문구 제거
    # 그리는 함수
    camera.update(player)

    if not isDead:
        ##현재 맵 타일을 화면에 그림
        tile_width = map_tile_images[current_map].get_width()
        tile_height = map_tile_images[current_map].get_height()

        #타일이미지를 반복적으로 그려 화면 전체를 덮음
        for x in range(0, WORLD_WIDTH, tile_width):
            for y in range(0, WORLD_HEIGHT, tile_height):            
                screen.blit(map_tile_images[current_map], (x - camera.camera.left, y - camera.camera.top))

        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite)) # blit = 스티커를 떼서 붙이다 라는 의미
        
        # BOSS SPAWN 문구 표시
        if boss_spawned:
            boss_font = pygame.font.Font(None, 74)
            boss_text = boss_font.render('BOSS SPAWN', True, (255, 0, 0))
            screen.blit(boss_text, (WIDTH // 10, HEIGHT // 13))

        display_game_playtime()
        display_player_HP()
    else:
        screen.fill(BLACK)  # 어두운 배경
        display_game_over() # 게임종료화면
    pygame.display.flip() # 준비된 화면을 보이게 해주는 함수

pygame.quit() # 종료