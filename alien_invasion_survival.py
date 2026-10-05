import pygame
import random
import time
import pandas as pd
from datetime import datetime
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Alien Invasion Survival")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)
GRAY = (128, 128, 128)
PINK = (255, 182, 193)
LIME = (50, 205, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)

# Game flow states
SHOW_RULES = 0
NAME_INPUT = 1
PLAYING = 2
GAME_OVER = 3
SHOW_SCORE = 4
SHOW_LEADERBOARD = 5
PAUSED = 6
game_state = SHOW_RULES

# Player settings
player_width = 35
player_height = 25
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 20
player_speed = 8
player_health = 100
max_health = 100

# Shooting settings
bullet_width = 3
bullet_height = 12
bullet_speed = 10
bullets = []
shoot_cooldown = 0
shoot_delay = 15  # frames between shots

# Enemy settings
enemy_width = 30
enemy_height = 30
enemy_base_speed = 2
enemy_current_speed = enemy_base_speed
enemies = []
enemy_spawn_timer = 0
enemy_spawn_delay = 45  # frames
enemy_bullets = []
enemy_shoot_chance = 0.005
enemy_evasion_skill = 0.0
enemy_prediction_skill = 0.0

# Boss settings
boss_width = 70
boss_height = 60
boss_speed = 3
boss_health = 25
boss_max_health = 25
boss_active = False
boss_spawn_timer = 0
boss_spawn_interval = 40  # seconds
boss_x = WIDTH // 2 - boss_width // 2
boss_y = -boss_height
boss_direction = 1
boss_bullets = []
boss_shoot_chance = 0.02
boss_alert_timer = 0
boss_alert_duration = 3

# Power-up settings (still in game but shield removed)
power_up_width = 25
power_up_height = 25
power_up_speed = 3
power_ups = []
power_up_spawn_timer = 0
power_up_spawn_delay = 450
power_up_health_boost = 10

# Game state
score = 0  # Now represents survival time in seconds
game_start_time = time.time()
survival_time = 0
player_name = ""
difficulty_increase_timer = 60
last_difficulty_increase = time.time()
player_best_time = 0
is_new_high_score = False

# Pause menu options
pause_options = ["RESUME", "QUIT TO MENU"]
selected_option = 0

# Font
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 48)
small_font = pygame.font.SysFont('Arial', 20)
rules_font = pygame.font.SysFont('Arial', 20)
score_font = pygame.font.SysFont('Arial', 36)
pause_font = pygame.font.SysFont('Arial', 36)

# DataFrame for storing player data
try:
    df = pd.read_csv('survival_leaderboard.csv')
except FileNotFoundError:
    df = pd.DataFrame(columns=['Name', 'Survival_Time', 'Date'])

