from pynput.mouse import \
    Listener as MouseListener, \
    Controller as MouseController, \
    Button as MouseButton

import logging
import time
import win32gui

logging.basicConfig(filename="clicker.log", level=logging.DEBUG, format='%(asctime)s: %(message)s')


class Scenario:

    def __init__(self, clicking_coords=None):
        self._clicking_cords = clicking_coords or list()
        self._mouse_controller = MouseController()
        self._cooldown_sec = 0.5

    def __str__(self):
        return str(self._clicking_cords)

    def _relax(self):
        time.sleep(self._cooldown_sec)

    def _click_cord(self, x, y):
        self._mouse_controller.position = (x, y)
        self._relax()
        self._mouse_controller.press(MouseButton.left)
        self._relax()
        self._mouse_controller.release(MouseButton.left)
        self._relax()

    def execute_scenario(self):
        for clicking_cord in self._clicking_cords:
            self._click_cord(*clicking_cord)

    def get_coords(self):
        return self._clicking_cords


class ActionRecorder:
    recorded_coords = tuple()

    @staticmethod
    def _on_click_callback(x, y, button, pressed):
        if pressed or button != MouseButton.left:
            return True
        ActionRecorder.recorded_coords = (x, y)
        return False

    @staticmethod
    def record_action():
        with MouseListener(on_click=ActionRecorder._on_click_callback) as listener:
            listener.join()

        assert len(ActionRecorder.recorded_coords) == 2
        return ActionRecorder.recorded_coords


class ScenarioBuilder:

    def __init__(self):
        self._clicking_cords = list()

    def register_click(self, message):
        print(message)
        record = ActionRecorder.record_action()
        self._clicking_cords.append(record)
        return self

    def get_scenario(self):
        return Scenario(self._clicking_cords)


class PixelsDaemon:

    def __init__(self, coord):
        self._coord = coord
        self._proper_color = None

    @staticmethod
    def _get_pixel_colour(i_x, i_y):
        desktop_window_id = win32gui.GetDesktopWindow()
        desktop_window_dc = win32gui.GetWindowDC(desktop_window_id)

        long_colour = win32gui.GetPixel(desktop_window_dc, i_x, i_y)
        integer_colour = int(long_colour)
        final_colour = (
            (integer_colour & 0xff),
            ((integer_colour >> 8) & 0xff),
            ((integer_colour >> 16) & 0xff)
        )

        win32gui.ReleaseDC(desktop_window_id, desktop_window_dc)
        return final_colour

    def _grab_color(self):
        return self._get_pixel_colour(self._coord[0], self._coord[1])

    def init_color(self):
        self._proper_color = self._grab_color()

    def get_proper_color(self):
        return self._proper_color

    def keep_an_eye(self, loop_sleep_time=5):
        current_color = self._grab_color()
        while current_color == self._proper_color:
            logging.debug("Color is good, sleeping... %s", current_color)
            time.sleep(loop_sleep_time)
            current_color = self._grab_color()

        logging.debug("Colors are different: {0}, {1}".format(current_color, self._proper_color))
        return current_color, self._proper_color


def greetings():
    print("Mishin Clicker 1.0 (c)")
    print("Welcome!")
    input("Press Enter to continue")


def hold_on(*messages):
    for message in messages:
        print(message)
    input("Press enter...")
    logging.debug("Got enter key")


def main():
    greetings()

    builder = ScenarioBuilder()
    builder\
        .register_click("Нажми на кнопку подключения в VPilot")\
        .register_click("Теперь нажми на кнопку connect в сплывающем окне")

    scenario = builder.get_scenario()
    print("Сценарий записали: {}".format(scenario))

    hold_on(
        "Теперь мы готовы запомнить цвет кнопки, чтобы в случае ее изменения, мы на нее кликнули",
        "Нажми на Enter, когда будешь готов записать цвет",
    )

    print("Теперь запомним цвет")
    p_daemon = PixelsDaemon(scenario.get_coords()[0])
    p_daemon.init_color()
    print("Запомнили цвет: {0}".format(p_daemon.get_proper_color()))

    hold_on(
        "Теперь не стоит волноваться!",
        "Нажми Enter, когда будешь готов запустить обозревателя!",
    )

    while True:
        print("Запускаем обозревателя")
        new_color, proper_color = p_daemon.keep_an_eye()
        print("О нет, цвет изменился!")
        print("Новый цвет: {0}, старый цвет: {1}".format(new_color, proper_color))
        print("Переподключаемся!")
        scenario.execute_scenario()

        time.sleep(10)
        print("Шаги были предприняты, смотрим опять на цвет")


if __name__ == '__main__':
    main()
