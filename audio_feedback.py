import pyttsx3

class AudioFeedback:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)

    def say(self, text):
        if self.enabled:
            self.engine.say(text)
            self.engine.runAndWait()

    def announce_selection(self, food_name):
        self.say(f"Selected: {food_name}")

    def announce_feedback(self, correct):
        if correct:
            self.say("Correct! Good job.")
        else:
            self.say("Incorrect. Try again.") 