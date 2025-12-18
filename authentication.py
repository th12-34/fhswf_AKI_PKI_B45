import os
import json
from databaseHandler import DatabaseAdministration

AUTH_FILE = "auth.json"

class Authentication:
    def __init__(self):
        self.user_admin = DatabaseAdministration()

    def login(self, username, password):

        if self.user_admin.verify_login(username, password):
            user = self.user_admin.get_user_by_name(username)
            # Save user data to a file
            with open(AUTH_FILE, "w") as f:
                json.dump(user, f)
            return user

        return None

    def get_logged_in_user(self):
        # Check if the auth file exists and return the user data
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r") as f:
                return json.load(f)
        return None

    def logout(self):
        # Remove the auth file to log out the user
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE)