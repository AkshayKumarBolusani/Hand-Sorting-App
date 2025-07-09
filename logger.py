import csv
import os
from datetime import datetime

LOG_FILE = 'game_log.csv'

class GameLogger:
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'food_item', 'classification', 'dropped_in', 'result', 'score'])

    def log(self, food_item, classification, dropped_in, result, score):
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                food_item,
                classification,
                dropped_in,
                result,
                score
            ]) 