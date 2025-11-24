import pygame
import random
import math
import sys
import time  # Added for time tracking

# --- Configuration & Constants ---
FPS = 60
TIME_LIMIT_SECONDS = 15 * 60  # 15 Minutes

# Colors (Sleek, minimalist palette)
BG_COLOR = (40, 44, 52)       # Dark Slate/Blue-Grey
TEXT_COLOR = (220, 223, 228)  # Off-white
INPUT_BG_COLOR = (60, 64, 72) # Lighter grey for input box
TARGET_COLORS = [
    (255, 107, 107),  # Pastel Red
    (78, 205, 196),   # Pastel Teal
    (255, 230, 109),  # Pastel Yellow
    (168, 230, 207),  # Mint
    (255, 159, 67)    # Orange
]
PARTICLE_COLORS = [
    (255, 255, 255), (255, 230, 109), (78, 205, 196)
]

# --- Helper Classes ---

class Particle:
    """A small piece of confetti that explodes when a target is clicked."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        # Random velocity
        speed = random.uniform(2, 6)
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 40) # Frames to live
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(0, self.size - 0.1) # Shrink over time

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class Target:
    """The circle the user needs to click."""
    def __init__(self, level, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # -- Difficulty Scaling --
        # Radius: Starts big (120px), ends smaller (40px)
        self.radius = int(120 - (level * 1.6)) 
        if self.radius < 40: self.radius = 40
        
        # Speed: Starts 0, slowly increases after level 20
        self.speed = 0
        if level > 20:
            self.speed = (level - 20) * 0.15
        
        # Spawn logic to keep circle fully on screen
        padding = self.radius + 50
        self.x = random.randint(padding, screen_w - padding)
        self.y = random.randint(padding, screen_h - padding)
        
        # Movement direction (bounce logic)
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.choice([-1, 1]) * self.speed
        
        self.color = random.choice(TARGET_COLORS)
        self.is_clicked = False
        
        # Animation for spawning (pop-in effect)
        self.current_radius = 0
        self.animation_speed = 10

    def update(self):
        # Spawn animation
        if self.current_radius < self.radius:
            self.current_radius += self.animation_speed
            if self.current_radius > self.radius:
                self.current_radius = self.radius

        # Movement logic
        self.x += self.dx
        self.y += self.dy

        # Bounce off walls
        if self.x - self.radius < 0 or self.x + self.radius > self.screen_w:
            self.dx *= -1
        if self.y - self.radius < 0 or self.y + self.radius > self.screen_h:
            self.dy *= -1

    def draw(self, surface):
        # Draw a slight shadow/glow
        pygame.draw.circle(surface, (30, 30, 30), (int(self.x)+5, int(self.y)+5), int(self.current_radius))
        # Draw main circle
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.current_radius))
        
        # Draw a simple concentric ring for "target" look
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(self.current_radius * 0.7), 3)

    def check_click(self, pos):
        # Distance formula
        distance = math.sqrt((pos[0] - self.x)**2 + (pos[1] - self.y)**2)
        return distance <= self.radius

# --- Main Game Class ---

class Game:
    def __init__(self):
        pygame.init()
        # Set Fullscreen Mode
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Mouse Master Junior")
        self.clock = pygame.time.Clock()
        
        # Fonts
        try:
            self.font_huge = pygame.font.SysFont("arialrounded", 100, bold=True)
            self.font_large = pygame.font.SysFont("arialrounded", 60, bold=True)
            self.font_small = pygame.font.SysFont("arial", 30)
        except:
            self.font_huge = pygame.font.SysFont(None, 100)
            self.font_large = pygame.font.SysFont(None, 60)
            self.font_small = pygame.font.SysFont(None, 30)

        self.level = 1
        self.max_levels = 50
        self.target = None
        self.particles = []
        
        # Game State Management
        self.state = "SETUP" # SETUP, START, PLAYING, WIN, LOCKED
        self.previous_state = "START"
        
        # Parental Control
        self.secret_answer = ""
        self.input_buffer = ""
        self.session_start_time = None
        
    def start_level(self):
        self.target = Target(self.level, self.width, self.height)
        self.particles = []

    def create_particles(self, x, y, color):
        for _ in range(20): 
            self.particles.append(Particle(x, y, color))

    def draw_text_centered(self, text, font, y_offset=0, color=TEXT_COLOR):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(self.width // 2, self.height // 2 + y_offset))
        self.screen.blit(surface, rect)

    def draw_input_box(self):
        # Draw box
        box_width, box_height = 400, 60
        box_x = (self.width - box_width) // 2
        box_y = (self.height // 2) + 50
        pygame.draw.rect(self.screen, INPUT_BG_COLOR, (box_x, box_y, box_width, box_height), border_radius=10)
        pygame.draw.rect(self.screen, TARGET_COLORS[1], (box_x, box_y, box_width, box_height), 2, border_radius=10)
        
        # Draw text input (masked if SETUP for password feel, or plain text)
        display_text = self.input_buffer
        text_surf = self.font_small.render(display_text, True, (255, 255, 255))
        self.screen.blit(text_surf, (box_x + 20, box_y + 15))

    def reset_timer(self):
        self.session_start_time = time.time()

    def run(self):
        running = True
        while running:
            current_time = time.time()
            
            # --- Timer Check ---
            if self.state in ["START", "PLAYING", "WIN"] and self.session_start_time:
                elapsed = current_time - self.session_start_time
                if elapsed >= TIME_LIMIT_SECONDS:
                    self.previous_state = self.state
                    self.state = "LOCKED"
                    self.input_buffer = ""

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                # Keyboard Input for Setup and Lock Screen
                if event.type == pygame.KEYDOWN:
                    if self.state in ["SETUP", "LOCKED"]:
                        if event.key == pygame.K_RETURN:
                            if self.state == "SETUP":
                                if self.input_buffer.strip() != "":
                                    self.secret_answer = self.input_buffer.strip()
                                    self.state = "START"
                                    self.reset_timer()
                                    self.input_buffer = ""
                            elif self.state == "LOCKED":
                                if self.input_buffer.strip() == self.secret_answer:
                                    self.state = self.previous_state
                                    self.reset_timer()
                                    self.input_buffer = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_buffer = self.input_buffer[:-1]
                        else:
                            # Add typing limits
                            if len(self.input_buffer) < 20:
                                self.input_buffer += event.unicode

                # Mouse Input for Game
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "START":
                        self.state = "PLAYING"
                        self.start_level()
                    
                    elif self.state == "PLAYING":
                        if self.target.check_click(event.pos):
                            self.create_particles(self.target.x, self.target.y, self.target.color)
                            self.level += 1
                            if self.level > self.max_levels:
                                self.state = "WIN"
                            else:
                                self.start_level()
                    
                    elif self.state == "WIN":
                        self.level = 1
                        self.state = "START"

            # 2. Updates
            if self.state == "PLAYING":
                self.target.update()
            
            for p in self.particles[:]:
                p.update()
                if p.life <= 0:
                    self.particles.remove(p)

            # 3. Drawing
            self.screen.fill(BG_COLOR)

            if self.state == "SETUP":
                self.draw_text_centered("PARENT SETUP", self.font_large, -100)
                self.draw_text_centered("Set a Secret Answer/PIN to unlock:", self.font_small, -30)
                self.draw_input_box()
                self.draw_text_centered("Press ENTER to Save", self.font_small, 150, (150, 150, 150))

            elif self.state == "LOCKED":
                # Darker overlay feel
                self.screen.fill((20, 22, 26)) 
                self.draw_text_centered("TIME'S UP!", self.font_large, -100, TARGET_COLORS[0])
                self.draw_text_centered("Ask a parent to type the Secret Answer:", self.font_small, -30)
                self.draw_input_box()
                self.draw_text_centered("Press ENTER to Unlock", self.font_small, 150, (150, 150, 150))

            elif self.state == "START":
                self.draw_text_centered("MOUSE MASTER", self.font_large, -50)
                self.draw_text_centered("Click to Start", self.font_small, 50, (150, 150, 150))
                
            elif self.state == "PLAYING":
                # Draw Progress Bar
                bar_width = 800
                bar_height = 20
                progress = (self.level - 1) / self.max_levels
                pygame.draw.rect(self.screen, (30, 34, 40), 
                                 ((self.width - bar_width)//2, 50, bar_width, bar_height), border_radius=10)
                if progress > 0:
                    pygame.draw.rect(self.screen, TARGET_COLORS[1], 
                                     ((self.width - bar_width)//2, 50, bar_width * progress, bar_height), border_radius=10)
                
                level_text = self.font_large.render(f"{self.level}", True, (255, 255, 255))
                self.screen.blit(level_text, (50, 30))
                self.target.draw(self.screen)

            elif self.state == "WIN":
                self.draw_text_centered("YOU DID IT!", self.font_huge, -50, TARGET_COLORS[2])
                self.draw_text_centered("Great Mouse Control!", self.font_small, 50)
                self.draw_text_centered("Click to Play Again", self.font_small, 100, (150, 150, 150))

            # Draw particles
            for p in self.particles:
                p.draw(self.screen)

            # Custom Cursor (visible in game modes)
            if self.state not in ["SETUP", "LOCKED"]:
                mouse_pos = pygame.mouse.get_pos()
                pygame.draw.circle(self.screen, (255, 255, 255), mouse_pos, 10, 2)
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
