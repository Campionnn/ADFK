import time
import mouse
import keyboard
import vgamepad as vg


class Control:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()

    def wake_up(self):
        self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        self.gamepad.update()
        time.sleep(0.1)
        self.reset()

    def sleep(self):
        del self.gamepad

    def reset(self):
        self.gamepad.reset()
        self.gamepad.update()

    def look_down(self):
        self.gamepad.right_joystick_float(x_value_float=0, y_value_float=-1.0)
        self.gamepad.update()

    def look_left(self):
        self.gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0)
        self.gamepad.update()