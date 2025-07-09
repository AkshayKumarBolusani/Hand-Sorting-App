import cv2
import mediapipe as mp
import numpy as np
import pygame
import sys
import time
import json
import os
from settings import Settings
from food_manager import FoodManager
from logger import GameLogger
from audio_feedback import AudioFeedback
from threading import Thread
from PIL import Image
import traceback
from ui_utils import draw_rounded_rect, draw_gradient, draw_shadow, animate_value

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
CIRCLE_RADIUS = 150
FOOD_ICON_SIZE = 80
DROP_ZONE_SIZE = 180
FPS = 30

# --- Helper Functions ---
def load_food_images(food_items):
    images = []
    for item in food_items:
        try:
            img = pygame.image.load(item['image'])
            img = pygame.transform.smoothscale(img, (FOOD_ICON_SIZE, FOOD_ICON_SIZE))
        except Exception:
            img = pygame.Surface((FOOD_ICON_SIZE, FOOD_ICON_SIZE))
            img.fill((200, 200, 200))
        images.append(img)
    return images

def draw_circular_menu(screen, center, food_images, food_items, selected_idx, angle_offset):
    n = len(food_images)
    for i, (img, item) in enumerate(zip(food_images, food_items)):
        angle = 2 * np.pi * i / n + angle_offset
        x = int(center[0] + CIRCLE_RADIUS * np.cos(angle))
        y = int(center[1] + CIRCLE_RADIUS * np.sin(angle))
        color = (0, 200, 0) if item['type'] == 'veg' else (200, 0, 0)
        pygame.draw.circle(screen, color, (x, y), FOOD_ICON_SIZE // 2 + 8, 0)
        screen.blit(img, (x - FOOD_ICON_SIZE // 2, y - FOOD_ICON_SIZE // 2))
        if i == selected_idx:
            pygame.draw.circle(screen, (255, 255, 0), (x, y), FOOD_ICON_SIZE // 2 + 12, 4)

def draw_drop_zones(screen):
    # Veg box (top)
    veg_rect = (40, SCREEN_HEIGHT//2 - DROP_ZONE_SIZE - 20, DROP_ZONE_SIZE, DROP_ZONE_SIZE)
    nonveg_rect = (40, SCREEN_HEIGHT//2 + 20, DROP_ZONE_SIZE, DROP_ZONE_SIZE)
    pygame.draw.rect(screen, (0, 200, 0), veg_rect, 0, 20)
    pygame.draw.rect(screen, (200, 0, 0), nonveg_rect, 0, 20)
    font = pygame.font.SysFont(None, 48)
    veg_text = font.render('VEG', True, (255,255,255))
    nonveg_text = font.render('NON-VEG', True, (255,255,255))
    screen.blit(veg_text, (veg_rect[0]+20, veg_rect[1]+veg_rect[3]//2-24))
    screen.blit(nonveg_text, (nonveg_rect[0]+20, nonveg_rect[1]+nonveg_rect[3]//2-24))
    return veg_rect, nonveg_rect

# --- Confetti and Emoji Rain ---
import random
class Confetti:
    def __init__(self):
        self.particles = []
    def spawn(self, x, y, color):
        for _ in range(30):
            angle = random.uniform(0, 2*np.pi)
            speed = random.uniform(4, 8)
            self.particles.append({
                'x': x, 'y': y,
                'vx': speed*np.cos(angle),
                'vy': speed*np.sin(angle),
                'color': color,
                'life': random.randint(20, 40)
            })
    def update(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3  # gravity
            p['life'] -= 1
        self.particles = [p for p in self.particles if p['life'] > 0]
    def draw(self, screen):
        for p in self.particles:
            pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), 6)

class EmojiRain:
    def __init__(self, emoji_img):
        self.drops = []
        self.emoji_img = emoji_img
    def spawn(self, happy=False):
        for _ in range(10):
            x = random.randint(0, SCREEN_WIDTH-40)
            self.drops.append({'x': x, 'y': -40, 'vy': random.uniform(4,8), 'happy': happy})
    def update(self):
        for d in self.drops:
            d['y'] += d['vy']
        self.drops = [d for d in self.drops if d['y'] < SCREEN_HEIGHT+40]
    def draw(self, screen):
        for d in self.drops:
            screen.blit(self.emoji_img, (int(d['x']), int(d['y'])))

# --- Main Game Class ---
class HandSortingGame:
    def __init__(self):
        try:
            self.settings = Settings()
            self.timer_setting = self.settings.game_duration
            self.food_manager = FoodManager(self.settings.food_items_file)
            self.logger = GameLogger()
            self.audio = AudioFeedback(enabled=self.settings.sound_on)
            self.score = 0
            self.selected_idx = 0
            self.angle_offset = 0
            self.dragging = False
            self.dragged_idx = None
            self.feedback = ''
            self.feedback_color = (0,0,0)
            self.feedback_time = 0
            self.start_time = None
            self.time_left = self.settings.game_duration
            self.running = True
            self.menu_buttons = [
                {'label': 'Start', 'action': 'start'},
                {'label': 'Settings', 'action': 'settings'},
                {'label': 'Quit', 'action': 'quit'}
            ]
            self.selected_menu = 0
            self.show_settings = False
            self.selected_food_setting = 0
            self.menu_center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            self.drag_pos = None
            self.last_left_hand = None
            self.last_right_hand = None
            self.confetti = Confetti()
            sad_emoji_path = os.path.join(os.path.dirname(__file__), 'images', 'sad_emoji.png')
            happy_emoji_path = os.path.join(os.path.dirname(__file__), 'images', 'happy_emoji.png')
            try:
                self.sad_emoji_img = pygame.image.load(sad_emoji_path)
                self.sad_emoji_img = pygame.transform.smoothscale(self.sad_emoji_img, (40, 40))
            except Exception:
                self.sad_emoji_img = pygame.Surface((40,40))
                self.sad_emoji_img.fill((200,200,200))
            try:
                self.happy_emoji_img = pygame.image.load(happy_emoji_path)
                self.happy_emoji_img = pygame.transform.smoothscale(self.happy_emoji_img, (40, 40))
            except Exception:
                self.happy_emoji_img = pygame.Surface((40,40))
                self.happy_emoji_img.fill((255,255,0))
            self.emoji_rain = EmojiRain(self.sad_emoji_img)
            self.happy_rain = EmojiRain(self.happy_emoji_img)
            self.state = 'menu'  # menu, playing, paused, gameover
            self.error_message = ''
            self.hand_present = False
            self.food_images = load_food_images(self.food_manager.food_items)
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise Exception('Camera not available or permission denied.')
            except Exception as e:
                self.error_message = str(e)
                self.cap = None
            self.clock = None
            self.screen = None
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)
        except Exception as e:
            self.error_message = f'Initialization error: {e}'
            self.state = 'error'

    def run(self):
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption('Hand-Tracking Food Sorting Game')
            self.clock = pygame.time.Clock()
            self.start_time = time.time()
            while self.running:
                try:
                    self.handle_events()
                    if self.state == 'menu':
                        self.render_menu()
                    elif self.state == 'playing':
                        if self.cap:
                            ret, frame = self.cap.read()
                            if not ret:
                                self.error_message = 'Camera frame not available.'
                                self.state = 'error'
                                continue
                            frame = cv2.flip(frame, 1)
                            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            results = self.hands.process(rgb)
                            hand_landmarks = results.multi_hand_landmarks
                            handedness = results.multi_handedness
                            self.hand_present = bool(hand_landmarks)
                            self.process_hands(hand_landmarks, handedness)
                            self.update_game()
                            self.render(frame)
                            if self.time_left <= 0:
                                self.state = 'gameover'
                        else:
                            self.state = 'error'
                    elif self.state == 'paused':
                        self.render_pause()
                    elif self.state == 'gameover':
                        self.render_gameover()
                    elif self.state == 'error':
                        self.render_error()
                    elif self.state == 'settings':
                        self.render_settings()
                    pygame.display.flip()
                    self.clock.tick(FPS)
                except Exception as e:
                    self.error_message = f'Unexpected error: {e}\n' + traceback.format_exc()
                    self.state = 'error'
            if self.cap:
                self.cap.release()
            pygame.quit()
        except Exception as e:
            print(f'Critical error: {e}')

    def handle_events(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == 'menu':
                        if event.key == pygame.K_UP:
                            self.selected_menu = (self.selected_menu - 1) % len(self.menu_buttons)
                        elif event.key == pygame.K_DOWN:
                            self.selected_menu = (self.selected_menu + 1) % len(self.menu_buttons)
                        elif event.key == pygame.K_RETURN:
                            action = self.menu_buttons[self.selected_menu]['action']
                            if action == 'start':
                                self.reset_game()
                                self.state = 'playing'
                            elif action == 'settings':
                                self.state = 'settings'
                            elif action == 'quit':
                                self.running = False
                    elif self.state == 'paused':
                        if event.key == pygame.K_RETURN:
                            self.state = 'playing'
                    elif self.state == 'gameover':
                        if event.key == pygame.K_RETURN:
                            self.state = 'menu'
                    elif self.state == 'error':
                        if event.key == pygame.K_RETURN:
                            self.state = 'menu'
                    elif self.state == 'playing':
                        if event.key == pygame.K_ESCAPE:
                            self.state = 'paused'
                    elif self.state == 'settings':
                        if event.key == pygame.K_ESCAPE:
                            self.settings.game_duration = self.timer_setting
                            self.settings.save()
                            self.state = 'menu'
                        elif event.key == pygame.K_UP:
                            if self.food_manager.food_items:
                                self.selected_food_setting = (self.selected_food_setting - 1) % len(self.food_manager.food_items)
                        elif event.key == pygame.K_DOWN:
                            if self.food_manager.food_items:
                                self.selected_food_setting = (self.selected_food_setting + 1) % len(self.food_manager.food_items)
                        elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                            if self.food_manager.food_items:
                                self.remove_selected_food_item()
                        elif event.key == pygame.K_LEFT:
                            self.timer_setting = max(10, self.timer_setting - 10)
                        elif event.key == pygame.K_RIGHT:
                            self.timer_setting = min(600, self.timer_setting + 10)
                        elif event.key == pygame.K_v:
                            self.set_selected_food_type('veg')
                        elif event.key == pygame.K_n:
                            self.set_selected_food_type('non-veg')
                elif event.type == pygame.DROPFILE and self.state == 'settings':
                    image_path = event.file
                    self.add_food_item_via_settings(image_path)
        except Exception as e:
            self.error_message = f'Event handling error: {e}'
            self.state = 'error'

    def add_food_item_via_settings(self, image_path):
        try:
            name = os.path.splitext(os.path.basename(image_path))[0]
            type_ = 'veg'  # Default, user can edit later
            self.food_manager.add_food_item(name, image_path, type_)
            self.food_images = load_food_images(self.food_manager.food_items)
        except Exception as e:
            self.error_message = f'Error adding food item: {e}'
            self.state = 'error'

    def remove_selected_food_item(self):
        try:
            idx = self.selected_food_setting
            if idx is not None and 0 <= idx < len(self.food_manager.food_items):
                self.food_manager.remove_food_item(idx)
                del self.food_images[idx]
                if self.selected_food_setting >= len(self.food_manager.food_items):
                    self.selected_food_setting = max(0, len(self.food_manager.food_items)-1)
        except Exception as e:
            self.error_message = f'Error removing food item: {e}'
            self.state = 'error'

    def reset_game(self):
        try:
            self.food_manager.load()  # Reload food items from file
            self.food_images = load_food_images(self.food_manager.food_items)
            self.score = 0
            self.selected_idx = 0
            self.angle_offset = 0
            self.dragging = False
            self.dragged_idx = None
            self.feedback = ''
            self.feedback_color = (0,0,0)
            self.feedback_time = 0
            self.start_time = time.time()
            self.time_left = self.settings.game_duration
            self.menu_center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            self.drag_pos = None
            self.last_left_hand = None
            self.last_right_hand = None
            self.selected_food_setting = 0
        except Exception as e:
            self.error_message = f'Error resetting game: {e}'
            self.state = 'error'

    def process_hands(self, hand_landmarks, handedness):
        try:
            self.dragging = False
            if hand_landmarks and handedness:
                right_hand = None
                left_hand = None
                for i, (landmarks, hand) in enumerate(zip(hand_landmarks, handedness)):
                    label = hand.classification[0].label  # 'Left' or 'Right'
                    lm = [(lm.x, lm.y) for lm in landmarks.landmark]
                    lm_px = [(int(x * SCREEN_WIDTH), int(y * SCREEN_HEIGHT)) for x, y in lm]
                    if label == 'Right':
                        right_hand = (lm, lm_px)
                    elif label == 'Left':
                        left_hand = (lm, lm_px)
                # Right hand: open palm shows menu, wrist rotation controls circle (invert for opposite motion)
                if right_hand:
                    lm, lm_px = right_hand
                    if self.is_palm_open(lm):
                        cx, cy = lm_px[0]
                        wrist_angle = -self.get_wrist_angle(lm)  # invert for opposite motion
                        self.angle_offset = wrist_angle
                        self.menu_center = (cx, cy)
                        idx_tip = lm_px[8]
                        self.selected_idx = self.get_closest_menu_item(idx_tip, cx, cy)
                        self.last_right_hand = (lm, lm_px)
                # Left hand: grab and drag
                if left_hand:
                    lm, lm_px = left_hand
                    if self.is_grabbing(lm):
                        self.dragging = True
                        self.dragged_idx = self.selected_idx
                        self.drag_pos = lm_px[8]
                        self.last_left_hand = (lm, lm_px)
                    elif self.dragged_idx is not None:
                        drop_zone = self.get_drop_zone(self.drag_pos)
                        if drop_zone:
                            self.handle_drop(drop_zone)
                        self.dragged_idx = None
        except Exception as e:
            self.error_message = f'Hand processing error: {e}'
            self.state = 'error'

    def is_palm_open(self, lm):
        # Simple: if all finger tips are above their pip joints (y axis)
        return all(lm[tip][1] < lm[tip-2][1] for tip in [8, 12, 16, 20])

    def is_grabbing(self, lm):
        # Simple: if all finger tips are below their pip joints (y axis)
        return all(lm[tip][1] > lm[tip-2][1] for tip in [8, 12, 16, 20])

    def get_wrist_angle(self, lm):
        # Angle between wrist and index mcp
        x0, y0 = lm[0]
        x1, y1 = lm[5]
        return np.arctan2(y1-y0, x1-x0)

    def get_closest_menu_item(self, pos, cx, cy):
        n = len(self.food_manager.food_items)
        min_dist = float('inf')
        min_idx = 0
        for i in range(n):
            angle = 2 * np.pi * i / n + self.angle_offset
            x = int(cx + CIRCLE_RADIUS * np.cos(angle))
            y = int(cy + CIRCLE_RADIUS * np.sin(angle))
            dist = (pos[0]-x)**2 + (pos[1]-y)**2
            if dist < min_dist:
                min_dist = dist
                min_idx = i
        return min_idx

    def get_drop_zone(self, pos):
        x, y = pos
        veg_rect, nonveg_rect = (40, SCREEN_HEIGHT//2 - DROP_ZONE_SIZE - 20, DROP_ZONE_SIZE, DROP_ZONE_SIZE), (40, SCREEN_HEIGHT//2 + 20, DROP_ZONE_SIZE, DROP_ZONE_SIZE)
        if veg_rect[0] < x < veg_rect[0]+veg_rect[2] and veg_rect[1] < y < veg_rect[1]+veg_rect[3]:
            return 'veg'
        if nonveg_rect[0] < x < nonveg_rect[0]+nonveg_rect[2] and nonveg_rect[1] < y < nonveg_rect[1]+nonveg_rect[3]:
            return 'non-veg'
        return None

    def handle_drop(self, drop_zone):
        try:
            if self.dragged_idx is not None and 0 <= self.dragged_idx < len(self.food_manager.food_items):
                item = self.food_manager.food_items[self.dragged_idx]
                correct = (item['type'] == drop_zone)
                if correct:
                    self.score += 10
                    self.feedback = 'Correct!'
                    self.feedback_color = (0, 200, 0)
                    # Confetti at drop zone
                    if drop_zone == 'veg':
                        x, y = 40+DROP_ZONE_SIZE//2, SCREEN_HEIGHT//2 - DROP_ZONE_SIZE//2
                    else:
                        x, y = 40+DROP_ZONE_SIZE//2, SCREEN_HEIGHT//2 + DROP_ZONE_SIZE + 20
                    self.confetti.spawn(x, y, (0,200,0) if drop_zone=='veg' else (200,0,0))
                    self.happy_rain.spawn(happy=True)
                else:
                    self.score -= 5
                    self.feedback = 'Incorrect!'
                    self.feedback_color = (200, 0, 0)
                    self.emoji_rain.spawn()
                self.feedback_time = time.time()
                self.logger.log(item['name'], item['type'], drop_zone, self.feedback, self.score)
                Thread(target=self.audio.announce_feedback, args=(correct,)).start()
                # Remove the item from the menu after drop
                del self.food_manager.food_items[self.dragged_idx]
                del self.food_images[self.dragged_idx]
                self.dragged_idx = None
                # If no items left, end game
                if not self.food_manager.food_items:
                    self.state = 'gameover'
        except Exception as e:
            self.error_message = f'Error handling drop: {e}'
            self.state = 'error'

    def update_game(self):
        self.time_left = self.settings.game_duration - (time.time() - self.start_time)
        # Hide feedback after 1.5s
        if self.feedback and time.time() - self.feedback_time > 1.5:
            self.feedback = ''

    def render_menu(self):
        self.screen.fill((245, 245, 255))
        draw_gradient(self.screen, (0,0,SCREEN_WIDTH,SCREEN_HEIGHT), (100,180,255), (255,255,255))
        font = pygame.font.SysFont('Arial', 80, bold=True)
        title = font.render('Food Sorting Game', True, (30,30,60))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))
        for i, btn in enumerate(self.menu_buttons):
            rect = (SCREEN_WIDTH//2-150, 300+i*100, 300, 70)
            color = (80, 120, 200) if i == self.selected_menu else (200, 220, 255)
            draw_shadow(self.screen, rect, (0,0,0,60), (6,6), 30)
            draw_rounded_rect(self.screen, rect, color, 30)
            font2 = pygame.font.SysFont('Arial', 40, bold=True)
            label = font2.render(btn['label'], True, (30,30,60))
            self.screen.blit(label, (rect[0]+rect[2]//2-label.get_width()//2, rect[1]+rect[3]//2-label.get_height()//2))
        if self.error_message:
            font3 = pygame.font.SysFont('Arial', 28)
            err = font3.render(self.error_message, True, (200,0,0))
            self.screen.blit(err, (SCREEN_WIDTH//2-err.get_width()//2, SCREEN_HEIGHT-100))

    def render_pause(self):
        self.screen.fill((230,230,240))
        font = pygame.font.SysFont('Arial', 60, bold=True)
        text = font.render('Paused', True, (30,30,60))
        self.screen.blit(text, (SCREEN_WIDTH//2-text.get_width()//2, 200))
        font2 = pygame.font.SysFont('Arial', 36)
        msg = font2.render('Press Enter to resume', True, (80,80,120))
        self.screen.blit(msg, (SCREEN_WIDTH//2-msg.get_width()//2, 350))

    def render_gameover(self):
        self.screen.fill((255,255,255))
        font = pygame.font.SysFont('Arial', 70, bold=True)
        text = font.render('Game Over', True, (200,50,50))
        self.screen.blit(text, (SCREEN_WIDTH//2-text.get_width()//2, 120))
        font2 = pygame.font.SysFont('Arial', 40)
        score = font2.render(f'Final Score: {self.score}', True, (30,30,60))
        self.screen.blit(score, (SCREEN_WIDTH//2-score.get_width()//2, 250))
        msg = font2.render('Press Enter to return to menu', True, (80,80,120))
        self.screen.blit(msg, (SCREEN_WIDTH//2-msg.get_width()//2, 350))

    def render_error(self):
        self.screen.fill((255,240,240))
        font = pygame.font.SysFont('Arial', 60, bold=True)
        text = font.render('Error', True, (200,0,0))
        self.screen.blit(text, (SCREEN_WIDTH//2-text.get_width()//2, 120))
        font2 = pygame.font.SysFont('Arial', 28)
        lines = self.error_message.split('\n')
        for i, line in enumerate(lines):
            err = font2.render(line, True, (120,0,0))
            self.screen.blit(err, (80, 220+i*32))
        msg = font2.render('Press Enter to return to menu', True, (80,80,120))
        self.screen.blit(msg, (SCREEN_WIDTH//2-msg.get_width()//2, SCREEN_HEIGHT-100))

    def render_settings(self):
        self.screen.fill((240, 250, 255))
        font = pygame.font.SysFont('Arial', 60, bold=True)
        text = font.render('Settings', True, (30,30,60))
        self.screen.blit(text, (SCREEN_WIDTH//2-text.get_width()//2, 80))
        font2 = pygame.font.SysFont('Arial', 32)
        msg = font2.render('Drag and drop an image file to add a food item.', True, (80,80,120))
        self.screen.blit(msg, (SCREEN_WIDTH//2-msg.get_width()//2, 180))
        msg2 = font2.render('Press ESC to return to menu. Select item and press Delete to remove.', True, (80,80,120))
        self.screen.blit(msg2, (SCREEN_WIDTH//2-msg2.get_width()//2, 220))
        msg3 = font2.render('Press V for Veg, N for Non-Veg.', True, (80,80,120))
        self.screen.blit(msg3, (SCREEN_WIDTH//2-msg3.get_width()//2, 250))
        # Timer setting
        font3 = pygame.font.SysFont('Arial', 32, bold=True)
        timer_label = font3.render(f'Timer: {self.timer_setting} seconds  (←/→ to adjust)', True, (30,30,60))
        self.screen.blit(timer_label, (SCREEN_WIDTH//2-timer_label.get_width()//2, 290))
        # List food items
        font4 = pygame.font.SysFont('Arial', 28)
        for i, item in enumerate(self.food_manager.food_items):
            color = (30,30,60) if i != self.selected_food_setting else (255,255,255)
            if i == self.selected_food_setting:
                bg_rect = pygame.Rect(90, 325 + i*40, 500, 36)
                pygame.draw.rect(self.screen, (80,120,200), bg_rect, border_radius=10)
            label = font4.render(f"{item['name']} ({item['type']})", True, color)
            self.screen.blit(label, (100, 330 + i*40))

    def render(self, frame):
        try:
            # Convert OpenCV frame to pygame surface
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(pygame.transform.scale(frame, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))
            # Draw drop zones
            veg_rect, nonveg_rect = draw_drop_zones(self.screen)
            # Draw circular menu if right hand open
            if hasattr(self, 'menu_center'):
                draw_circular_menu(self.screen, self.menu_center, self.food_images, self.food_manager.food_items, self.selected_idx, self.angle_offset)
            # Draw dragged item
            if self.dragging and self.dragged_idx is not None:
                img = self.food_images[self.dragged_idx]
                x, y = self.drag_pos
                self.screen.blit(img, (x - FOOD_ICON_SIZE//2, y - FOOD_ICON_SIZE//2))
            # Draw score and timer
            draw_score_timer(self.screen, self.score, max(0, self.time_left))
            # Draw feedback
            if self.feedback:
                draw_feedback(self.screen, self.feedback, self.feedback_color)
            # Hand presence cue
            if not self.hand_present:
                font = pygame.font.SysFont('Arial', 36)
                msg = font.render('Show your hand to start interacting!', True, (80,80,120))
                self.screen.blit(msg, (SCREEN_WIDTH//2-msg.get_width()//2, SCREEN_HEIGHT-80))
            # Draw confetti and emoji rain
            self.confetti.update()
            self.confetti.draw(self.screen)
            self.emoji_rain.update()
            self.emoji_rain.draw(self.screen)
            self.happy_rain.update()
            self.happy_rain.draw(self.screen)
        except Exception as e:
            self.screen.fill((255,240,240))
            font = pygame.font.SysFont('Arial', 60, bold=True)
            text = font.render('Render Error', True, (200,0,0))
            self.screen.blit(text, (SCREEN_WIDTH//2-text.get_width()//2, 120))
            font2 = pygame.font.SysFont('Arial', 28)
            err = font2.render(str(e), True, (120,0,0))
            self.screen.blit(err, (80, 220))

def draw_score_timer(screen, score, time_left):
    font = pygame.font.SysFont(None, 48)
    score_text = font.render(f'Score: {score}', True, (0,0,0))
    timer_text = font.render(f'Time: {int(time_left)}s', True, (0,0,0))
    screen.blit(score_text, (SCREEN_WIDTH//2 - 120, 20))
    screen.blit(timer_text, (SCREEN_WIDTH//2 + 80, 20))

def draw_feedback(screen, feedback, color):
    font = pygame.font.SysFont(None, 64)
    text = font.render(feedback, True, color)
    screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 200))

if __name__ == '__main__':
    game = HandSortingGame()
    game.run() 