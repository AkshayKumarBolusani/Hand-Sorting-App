import json
import os

class FoodManager:
    def __init__(self, food_items_file='food_items.json'):
        self.food_items_file = food_items_file
        self.food_items = []
        self.load()

    def load(self):
        if os.path.exists(self.food_items_file):
            with open(self.food_items_file, 'r') as f:
                self.food_items = json.load(f)
        else:
            self.food_items = []

    def save(self):
        with open(self.food_items_file, 'w') as f:
            json.dump(self.food_items, f, indent=4)

    def add_food_item(self, name, image, type_):
        self.food_items.append({"name": name, "image": image, "type": type_})
        self.save()

    def update_food_item(self, index, name=None, image=None, type_=None):
        if 0 <= index < len(self.food_items):
            if name:
                self.food_items[index]["name"] = name
            if image:
                self.food_items[index]["image"] = image
            if type_:
                self.food_items[index]["type"] = type_
            self.save()

    def remove_food_item(self, index):
        if 0 <= index < len(self.food_items):
            self.food_items.pop(index)
            self.save() 