class Bullet:
    def __init__(self, x, y, width=bullet_width, height=bullet_height, speed=bullet_speed, color=GREEN, enemy=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.color = color
        self.is_enemy = enemy
    
    def update(self):
        if self.is_enemy:
            self.y += self.speed
            return self.y > HEIGHT
        else:
            self.y -= self.speed
            return self.y < 0
    
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        if self.color == GREEN:
            pygame.draw.rect(screen, LIME, (self.x-1, self.y-1, self.width+2, self.height+2), 1)
    
    def collides_with(self, x, y, width, height):
        return (self.x < x + width and 
                self.x + self.width > x and 
                self.y < y + height and 
                self.y + self.height > y)

class Enemy:
    def __init__(self):
        self.x = random.randint(0, WIDTH - enemy_width)
        self.y = -enemy_height
        self.speed_x = random.uniform(-1.5, 1.5) * (1 + enemy_evasion_skill)
        self.speed_y = enemy_current_speed + random.random() * 1.5
        self.move_timer = 0
        self.move_direction_change = random.randint(30, 90)
        self.color = random.choice([(255, 50, 50), (50, 50, 255), (255, 100, 50), (100, 50, 255)])
        self.last_shot_time = 0
        self.shoot_delay = random.randint(60, 180)
        self.aggressiveness = 0.3 + enemy_prediction_skill * 0.7
    
    def update(self, player_x, player_y):
        evasion_x = 0
        if enemy_evasion_skill > 0.3:
            if abs(player_x - self.x) < 100 and player_y < self.y:
                evasion_x = 1 if self.x < WIDTH/2 else -1
        
        target_x = player_x
        if enemy_prediction_skill > 0.2:
            prediction = (player_x - self.x) * 0.02 * enemy_prediction_skill
            target_x += prediction
        
        self.x += self.speed_x + evasion_x * enemy_evasion_skill * 2
        self.y += self.speed_y
        
        if random.random() < self.aggressiveness * 0.02:
            if self.x < target_x:
                self.speed_x += 0.1
            else:
                self.speed_x -= 0.1
        
        self.move_timer += 1
        if self.move_timer >= self.move_direction_change:
            self.speed_x = random.uniform(-2, 2) * (1 + enemy_evasion_skill)
            self.move_timer = 0
            self.move_direction_change = random.randint(30, 90)
        
        if self.x <= 0 or self.x >= WIDTH - enemy_width:
            self.speed_x *= -1
            if enemy_evasion_skill > 0.5:
                self.x = max(20, min(WIDTH - enemy_width - 20, self.x))
        
        return self.y > HEIGHT or self.x < -enemy_width or self.x > WIDTH
    
    def draw(self):
        pygame.draw.ellipse(screen, self.color, (self.x, self.y, enemy_width, enemy_height//2))
        pygame.draw.ellipse(screen, (min(255, self.color[0]+50), min(255, self.color[1]+50), min(255, self.color[2]+50)), 
                           (self.x+2, self.y+2, enemy_width-4, enemy_height//2-4))
        
        pygame.draw.circle(screen, WHITE, (self.x + enemy_width // 2, self.y + enemy_height // 4), 6)
        pygame.draw.circle(screen, YELLOW, (self.x + enemy_width // 2, self.y + enemy_height // 4), 3)
        
        pygame.draw.ellipse(screen, YELLOW, (self.x + 5, self.y + enemy_height//2, enemy_width-10, 4))
        pygame.draw.ellipse(screen, ORANGE, (self.x + 7, self.y + enemy_height//2 + 1, enemy_width-14, 2))
    
    def collides_with(self, x, y, width, height):
        return (self.x < x + width and 
                self.x + enemy_width > x and 
                self.y < y + height and 
                self.y + enemy_height > y)
    
    def shoot(self, player_x, player_y):
        self.last_shot_time += 1
        if self.last_shot_time >= self.shoot_delay:
            aim_x = player_x + enemy_width // 2
            if enemy_prediction_skill > 0.4:
                vertical_distance = player_y - self.y
                if vertical_distance > 0:
                    prediction = (player_x - self.x) * 0.1 * enemy_prediction_skill
                    aim_x += prediction
            
            bullet_x = self.x + enemy_width // 2 - bullet_width // 2
            if enemy_prediction_skill > 0:
                accuracy = 1.0 - (enemy_prediction_skill * 0.3)
                spread = (random.random() - 0.5) * 20 * accuracy
                bullet_x += spread
            
            self.last_shot_time = 0
            self.shoot_delay = random.randint(60, 180) // (1 + enemy_prediction_skill)
            return Bullet(bullet_x, self.y + enemy_height, color=RED, enemy=True)
        return None

class Boss:
    def __init__(self):
        self.x = WIDTH // 2 - boss_width // 2
        self.y = -boss_height
        self.speed_x = boss_speed
        self.direction = 1
        self.health = boss_health
        self.max_health = boss_max_health
        self.move_boundary = 100
        self.center_x = WIDTH // 2
        self.last_shot_time = 0
        self.shoot_pattern = 0
        
    def update(self):
        self.x += self.speed_x * self.direction
        
        if self.y < HEIGHT // 4:
            self.y += 1
        
        if self.x <= self.center_x - self.move_boundary or self.x >= self.center_x + self.move_boundary:
            self.direction *= -1
            self.shoot_pattern = (self.shoot_pattern + 1) % 3
        
        if self.x <= 0 or self.x >= WIDTH - boss_width:
            self.direction *= -1
            self.x = max(0, min(WIDTH - boss_width, self.x))
    
    def draw(self):
        pygame.draw.ellipse(screen, DARK_RED, (self.x, self.y, boss_width, boss_height))
        pygame.draw.ellipse(screen, RED, (self.x+5, self.y+5, boss_width-10, boss_height-10))
        
        pygame.draw.circle(screen, (200, 200, 255), 
                          (self.x + boss_width // 2, self.y + boss_height // 2), 
                          boss_height // 3)
        pygame.draw.circle(screen, (150, 150, 255), 
                          (self.x + boss_width // 2, self.y + boss_height // 2), 
                          boss_height // 4)
        
        for i in range(3):
            engine_x = self.x + (i+1) * boss_width // 4 - 5
            pygame.draw.rect(screen, YELLOW, (engine_x, self.y + boss_height - 10, 10, 10))
            pygame.draw.rect(screen, ORANGE, (engine_x+2, self.y + boss_height - 8, 6, 6))
        
        for i in range(2):
            side = -1 if i == 0 else 1
            tentacle_x = self.x + boss_width // 2 + (side * boss_width // 3)
            pygame.draw.line(screen, PURPLE, 
                            (tentacle_x, self.y + boss_height // 2),
                            (tentacle_x + side * 20, self.y + boss_height // 2 + 20), 3)
        
        health_width = (self.health / self.max_health) * boss_width
        pygame.draw.rect(screen, RED, (self.x, self.y - 15, boss_width, 10))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 15, health_width, 10))
        
        health_text = small_font.render(f"{self.health}/{self.max_health}", True, WHITE)
        screen.blit(health_text, (self.x + boss_width // 2 - health_text.get_width() // 2, self.y - 25))
    
    def collides_with(self, x, y, width, height):
        return (self.x < x + width and 
                self.x + boss_width > x and 
                self.y < y + height and 
                self.y + boss_height > y)
    
    def shoot(self):
        self.last_shot_time += 1
        if self.last_shot_time >= 30:
            bullets = []
            
            if self.shoot_pattern == 0:
                bullets.append(Bullet(self.x + boss_width // 2 - 4, 
                                     self.y + boss_height, 
                                     width=8, height=20, speed=6, color=ORANGE, enemy=True))
            elif self.shoot_pattern == 1:
                for i in range(3):
                    offset = (i-1) * 15
                    bullets.append(Bullet(self.x + boss_width // 2 - 2 + offset, 
                                         self.y + boss_height, 
                                         width=4, height=15, speed=5, color=PINK, enemy=True))
            else:
                bullets.append(Bullet(self.x + boss_width // 4, 
                                     self.y + boss_height, 
                                     width=6, height=18, speed=5, color=CYAN, enemy=True))
                bullets.append(Bullet(self.x + 3*boss_width // 4, 
                                     self.y + boss_height, 
                                     width=6, height=18, speed=5, color=CYAN, enemy=True))
            
            self.last_shot_time = 0
            return bullets
        return []

class PowerUp:
    def __init__(self):
        self.x = random.randint(0, WIDTH - power_up_width)
        self.y = -power_up_height
        self.speed_x = random.uniform(-1, 1)
        self.rotation = 0
    
    def update(self):
        self.x += self.speed_x
        self.y += power_up_speed
        self.rotation += 5
        
        if self.x <= 0 or self.x >= WIDTH - power_up_width:
            self.speed_x *= -1
        
        return self.y > HEIGHT
    
    def draw(self):
        center_x = self.x + power_up_width // 2
        center_y = self.y + power_up_height // 2
        
        for i in range(3):
            radius = power_up_width // 2 + i
            pygame.draw.circle(screen, (255, 255, 200 - i*50), 
                             (int(center_x), int(center_y)), 
                             radius, 1)
        
        angle = math.radians(self.rotation)
        points = []
        for i in range(6):
            a = angle + i * math.pi / 3
            r = power_up_width // 3 if i % 2 == 0 else power_up_width // 2
            points.append((
                center_x + math.cos(a) * r,
                center_y + math.sin(a) * r
            ))
        
        pygame.draw.polygon(screen, YELLOW, points)
        pygame.draw.polygon(screen, (255, 255, 150), points, 2)
        
        health_text = small_font.render("+10%", True, GREEN)
        screen.blit(health_text, (center_x - health_text.get_width() // 2,
                                 center_y - health_text.get_height() // 2))
    
    def collides_with(self, x, y, width, height):
        center_x = self.x + power_up_width // 2
        center_y = self.y + power_up_height // 2
        radius = power_up_width // 2
        
        closest_x = max(x, min(center_x, x + width))
        closest_y = max(y, min(center_y, y + height))
        
        distance_x = center_x - closest_x
        distance_y = center_y - closest_y
        
        return (distance_x ** 2 + distance_y ** 2) <= (radius ** 2)

def spawn_enemy():
    enemies.append(Enemy())

def spawn_power_up():
    power_ups.append(PowerUp())

def draw_player():
    center_x = player_x + player_width // 2
    center_y = player_y + player_height // 2
    
    pygame.draw.rect(screen, GREEN, (player_x, player_y, player_width, player_height))
    pygame.draw.rect(screen, LIME, (player_x+2, player_y+2, player_width-4, player_height-4), 1)
    
    pygame.draw.circle(screen, CYAN, (center_x, center_y), 6)
    pygame.draw.circle(screen, (200, 255, 255), (center_x, center_y), 3)
    
    pygame.draw.polygon(screen, BLUE, [
        (player_x, player_y + player_height),
        (center_x, player_y + player_height - 5),
        (player_x + player_width, player_y + player_height)
    ])
    
    pygame.draw.rect(screen, YELLOW, (player_x + 5, player_y + player_height, player_width - 10, 3))
    pygame.draw.rect(screen, ORANGE, (player_x + 7, player_y + player_height + 1, player_width - 14, 1))

def draw_health_bar():
    # Health bar at top right
    bar_x = WIDTH - 210
    bar_y = 10
    
    pygame.draw.rect(screen, RED, (bar_x, bar_y, 200, 25))
    
    health_width = (player_health / max_health) * 200
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, 25))
    
    health_text = font.render(f"Health: {player_health:.0f}%", True, WHITE)
    screen.blit(health_text, (bar_x + 5, bar_y + 3))

def draw_rules_screen():
    screen.fill(BLACK)
    
    # Draw stars background
    for _ in range(50):
        star_x = random.randint(0, WIDTH)
        star_y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)
    
    # Title
    title = title_font.render("ALIEN INVASION SURVIVAL", True, GREEN)
    subtitle = font.render("SURVIVE AS LONG AS POSSIBLE", True, CYAN)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 70))
    
    # Rules box - larger to accommodate all rules neatly
    rules_box = pygame.Rect(WIDTH // 2 - 350, 110, 700, 420)
    pygame.draw.rect(screen, (20, 20, 40), rules_box)
    pygame.draw.rect(screen, CYAN, rules_box, 3)
    
    # Rules title inside box
    rules_title = font.render("SURVIVAL RULES", True, YELLOW)
    screen.blit(rules_title, (WIDTH // 2 - rules_title.get_width() // 2, 125))
    
    # Draw decorative line under title
    pygame.draw.line(screen, CYAN, (WIDTH // 2 - 150, 150), (WIDTH // 2 + 150, 150), 2)
    
    # Rules content - all neatly aligned inside the box with proper spacing
    rules = [
        ("OBJECTIVE:", "Survive the alien invasion as long as possible!"),
        ("", "Your survival time is your score."),
        ("", ""),
        ("CONTROLS:", ""),
        ("• LEFT/RIGHT ARROW KEYS", "- Move your spaceship"),
        ("• R KEY", "- Shoot at aliens"),
        ("• ESC KEY", "- Pause game / Show menu"),
        ("", ""),
        ("GAME FEATURES:", ""),
        ("• Aliens get smarter over time", ""),
        ("• Collect health power-ups", "(+10% health)"),
        ("• Defeat the boss mothership", "(appears every 40 seconds)"),
        ("", ""),
        ("LEADERBOARD:", ""),
        ("• Top 5 players by survival time", ""),
        ("• Only your best survival time counts", ""),
        ("", ""),
        ("TIP:", "Stay alive to increase your survival time!")
    ]
    
    y_offset = 175
    for i, (left, right) in enumerate(rules):
        if left == "" and right == "":
            y_offset += 8  # Gap between sections
            continue
            
        if left and right:
            # Two-part rule with proper spacing
            if "LEFT/RIGHT" in left:
                left_text = rules_font.render(left, True, WHITE)
                screen.blit(left_text, (WIDTH // 2 - 320, y_offset))
                right_text = rules_font.render(right, True, CYAN)
                screen.blit(right_text, (WIDTH // 2 - 100, y_offset))
            elif "power-ups" in left:
                left_text = rules_font.render(left, True, WHITE)
                screen.blit(left_text, (WIDTH // 2 - 320, y_offset))
                right_text = rules_font.render(right, True, GREEN)
                screen.blit(right_text, (WIDTH // 2 - 100, y_offset))
            else:
                left_text = rules_font.render(left, True, YELLOW if ":" in left else WHITE)
                screen.blit(left_text, (WIDTH // 2 - 320, y_offset))
                if right:
                    right_text = rules_font.render(right, True, CYAN if "health" in right else WHITE)
                    screen.blit(right_text, (WIDTH // 2 - 100, y_offset))
        elif left:
            # Single line rule
            text_color = YELLOW if ":" in left else WHITE
            if "TIP" in left:
                text_color = GOLD
            text = rules_font.render(left, True, text_color)
            screen.blit(text, (WIDTH // 2 - 320, y_offset))
        
        y_offset += 22
    
    # Continue prompt below the box
    continue_text = font.render("Press ENTER to continue to registration", True, YELLOW)
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 50))
    
    # Decorative alien ship
    pygame.draw.ellipse(screen, (255, 50, 50), (WIDTH // 2 - 20, HEIGHT - 120, 40, 20))
    pygame.draw.circle(screen, WHITE, (WIDTH // 2, HEIGHT - 110), 8)
    pygame.draw.circle(screen, YELLOW, (WIDTH // 2, HEIGHT - 110), 4)

def draw_name_input_screen():
    screen.fill(BLACK)
    
    for _ in range(50):
        star_x = random.randint(0, WIDTH)
        star_y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)
    
    title = title_font.render("PILOT REGISTRATION", True, GREEN)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    
    input_box = pygame.Rect(WIDTH // 2 - 200, 250, 400, 60)
    pygame.draw.rect(screen, WHITE, input_box, 2)
    
    name_text = font.render(player_name if player_name else "Enter pilot name", True, WHITE)
    screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, 265))
    
    instructions = [
        "Enter your pilot name using the keyboard",
        "Only letters and numbers are allowed",
        "Press BACKSPACE to delete",
        "Press ENTER when ready for launch"
    ]
    
    for i, instruction in enumerate(instructions):
        inst_text = font.render(instruction, True, CYAN)
        screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, 350 + i * 40))
    
    pygame.draw.circle(screen, YELLOW, (WIDTH // 2, 500), 30)
    start_text = font.render("LAUNCH", True, BLACK)
    screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 495))

def draw_score_screen():
    """Draw screen showing player's survival time"""
    screen.fill(BLACK)
    
    for _ in range(50):
        star_x = random.randint(0, WIDTH)
        star_y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)
    
    # Mission result
    if is_new_high_score:
        result_text = title_font.render("NEW HIGH SCORE!", True, GOLD)
    else:
        result_text = title_font.render("MISSION FAILED", True, RED)
    screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, 60))
    
    # Player name and survival time
    name_display = score_font.render(f"Pilot: {player_name}", True, CYAN)
    screen.blit(name_display, (WIDTH // 2 - name_display.get_width() // 2, 150))
    
    # Format survival time
    minutes = int(survival_time // 60)
    seconds = int(survival_time % 60)
    time_display = score_font.render(f"Survival Time: {minutes:02d}:{seconds:02d}", True, GREEN)
    screen.blit(time_display, (WIDTH // 2 - time_display.get_width() // 2, 200))
    
    # Show player's best time if they have one
    if player_best_time > 0:
        best_minutes = int(player_best_time // 60)
        best_seconds = int(player_best_time % 60)
        best_text = font.render(f"Your Best: {best_minutes:02d}:{best_seconds:02d}", True, YELLOW)
        screen.blit(best_text, (WIDTH // 2 - best_text.get_width() // 2, 250))
    
    # Show if this is a new high score
    if is_new_high_score:
        high_score_text = font.render("Congratulations! You made it to the Top 3!", True, GOLD)
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 300))
    
    # Smartness reached
    smartness = int((enemy_evasion_skill + enemy_prediction_skill)/2 * 100)
    smart_text = font.render(f"Alien Smartness Reached: {smartness}%", True, YELLOW)
    screen.blit(smart_text, (WIDTH // 2 - smart_text.get_width() // 2, 350))
    
    # Instructions
    continue_text = font.render("Press R to view Leaderboard", True, WHITE)
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 80))
    
    quit_text = font.render("Press Q to Quit", True, WHITE)
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT - 40))

def draw_leaderboard():
    """Draw the leaderboard showing top 5 players by survival time"""
    try:
        leaderboard_df = pd.read_csv('survival_leaderboard.csv')
        if leaderboard_df.empty:
            no_data_text = font.render("No survival records yet! Be the first!", True, WHITE)
            screen.blit(no_data_text, (WIDTH // 2 - no_data_text.get_width() // 2, HEIGHT // 2))
            return
        
        # Sort by Survival_Time (descending)
        leaderboard_df = leaderboard_df.sort_values('Survival_Time', ascending=False).head(5)
        
        screen.fill(BLACK)
        
        # Draw stars background
        for _ in range(50):
            star_x = random.randint(0, WIDTH)
            star_y = random.randint(0, HEIGHT)
            pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)
        
        # Leaderboard box
        leaderboard_width = 500
        leaderboard_height = 400
        leaderboard_x = WIDTH // 2 - leaderboard_width // 2
        leaderboard_y = 80
        
        leaderboard_rect = pygame.Rect(leaderboard_x, leaderboard_y, leaderboard_width, leaderboard_height)
        pygame.draw.rect(screen, (20, 20, 40, 240), leaderboard_rect)
        pygame.draw.rect(screen, PURPLE, leaderboard_rect, 3)
        
        leaderboard_title = title_font.render("SURVIVAL LEADERBOARD", True, CYAN)
        screen.blit(leaderboard_title, (WIDTH // 2 - leaderboard_title.get_width() // 2, leaderboard_y + 20))
        
        # Column headers
        headers = font.render("Rank  Pilot Name           Survival Time", True, YELLOW)
        screen.blit(headers, (leaderboard_x + 60, leaderboard_y + 80))
        
        pygame.draw.line(screen, CYAN, (leaderboard_x + 60, leaderboard_y + 110), 
                        (leaderboard_x + leaderboard_width - 60, leaderboard_y + 110), 2)
        
        # Display top 5 players
        for i, (_, row) in enumerate(leaderboard_df.iterrows()):
            if i == 0:
                rank_color = GOLD
                rank_symbol = "🥇"
            elif i == 1:
                rank_color = SILVER
                rank_symbol = "🥈"
            elif i == 2:
                rank_color = BRONZE
                rank_symbol = "🥉"
            else:
                rank_color = WHITE
                rank_symbol = f"{i+1}."
            
            rank_text = small_font.render(f"{rank_symbol}", True, rank_color)
            
            player_display_name = row['Name'][:18]  # Slightly longer display
            name_text = font.render(player_display_name, True, rank_color)
            
            # Format survival time
            survival_seconds = row['Survival_Time']
            minutes = int(survival_seconds // 60)
            seconds = int(survival_seconds % 60)
            time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, rank_color)
            
            y_pos = leaderboard_y + 120 + i * 50
            
            screen.blit(rank_text, (leaderboard_x + 70, y_pos))
            screen.blit(name_text, (leaderboard_x + 120, y_pos))
            screen.blit(time_text, (leaderboard_x + leaderboard_width - 120 - time_text.get_width(), y_pos))
            
            # Highlight current player
            if row['Name'] == player_name:
                highlight_text = small_font.render("(YOU)", True, GREEN)
                screen.blit(highlight_text, (leaderboard_x + leaderboard_width - 70, y_pos))
        
        # Instructions
        restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT - 60))
                
    except Exception as e:
        error_text = font.render("Could not load leaderboard", True, RED)
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2))

def draw_pause_menu():
    """Draw the pause menu with resume and quit options"""
    # Create semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Pause menu box
    menu_width = 400
    menu_height = 300
    menu_x = WIDTH // 2 - menu_width // 2
    menu_y = HEIGHT // 2 - menu_height // 2
    
    pygame.draw.rect(screen, DARK_GRAY, (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(screen, CYAN, (menu_x, menu_y, menu_width, menu_height), 3)
    
    # Pause title
    pause_title = pause_font.render("PAUSED", True, YELLOW)
    screen.blit(pause_title, (WIDTH // 2 - pause_title.get_width() // 2, menu_y + 40))
    
    # Draw options
    for i, option in enumerate(pause_options):
        color = YELLOW if i == selected_option else WHITE
        
        # Draw selection indicator
        if i == selected_option:
            pygame.draw.polygon(screen, CYAN, [
                (menu_x + 80, menu_y + 140 + i * 60),
                (menu_x + 70, menu_y + 135 + i * 60),
                (menu_x + 70, menu_y + 145 + i * 60)
            ])
        
        option_text = pause_font.render(option, True, color)
        screen.blit(option_text, (menu_x + 100, menu_y + 130 + i * 60))
    
    # Instructions
    inst_text = small_font.render("Use ARROW KEYS to select, ENTER to confirm", True, LIGHT_GRAY)
    screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, menu_y + 250))

def draw_game_interface():
    """Draw all game interface elements in a clean layout"""
    # Format survival time for display
    minutes = int(survival_time // 60)
    seconds = int(survival_time % 60)
    
    # LEFT SIDE - Game stats
    time_text = font.render(f"Survival Time: {minutes:02d}:{seconds:02d}", True, WHITE)
    screen.blit(time_text, (10, 10))
    
    enemy_count_text = font.render(f"Aliens: {len(enemies)}", True, CYAN)
    screen.blit(enemy_count_text, (10, 40))
    
    smartness = int((enemy_evasion_skill + enemy_prediction_skill)/2 * 100)
    smartness_text = font.render(f"Alien Smartness: {smartness}%", True, YELLOW)
    screen.blit(smartness_text, (10, 70))
    
    # Difficulty timer
    next_increase = max(0, difficulty_increase_timer - (time.time() - last_difficulty_increase))
    if next_increase > 0:
        diff_text = font.render(f"Smartness increase in: {next_increase:.0f}s", True, CYAN)
        screen.blit(diff_text, (10, 100))
    
    # RIGHT SIDE - Health bar and controls
    # Health bar at top right
    draw_health_bar()
    
    # Controls below health bar, properly spaced
    shoot_text = font.render("Press R to Shoot", True, YELLOW)
    screen.blit(shoot_text, (WIDTH - shoot_text.get_width() - 10, 45))
    
    esc_text = font.render("Press ESC to Pause", True, ORANGE)
    screen.blit(esc_text, (WIDTH - esc_text.get_width() - 10, 75))
    
    # Boss alerts and timers (center)
    if boss_alert_timer > 0 and time.time() - boss_alert_timer < 3:
        alert_text = title_font.render("MOTHERSHIP INCOMING!", True, RED)
        screen.blit(alert_text, (WIDTH // 2 - alert_text.get_width() // 2, HEIGHT // 2 - 50))
    
    if not boss_active:
        next_boss = max(0, boss_spawn_interval - (time.time() - boss_spawn_timer))
        if next_boss > 0:
            boss_timer_text = font.render(f"Next Mothership: {next_boss:.0f}s", True, ORANGE)
            screen.blit(boss_timer_text, (WIDTH // 2 - boss_timer_text.get_width() // 2, HEIGHT - 40))

def save_player_data():
    """Save player data only if they are in top 3"""
    global df, is_new_high_score, player_best_time
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        df = pd.read_csv('survival_leaderboard.csv')
    except:
        df = pd.DataFrame(columns=['Name', 'Survival_Time', 'Date'])
    
    # Get current top times
    top_times = []
    if not df.empty:
        sorted_df = df.sort_values('Survival_Time', ascending=False)
        top_times = sorted_df['Survival_Time'].head(3).tolist()
    
    # Check if player exists
    player_exists = player_name in df['Name'].values
    
    if player_exists:
        player_idx = df[df['Name'] == player_name].index[0]
        current_survival_time = df.loc[player_idx, 'Survival_Time']
        player_best_time = current_survival_time
        
        # Only update if new survival time is longer AND it puts them in top 3
        if survival_time > current_survival_time:
            # Check if this would put them in top 3
            if len(top_times) < 3 or survival_time > min(top_times):
                df.loc[player_idx, 'Survival_Time'] = survival_time
                df.loc[player_idx, 'Date'] = current_date
                is_new_high_score = True
                player_best_time = survival_time
            else:
                is_new_high_score = False
        else:
            is_new_high_score = False
    else:
        # New player - check if they make it to top 3
        if len(top_times) < 3 or survival_time > min(top_times):
            new_player = pd.DataFrame({
                'Name': [player_name],
                'Survival_Time': [survival_time],
                'Date': [current_date]
            })
            df = pd.concat([df, new_player], ignore_index=True)
            is_new_high_score = True
            player_best_time = survival_time
        else:
            is_new_high_score = False
            player_best_time = 0
    
    df.to_csv('survival_leaderboard.csv', index=False)

def increase_difficulty():
    """Increase game difficulty every minute - aliens get smarter!"""
    global enemy_shoot_chance, enemy_spawn_delay, enemy_current_speed, last_difficulty_increase
    global enemy_evasion_skill, enemy_prediction_skill
    current_time = time.time()
    
    if current_time - last_difficulty_increase >= difficulty_increase_timer:
        enemy_evasion_skill = min(0.8, enemy_evasion_skill + 0.15)
        enemy_prediction_skill = min(0.9, enemy_prediction_skill + 0.2)
        
        enemy_shoot_chance = min(0.03, enemy_shoot_chance * 1.4)
        enemy_spawn_delay = max(25, enemy_spawn_delay * 0.85)
        enemy_current_speed = min(4.5, enemy_current_speed * 1.15)
        
        last_difficulty_increase = current_time
        return True
    return False

def reset_game():
    global player_x, player_y, enemies, power_ups, game_start_time, survival_time
    global power_up_spawn_timer, enemy_spawn_timer, boss_spawn_timer
    global enemy_current_speed, enemy_shoot_chance, enemy_spawn_delay, last_difficulty_increase
    global player_health, bullets, enemy_bullets, boss_bullets, enemy_evasion_skill, enemy_prediction_skill
    global boss_active, boss, boss_alert_timer, is_new_high_score, player_best_time, selected_option
    
    player_x = WIDTH // 2 - player_width // 2
    player_y = HEIGHT - player_height - 20
    player_health = 100
    
    enemies = []
    power_ups = []
    bullets = []
    enemy_bullets = []
    boss_bullets = []
    
    game_start_time = time.time()
    survival_time = 0
    
    enemy_spawn_timer = 0
    power_up_spawn_timer = 0
    boss_spawn_timer = 0
    
    enemy_current_speed = enemy_base_speed
    enemy_shoot_chance = 0.005
    enemy_spawn_delay = 45
    enemy_evasion_skill = 0.0
    enemy_prediction_skill = 0.0
    
    last_difficulty_increase = time.time()
    
    boss_active = False
    boss = None
    boss_alert_timer = 0
    
    is_new_high_score = False
    player_best_time = 0
    selected_option = 0

# Main game loop
clock = pygame.time.Clock()
running = True
boss = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == SHOW_RULES:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                game_state = NAME_INPUT
        
        elif game_state == NAME_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name:
                    game_state = PLAYING
                    game_start_time = time.time()
                    last_difficulty_increase = time.time()
                    boss_spawn_timer = time.time()
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if event.unicode.isalnum() and len(player_name) < 15:
                        player_name += event.unicode
        
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = PAUSED
                    selected_option = 0
        
        elif game_state == PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(pause_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(pause_options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:  # RESUME
                        game_state = PLAYING
                    else:  # QUIT TO MENU
                        reset_game()
                        player_name = ""
                        game_state = SHOW_RULES
        
        elif game_state == SHOW_SCORE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = SHOW_LEADERBOARD
                elif event.key == pygame.K_q:
                    running = False
        
        elif game_state == SHOW_LEADERBOARD:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    player_name = ""
                    game_state = SHOW_RULES
                elif event.key == pygame.K_q:
                    running = False
        
        elif game_state == GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = SHOW_SCORE
                elif event.key == pygame.K_q:
                    running = False
    
    if game_state == SHOW_RULES:
        draw_rules_screen()
    
    elif game_state == NAME_INPUT:
        draw_name_input_screen()
    
    elif game_state == SHOW_SCORE:
        draw_score_screen()
    
    elif game_state == SHOW_LEADERBOARD:
        draw_leaderboard()
    
    elif game_state == GAME_OVER:
        # Save player data and show score screen
        save_player_data()
        game_state = SHOW_SCORE
    
    elif game_state == PAUSED:
        # Continue drawing the game in the background
        # Draw game elements
        screen.fill(BLACK)
        
        for _ in range(10):
            star_x = random.randint(0, WIDTH)
            star_y = random.randint(0, HEIGHT)
            pygame.draw.circle(screen, WHITE, (star_x, star_y), random.randint(1, 2))
        
        draw_player()
        
        for enemy in enemies:
            enemy.draw()
        
        if boss_active and boss:
            boss.draw()
        
        for power_up in power_ups:
            power_up.draw()
        
        for bullet in bullets:
            bullet.draw()
        
        for bullet in enemy_bullets:
            bullet.draw()
        
        for bullet in boss_bullets:
            bullet.draw()
        
        # Draw game interface
        draw_game_interface()
        
        # Draw pause menu on top
        draw_pause_menu()
    
    elif game_state == PLAYING:
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += player_speed
        
        shoot_cooldown += 1
        if keys[pygame.K_r] and shoot_cooldown >= shoot_delay:
            bullets.append(Bullet(player_x + player_width // 2 - bullet_width // 2, player_y))
            shoot_cooldown = 0
        
        survival_time = time.time() - game_start_time
        
        if increase_difficulty():
            pass
        
        enemy_spawn_timer += 1
        if enemy_spawn_timer >= enemy_spawn_delay:
            spawn_enemy()
            enemy_spawn_timer = 0
        
        power_up_spawn_timer += 1
        if power_up_spawn_timer >= power_up_spawn_delay:
            spawn_power_up()
            power_up_spawn_timer = 0
        
        if not boss_active and time.time() - boss_spawn_timer >= boss_spawn_interval:
            boss = Boss()
            boss_active = True
            boss_spawn_timer = time.time()
        
        time_to_boss = boss_spawn_interval - (time.time() - boss_spawn_timer)
        if time_to_boss <= 10 and time_to_boss > 7 and not boss_active:
            boss_alert_timer = time.time()
        
        if boss_active and boss:
            boss.update()
            
            boss_bullet_list = boss.shoot()
            if boss_bullet_list:
                boss_bullets.extend(boss_bullet_list)
            
            if boss.health <= 0:
                boss_active = False
                boss = None
        
        for enemy in enemies[:]:
            if enemy.update(player_x, player_y):
                enemies.remove(enemy)
            
            enemy_bullet = enemy.shoot(player_x, player_y)
            if enemy_bullet:
                enemy_bullets.append(enemy_bullet)
        
        for bullet in bullets[:]:
            if bullet.update():
                bullets.remove(bullet)
            else:
                for enemy in enemies[:]:
                    if bullet.collides_with(enemy.x, enemy.y, enemy_width, enemy_height):
                        if bullet in bullets:
                            bullets.remove(bullet)
                        enemies.remove(enemy)
                        break
                
                if boss_active and boss and bullet.collides_with(boss.x, boss.y, boss_width, boss_height):
                    if bullet in bullets:
                        bullets.remove(bullet)
                    boss.health -= 5
        
        for bullet in enemy_bullets[:]:
            if bullet.update():
                enemy_bullets.remove(bullet)
            elif bullet.collides_with(player_x, player_y, player_width, player_height):
                if bullet in enemy_bullets:
                    enemy_bullets.remove(bullet)
                player_health -= 5
                if player_health <= 0:
                    game_state = GAME_OVER
        
        for bullet in boss_bullets[:]:
            if bullet.update():
                boss_bullets.remove(bullet)
            elif bullet.collides_with(player_x, player_y, player_width, player_height):
                if bullet in boss_bullets:
                    boss_bullets.remove(bullet)
                player_health -= 10
                if player_health <= 0:
                    game_state = GAME_OVER
        
        for enemy in enemies[:]:
            if enemy.collides_with(player_x, player_y, player_width, player_height):
                enemies.remove(enemy)
                player_health -= 10
                if player_health <= 0:
                    game_state = GAME_OVER
        
        if boss_active and boss and boss.collides_with(player_x, player_y, player_width, player_height):
            player_health -= 20
            if player_health <= 0:
                game_state = GAME_OVER
        
        for power_up in power_ups[:]:
            if power_up.update():
                power_ups.remove(power_up)
            elif power_up.collides_with(player_x, player_y, player_width, player_height):
                power_ups.remove(power_up)
                player_health = min(100, player_health + power_up_health_boost)
        
        screen.fill(BLACK)
        
        for _ in range(10):
            star_x = random.randint(0, WIDTH)
            star_y = random.randint(0, HEIGHT)
            pygame.draw.circle(screen, WHITE, (star_x, star_y), random.randint(1, 2))
        
        draw_player()
        
        for enemy in enemies:
            enemy.draw()
        
        if boss_active and boss:
            boss.draw()
        
        for power_up in power_ups:
            power_up.draw()
        
        for bullet in bullets:
            bullet.draw()
        
        for bullet in enemy_bullets:
            bullet.draw()
        
        for bullet in boss_bullets:
            bullet.draw()
        
        # Draw game interface with clean layout
        draw_game_interface()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()