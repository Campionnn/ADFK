from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time
import concurrent.futures

from utils.exceptions import *
from utils.roblox_types.roblox_portal import RobloxPortal
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerPortal(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxPortal
        super().__init__(**kwargs)

    def all_enter(self):
        assert type(self.main_instance) is RobloxPortal
        self.logger.info(f"Entering portal for all accounts")
        self.logger.info("Going to portal open position")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        host = ""
        if self.level > 10:
            self.logger.info(f"Looking for best {self.main_instance.portal_names.get(self.world)} to open")
            self.all_open_inventory(self.main_instance.portal_names.get(self.world))
            host = self.open_best_portal()
            if host == "":
                self.ensure_all_instance()
                self.all_leave()
                return
        else:
            self.logger.info(f"Looking for {self.main_instance.rarity_names.get(self.level)} {self.main_instance.portal_names.get(self.world)} to open")
            self.all_open_inventory(self.main_instance.portal_names.get(self.world))
            found = False
            attempts = 0
            while not found:
                if attempts > 3:
                    self.ensure_all_instance()
                    self.all_leave()
                    return
                for username in config.usernames:
                    if self.roblox_instances[username].open_portal():
                        host = username
                        found = True
                        break
                attempts += 1
        self.logger.info("Entering portal")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            if instance.username != host:
                try:
                    instance.enter()
                except (StartupException, MemoryException):
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_leave()
                    return
        time.sleep(0.1)
        self.logger.info(f"Starting portal")
        try:
            if not self.roblox_instances[host].start():
                self.logger.warning("Failed to start portal. Retrying")
                self.all_leave()
                self.ensure_all_instance()
                return
        except StartupException:
            self.roblox_instances[host].close_instance()
            self.ensure_all_instance()
            return
        time.sleep(2)
        self.logger.info("Going to play position")
        try:
            self.main_instance.play(host)
        except (PlayException, StartupException):
            self.all_back_to_lobby()
            return
        self.logger.info("Performing custom sequence")
        try:
            if not self.main_instance.do_custom_sequence():
                self.all_back_to_lobby()
                return
        except (PlayException, StartupException, MemoryException):
            self.all_back_to_lobby()
            self.ensure_all_instance()
            return

    def all_open_inventory(self, search=None):
        self.all_close_menu()
        self.logger.info(f"Opening inventory for all accounts")
        failed = self.all_click_text("items")
        if len(failed) > 0:
            return self.all_open_inventory(search)
        time.sleep(0.1)
        self.logger.info(f"Searching for {search} in inventory")
        failed = self.all_click_text("search", search=search)
        if len(failed) > 0:
            return self.all_open_inventory(search)

    def open_best_portal(self):
        def find_best_portal(username_):
            return username_, self.roblox_instances[username_].get_best_portal()

        best_portal = 0
        best_instance = None
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_username = {executor.submit(find_best_portal, username): username for username in config.usernames}
            for future in concurrent.futures.as_completed(future_to_username):
                username, portal = future.result()
                if portal == 0:
                    self.logger.info(f"No portal found for {username}")
                else:
                    self.logger.info(f"Best portal for {username} is {self.main_instance.rarity_names.get(portal)}")
                if portal > best_portal:
                    best_portal = portal
                    best_instance = self.roblox_instances[username]
        if best_instance is not None:
            self.logger.info(f"Opening {self.main_instance.rarity_names.get(best_portal)} portal for {best_instance.username}")
            attempts = 0
            while True:
                if attempts > 3:
                    return ""
                if best_instance.open_portal(best_portal):
                    return best_instance.username
                attempts += 1
        return ""
