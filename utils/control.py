import time
import math
import keyboard
import vgamepad as vg
import logging
from utils import memory


class Control:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.gamepad = vg.VX360Gamepad()

    def reset(self):
        self.gamepad.reset()
        self.gamepad.update()
        keyboard.release("space")

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

    # def move_backward(self, value):
    #     self.gamepad.left_joystick_float(x_value_float=0, y_value_float=-value)
    #     self.gamepad.update()

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

    def turn_towards_yaw(self, pid, y_addrs, degree, tolerance):
        while True:
            rot = memory.get_current_rot(pid, y_addrs)[1]
            diff = self.calculate_degree_difference(rot, degree)
            if abs(diff) < tolerance:
                break
            amount = min(abs(diff/90)+0.2, 1)
            if diff > 0:
                self.look_right(amount)
            else:
                self.look_left(amount)
            time.sleep(0.1)
            self.reset_look()

    def calculate_degree_pos(self, x1, z1, x2, z2):
        degrees = math.degrees(math.atan2(z2 - z1, x2 - x1))
        if degrees < 0:
            degrees += 360
        return degrees

    def calculate_distance(self, x1, z1, x2, z2):
        return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)

    def go_to_pos(self, pid, y_addrs, final_x, final_z, tolerance, turn_tolerance=5, jump=False):
        current_pos = memory.get_current_pos(pid, y_addrs)
        init_distance = self.calculate_distance(current_pos[0], current_pos[2], final_x, final_z)
        self.logger.debug(f"Going to {final_x}, {final_z} from {current_pos[0]}, {current_pos[2]}")
        self.logger.debug(f"Distance to target: {init_distance}")
        final_rot = self.calculate_degree_pos(current_pos[0], current_pos[2], final_x, final_z)
        self.turn_towards_yaw(pid, y_addrs, final_rot, 5)
        while True:
            current_x = current_pos[0]
            current_z = current_pos[2]
            if abs(current_x - final_x) < tolerance and abs(current_z - final_z) < tolerance:
                break
            final_rot = self.calculate_degree_pos(current_x, current_z, final_x, final_z)
            self.turn_towards_yaw(pid, y_addrs, final_rot, turn_tolerance)
            distance = self.calculate_distance(current_x, current_z, final_x, final_z)
            amount = abs(distance/(init_distance/2))+0.4
            if jump:
                self.jump()
            self.move_forward(amount if amount < 1 else 1)
            time.sleep(0.1)
            self.reset_move()
            current_pos = memory.get_current_info(pid, y_addrs)
