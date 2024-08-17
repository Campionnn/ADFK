import os
import time
import math
import keyboard
import vgamepad as vg
import logging
import random
from utils import memory


class Control:
    def __init__(self):
        self.logger = logging.getLogger()
        try:
            self.gamepad = vg.VX360Gamepad()
        except AssertionError:
            self.logger.error("No controller detected. Try relaunching the script")
            self.logger.error("If that doesn't work reinstall ViGEmBus from https://github.com/nefarius/ViGEmBus/releases")
            os._exit(0)

    def reset(self):
        self.gamepad.reset()
        self.gamepad.update()

    def reset_look(self):
        self.gamepad.right_joystick_float(x_value_float=0, y_value_float=0)
        self.gamepad.update()

    def reset_move(self):
        self.gamepad.left_joystick_float(x_value_float=0, y_value_float=0)
        self.gamepad.update()

    def look_down(self, value):
        self.gamepad.right_joystick_float(x_value_float=0, y_value_float=-value)
        self.gamepad.update()

    def look_up(self, value):
        self.gamepad.right_joystick_float(x_value_float=0, y_value_float=value)
        self.gamepad.update()

    def look_left(self, value):
        self.gamepad.right_joystick_float(x_value_float=-value, y_value_float=0)
        self.gamepad.update()

    def look_right(self, value):
        self.gamepad.right_joystick_float(x_value_float=value, y_value_float=0)
        self.gamepad.update()

    def move_forward(self, value):
        self.gamepad.left_joystick_float(x_value_float=0, y_value_float=value)
        self.gamepad.update()

    def move(self, value_x, value_y):
        self.gamepad.left_joystick_float(x_value_float=value_x, y_value_float=-value_y)
        self.gamepad.update()

    def jump(self):
        self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.gamepad.update()
        time.sleep(0.1)
        self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.gamepad.update()

    def zoom_in(self, duration=2):
        self.logger.debug("Zooming in")
        keyboard.press("i")
        time.sleep(duration)
        keyboard.release("i")

    def zoom_out(self, duration=2):
        self.logger.debug("Zooming out")
        keyboard.press("o")
        time.sleep(duration)
        keyboard.release("o")

    def calculate_degree_difference(self, current_degree, target_degree):
        diff = target_degree - current_degree
        if diff < -180:
            diff += 360
        if diff > 180:
            diff -= 360
        return diff

    def turn_towards_yaw(self, pid, y_addrs, degree, tolerance, min_amount=0.4, precise=False):
        while True:
            rot = memory.get_current_rot(pid, y_addrs)[1]
            diff = self.calculate_degree_difference(rot, degree)
            if abs(diff) <= tolerance:
                self.reset_look()
                return True
            else:
                self.reset_move()
            amount = max(min(abs(diff/90), 1), min_amount)
            if diff > 0:
                self.look_right(amount)
            else:
                self.look_left(amount)
            time.sleep(0.1)
            if precise:
                self.reset_look()

    def calculate_degree_pos(self, x1, z1, x2, z2):
        degrees = math.degrees(math.atan2(z2 - z1, x2 - x1))
        if degrees < 0:
            degrees += 360
        return degrees

    def calculate_distance(self, x1, z1, x2, z2):
        return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)

    def go_to_pos(self, pid, y_addrs, final_x, final_z, tolerance, turn_tolerance=5, jump=False, min_speed=0.4, max_speed=1.0, min_turn=0.4, precise=False, timeout=10):
        current_pos = memory.get_current_pos(pid, y_addrs)
        init_distance = self.calculate_distance(current_pos[0], current_pos[2], final_x, final_z)
        self.logger.debug(f"Going to {final_x}, {final_z} from {current_pos[0]}, {current_pos[2]}")
        self.logger.debug(f"Distance to target: {init_distance}")
        start = time.time()
        while time.time() - start < timeout:
            current_x = current_pos[0]
            current_z = current_pos[2]
            if abs(current_x - final_x) < tolerance and abs(current_z - final_z) < tolerance:
                self.reset_move()
                return True
            final_rot = self.calculate_degree_pos(current_x, current_z, final_x, final_z)
            self.turn_towards_yaw(pid, y_addrs, final_rot, turn_tolerance, min_turn, precise)
            distance = self.calculate_distance(current_x, current_z, final_x, final_z)
            amount = max(min((distance / 15), max_speed), min_speed)
            if jump:
                self.jump()
            self.move_forward(amount)
            time.sleep(0.1)
            if precise:
                self.reset_move()
            current_pos = memory.get_current_info(pid, y_addrs)
        self.logger.warning("Timed out while moving to position")
        self.reset_move()
        return False

    def unstuck(self, pid, y_addrs, jump=True):
        self.logger.debug("Unstucking player")
        init_pos = memory.get_current_pos(pid, y_addrs)
        for _ in range(5):
            if jump:
                for __ in range(5):
                    self.jump()
            self.move(random.uniform(-1, 1), random.uniform(-1, 1))
            time.sleep(0.5)
        self.reset_move()
        pos = memory.get_current_pos(pid, y_addrs)
        if self.calculate_distance(init_pos[0], init_pos[2], pos[0], pos[2]) > 5:
            return True
        return False
