import pyxel
import os

# ===== 設定 =====
FONT_CONFIG = {
    10: "PixelMplus10-Regular.ttf",
    12: "PixelMplus12-Regular.ttf",
}
FONT_SIZE_DEFAULT = 12

SCREEN_W = 256
SCREEN_H = 256

BOX_X = 8
BOX_Y = 8
BOX_W = 240
BOX_H = 240
PADDING = 8
FOOTER_H = 16
MAX_TEXT_W = BOX_W - PADDING * 2

CHAR_INTERVAL = 2
FAST_INTERVAL = 1
FILE_PATH = "aozora_416.txt"


def _get_gamepad_consts():
    candidates = {
        'A': ['GAMEPAD1_BUTTON_A', 'GAMEPAD1_A'],
        'B': ['GAMEPAD1_BUTTON_B', 'GAMEPAD1_B'],
        'X': ['GAMEPAD1_BUTTON_X', 'GAMEPAD1_X'],
        'UP': ['GAMEPAD1_BUTTON_DPAD_UP', 'GAMEPAD1_DPAD_UP', 'GAMEPAD1_BUTTON_UP'],
        'DOWN': ['GAMEPAD1_BUTTON_DPAD_DOWN', 'GAMEPAD1_DPAD_DOWN', 'GAMEPAD1_BUTTON_DOWN'],
        'SELECT': ['GAMEPAD1_BUTTON_SELECT', 'GAMEPAD1_SELECT'],
        'START': ['GAMEPAD1_BUTTON_START', 'GAMEPAD1_START'],
    }
    result = {}
    for name, keys in candidates.items():
        val = None
        for k in keys:
            if hasattr(pyxel, k):
                val = getattr(pyxel, k)
                break
        result[name] = val
    return result


_gp = _get_gamepad_consts()
GAMEPAD_A = _gp['A']
GAMEPAD_B = _gp['B']
GAMEPAD_X = _gp['X']
GAMEPAD_UP = _gp['UP']
GAMEPAD_DOWN = _gp['DOWN']
GAMEPAD_SELECT = _gp['SELECT']
GAMEPAD_START = _gp['START']


def _btn(key):
    return pyxel.btn(key) if key is not None else False


def _btnp(key):
    return pyxel.btnp(key) if key is not None else False


def load_paragraphs(path):
    if not os.path.exists(path):
        return ["（ファイルが見つかりません）"]
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return raw.splitlines()


def wrap_paragraphs(paragraphs, font, max_w):
    char_width = pyxel.FONT_WIDTH if font is None else None
    wrapped = []
    for para in paragraphs:
        if para == "":
            wrapped.append("")
            continue
        line = ""
        for ch in para:
            test = line + ch
            test_w = len(test) * char_width if char_width else font.text_width(test)
            if test_w > max_w:
                if line:
                    wrapped.append(line)
                    line = ch
                else:
                    wrapped.append(ch)
                    line = ""
            else:
                line = test
        if line:
            wrapped.append(line)
    return wrapped


