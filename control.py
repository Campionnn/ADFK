import time
import math
import vgamepad as vg
import memory


class Control:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()

    def wake_up(self):
        self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        self.gamepad.update()
        time.sleep(0.1)
        self.reset()

    def reset(self):
        self.gamepad.reset()
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

    def calculate_degree_difference(self, current_degree, target_degree):
        diff = target_degree - current_degree
        if diff < -180:
            diff += 360
        if diff > 180:
            diff -= 360
        return diff

    def turn_towards(self, pid, y_addrs, degree, tolerance):
        while True:
            rot = memory.get_current_rot(pid, y_addrs)[1]
            diff = self.calculate_degree_difference(rot, degree)
            if abs(diff) < tolerance:
                break
            amount = abs(diff/180)+0.2
            if diff > 0:
                self.look_right(amount if amount < 1 else 1)
                time.sleep(0.25)
                self.reset()
            else:
                self.look_left(amount if amount < 1 else 1)
                time.sleep(0.25)
                self.reset()

    def calculate_degree_pos(self, x1, z1, x2, z2):
        degrees = math.degrees(math.atan2(z2 - z1, x2 - x1))
        if degrees < 0:
            degrees += 360
        return degrees

    def calculate_distance(self, x1, z1, x2, z2):
        return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)

    def go_to_pos(self, pid, y_addrs, final_x, final_z, tolerance):
        current_pos = memory.get_current_pos(pid, y_addrs)
        init_distance = self.calculate_distance(current_pos[0], current_pos[2], final_x, final_z)
        while True:
            current_x = current_pos[0]
            current_z = current_pos[2]
            if abs(current_x - final_x) < tolerance and abs(current_z - final_z) < tolerance:
                break
            final_rot = self.calculate_degree_pos(current_x, current_z, final_x, final_z)
            self.turn_towards(pid, y_addrs, final_rot, 5)
            distance = self.calculate_distance(current_x, current_z, final_x, final_z)
            amount = abs(distance/init_distance)+0.4
            self.move_forward(amount if amount < 1 else 1)
            time.sleep(0.25)
            self.reset()
            current_pos = memory.get_current_info(pid, y_addrs)
