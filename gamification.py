import json
import os
from datetime import datetime

GAMIFICATION_DATA_FILE = "gamification_data.json"

class GamificationManager:
    def __init__(self, data_file=GAMIFICATION_DATA_FILE):
        self.data_file = data_file
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {"xp": 0, "level": 1, "last_message": None, "badges": []}
        # Ensure badges key exists for legacy users
        if "badges" not in self.data[user_id]:
            self.data[user_id]["badges"] = []
        return self.data[user_id]

    def add_xp(self, user_id, amount):
        user = self.get_user(user_id)
        user["xp"] += amount
        user["last_message"] = datetime.utcnow().isoformat()
        # Level up logic
        next_level_xp = self.get_xp_for_level(user["level"] + 1)
        leveled_up = False
        new_badges = []
        while user["xp"] >= next_level_xp:
            user["level"] += 1
            leveled_up = True
            next_level_xp = self.get_xp_for_level(user["level"] + 1)
            # Check for badge unlocks
            badge = self.check_badge_unlock(user["level"], user)
            if badge:
                user["badges"].append(badge)
                new_badges.append(badge)
        self.save_data()
        return leveled_up, user["level"], user["xp"], new_badges

    def get_xp_for_level(self, level):
        # Faster early, slower later: linear for levels 1-5, quadratic for 6+
        if level <= 5:
            return 100 * level
        else:
            return 100 * (level ** 2)

    def get_leaderboard(self, top_n=10):
        leaderboard = [
            (uid, data["level"], data["xp"])
            for uid, data in self.data.items()
        ]
        leaderboard.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return leaderboard[:top_n]

    def get_user_level(self, user_id):
        user = self.get_user(user_id)
        return user["level"], user["xp"]

    def check_badge_unlock(self, level, user):
        # Define level milestones and badges
        badge_milestones = {
            2: "Congrats, You Did Something 🥱",
            5: "Tryhard in Training 🏋️‍♂️",
            10: "Still Here? Wow. 😏",
            20: "Professional Procrastinator 🕰️",
            30: "Overachiever Alert 🚨",
            50: "Touch Grass, Maybe? 🌱"
        }
        if level in badge_milestones and badge_milestones[level] not in user["badges"]:
            return badge_milestones[level]
        return None

    def get_user_badges(self, user_id):
        user = self.get_user(user_id)
        return user["badges"]

    def reset(self):
        self.data = {}
        self.save_data()