def paginate(lines, rows_per_page):
    return [lines[i:i + rows_per_page] for i in range(0, len(lines), rows_per_page)]


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Aozora Reader")

        self.fonts = {}
        for size, path in FONT_CONFIG.items():
            if not isinstance(size, int):
                raise TypeError(f"FONT_CONFIG のキーは int にしてください: {size!r}")
            if not isinstance(path, str):
                raise TypeError(f"FONT_CONFIG の値は str にしてください: {path!r}")
            if os.path.exists(path):
                self.fonts[size] = pyxel.Font(path, size)
            else:
                self.fonts[size] = None

        self.paragraphs = load_paragraphs(FILE_PATH)

        self.current_size = int(FONT_SIZE_DEFAULT)
        self.font = self._get_font(self.current_size)
        self.line_height = self.current_size + 6

        self._rebuild_pages()

        self.page_index = 0
        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 0

        self.snd_talk = pyxel.Sound()
        self.snd_talk.set("c3", "t", "2", "n", 1)
        self.snd_talk_space = pyxel.Sound()
        self.snd_talk_space.set("c3", "t", "3", "n", 1)
        self.snd_talk_fast = pyxel.Sound()
        self.snd_talk_fast.set("c3", "t", "3", "f", 1)
        self.snd_talk_faster = pyxel.Sound()
        self.snd_talk_faster.set("c3", "t", "5", "f", 1)

        pyxel.run(self.update, self.draw)

    def _get_font(self, size):
        return self.fonts.get(int(size))

    def _rebuild_pages(self):
        self.font = self._get_font(self.current_size)
        self.line_height = int(self.current_size) + 6
        rows_per_page = max(1, (BOX_H - PADDING * 2 - FOOTER_H) // self.line_height)

        wrapped = wrap_paragraphs(self.paragraphs, self.font, MAX_TEXT_W)
        self.pages = paginate(wrapped, rows_per_page)

    def reset(self):
        self.page_index = 0
        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 0

    def toggle_font_size(self):
        sizes = sorted(FONT_CONFIG.keys())
        idx = sizes.index(int(self.current_size))
        new_size = sizes[(idx + 1) % len(sizes)]

        self.current_size = int(new_size)
        self._rebuild_pages()

        if self.page_index >= len(self.pages):
            self.page_index = max(0, len(self.pages) - 1)

        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 5

    @property
    def current_page_text(self):
        if 0 <= self.page_index < len(self.pages):
            return "\n".join(self.pages[self.page_index])
        return ""

    def _down_alone_pressed(self):
        down = pyxel.btnp(pyxel.KEY_DOWN) or _btnp(GAMEPAD_DOWN)
        a_held = pyxel.btn(pyxel.KEY_Z) or _btn(GAMEPAD_A)
        b_held = pyxel.btn(pyxel.KEY_X) or _btn(GAMEPAD_B)
        return down and not (a_held or b_held)

    def _skip_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
            or self._down_alone_pressed()
        )

    def _back_pressed(self):
        return pyxel.btnp(pyxel.KEY_UP) or _btnp(GAMEPAD_UP)

    def _next_pressed(self):
        return (
            self._down_alone_pressed()
            or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        )

    def _super_speed_combo(self):
        down = pyxel.btn(pyxel.KEY_DOWN) or _btn(GAMEPAD_DOWN)
        b_btn = pyxel.btn(pyxel.KEY_X) or _btn(GAMEPAD_B)
        return down and b_btn

    def _speed_combo(self):
        down = pyxel.btn(pyxel.KEY_DOWN) or _btn(GAMEPAD_DOWN)
        a_btn = pyxel.btn(pyxel.KEY_Z) or _btn(GAMEPAD_A)
        return down and a_btn

    def _space_held(self):
        return pyxel.btn(pyxel.KEY_SPACE)

    def _reset_pressed(self):
        return pyxel.btnp(pyxel.KEY_R) or _btnp(GAMEPAD_SELECT) or _btnp(GAMEPAD_START)

    def _font_toggle_pressed(self):
        return pyxel.btnp(pyxel.KEY_F) or _btnp(GAMEPAD_X)

    def _get_typing_speed(self):
        if self._super_speed_combo():
            return 0, 3
        if self._speed_combo():
            return 0, 1
        if self._space_held():
            return FAST_INTERVAL, 1
        return CHAR_INTERVAL, 1

    def _play_talk_sound(self, interval, chars_per_tick):
        if interval == 0 and chars_per_tick >= 3:
            pyxel.play(0, self.snd_talk_faster)
        elif interval == 0 and chars_per_tick == 1:
            pyxel.play(0, self.snd_talk_fast)
        elif interval == FAST_INTERVAL:
            pyxel.play(0, self.snd_talk_space)
        else:
            pyxel.play(0, self.snd_talk)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        if self._reset_pressed():
            self.reset()
            return

        if self._font_toggle_pressed():
            self.toggle_font_size()
            return

        if self._back_pressed():
            if self.page_index >= len(self.pages):
                if self.pages:
                    self.page_index = len(self.pages) - 1
                    self.revealed = len(self.current_page_text)
                    self.page_done = True
                    self.skip_cooldown = 5
                return
            if self.page_index > 0:
                self.page_index -= 1
                self.revealed = len(self.current_page_text)
                self.page_done = True
                self.skip_cooldown = 5
            return

        if self.skip_cooldown > 0:
            self.skip_cooldown -= 1
            return

        if self.page_index >= len(self.pages):
            return

        text = self.current_page_text

        if not self.page_done:
            if self._skip_pressed():
                self.revealed = len(text)
                self.page_done = True
                self.skip_cooldown = 8
                return

            interval, chars_per_tick = self._get_typing_speed()

            self.timer += 1
            if self.timer >= interval:
                self.timer = 0
                advanced = False

                for _ in range(chars_per_tick):
                    while self.revealed < len(text) and text[self.revealed] == "\n":
                        self.revealed += 1
                    if self.revealed < len(text):
                        self.revealed += 1
                        advanced = True

                if advanced:
                    self._play_talk_sound(interval, chars_per_tick)

                if self.revealed >= len(text):
                    self.revealed = len(text)
                    self.page_done = True
                    self.skip_cooldown = 5

        else:
            if self._next_pressed():
                self.page_index += 1
                self.revealed = 0
                self.timer = 0
                self.page_done = False

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(BOX_X + 1, BOX_Y + 1, BOX_W - 2, BOX_H - 2, 1)
        pyxel.rectb(BOX_X, BOX_Y, BOX_W, BOX_H, 7)

        if self.page_index >= len(self.pages):
            pyxel.text(BOX_X + PADDING, BOX_Y + PADDING, "-- 読了 --", 7, font=self.font)
            self._draw_ui()
            return

        text = self.current_page_text
        shown = text[:self.revealed]
        for i, line in enumerate(shown.split("\n")):
            y = BOX_Y + PADDING + i * self.line_height
            pyxel.text(BOX_X + PADDING, y, line, 7, font=self.font)

        if self.page_done and pyxel.frame_count % 30 < 15:
            pyxel.text(BOX_X + BOX_W - 14, BOX_Y + BOX_H - 12, "▼", 7, font=self.font)

        self._draw_ui()

    def _draw_ui(self):
        if not self.pages:
            return

        total = len(self.pages)
        current = min(self.page_index + 1, total)
        page_label = f"{current}/{total}"
        font_label = f"{int(self.current_size)}px"

        footer_y = BOX_Y + BOX_H - PADDING - self.current_size

        if self.font:
            label_w = self.font.text_width(page_label)
        else:
            label_w = len(page_label) * pyxel.FONT_WIDTH
        x = BOX_X + BOX_W - PADDING - label_w
        pyxel.text(x, footer_y, page_label, 5, font=self.font)
        pyxel.text(BOX_X + PADDING, footer_y, font_label, 5, font=self.font)


App()
