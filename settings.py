import json
import os

SETTINGS_FILE = 'settings.json'

class Settings:
    def __init__(self):
        self.camera_on = True
        self.sound_on = True
        self.game_duration = 60  # seconds
        self.food_items_file = 'food_items.json'
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                self.camera_on = data.get('camera_on', True)
                self.sound_on = data.get('sound_on', True)
                self.game_duration = data.get('game_duration', 60)
                self.food_items_file = data.get('food_items_file', 'food_items.json')

    def save(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({
                'camera_on': self.camera_on,
                'sound_on': self.sound_on,
                'game_duration': self.game_duration,
                'food_items_file': self.food_items_file
            }, f, indent=4)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.save() 