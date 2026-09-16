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
BOX_Y = 160
BOX_W = 240
BOX_H = 88
PADDING = 8
MAX_TEXT_W = BOX_W - PADDING * 2

CHAR_INTERVAL = 2   # 通常時: 何フレームで1文字進めるか
FAST_INTERVAL = 1   # SPACE長押し時
FILE_PATH = "aozora_416.txt"

# ゲームパッド定数の安全な取得（存在しない場合は None）
GAMEPAD_A = getattr(pyxel, "GAMEPAD1_BUTTON_A", None)
GAMEPAD_B = getattr(pyxel, "GAMEPAD1_BUTTON_B", None)
GAMEPAD_X = getattr(pyxel, "GAMEPAD1_BUTTON_X", None)
GAMEPAD_UP = getattr(pyxel, "GAMEPAD1_BUTTON_DPAD_UP", None)
GAMEPAD_DOWN = getattr(pyxel, "GAMEPAD1_BUTTON_DPAD_DOWN", None)
GAMEPAD_SELECT = getattr(pyxel, "GAMEPAD1_BUTTON_SELECT", None)
GAMEPAD_START = getattr(pyxel, "GAMEPAD1_BUTTON_START", None)


def _btn(key):
    return pyxel.btn(key) if key is not None else False


def _btnp(key):
    return pyxel.btnp(key) if key is not None else False


def load_paragraphs(path):
    if not os.path.exists(path):
        return ["（ファイルが見つかりません）"]
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return raw.split("\n")


def wrap_paragraphs(paragraphs, font, max_w):
    wrapped = []
    for para in paragraphs:
        if para == "":
            wrapped.append("")
            continue
        line = ""
        for ch in para:
            test = line + ch
            if font.text_width(test) > max_w:
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

        # フォントサイズごとに Font インスタンスを生成
        self.fonts = {}
        for size, path in FONT_CONFIG.items():
            if os.path.exists(path):
                self.fonts[size] = pyxel.Font(path, size)
            else:
                # ファイルがなければデフォルトフォントをフォールバック
                self.fonts[size] = pyxel.Font(size)

        self.paragraphs = load_paragraphs(FILE_PATH)

        self.current_size = FONT_SIZE_DEFAULT
        self.font = self.fonts[self.current_size]
        self.line_height = self.current_size + 6

        self._rebuild_pages()

        self.page_index = 0
        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 0

        pyxel.run(self.update, self.draw)

    def _rebuild_pages(self):
        """フォントサイズ変更時に折り返しとページ割りを再計算"""
        self.font = self.fonts.get(self.current_size, pyxel.Font(self.current_size))
        self.line_height = self.current_size + 6
        rows_per_page = max(1, (BOX_H - PADDING * 2) // self.line_height)

        wrapped = wrap_paragraphs(self.paragraphs, self.font, MAX_TEXT_W)
        self.pages = paginate(wrapped, rows_per_page)

    def reset(self):
        self.page_index = 0
        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 0

    def toggle_font_size(self):
        """10px と 12px を切り替え、ページを再構成して同じページの先頭から再開"""
        new_size = 10 if self.current_size == 12 else 12
        self.current_size = new_size
        self._rebuild_pages()

        # ページ位置を維持（範囲外なら最終ページに収める）
        if self.page_index >= len(self.pages):
            self.page_index = max(0, len(self.pages) - 1)

        # そのページの先頭から再表示
        self.revealed = 0
        self.timer = 0
        self.page_done = False
        self.skip_cooldown = 5

    @property
    def current_page_text(self):
        if 0 <= self.page_index < len(self.pages):
            return "\n".join(self.pages[self.page_index])
        return ""

    def _skip_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
            or _btnp(GAMEPAD_A)
        )

    def _back_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_UP)
            or _btnp(GAMEPAD_UP)
        )

    def _next_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_DOWN)
            or _btnp(GAMEPAD_DOWN)
        )

    def _fast_forward(self):
        return (
            pyxel.btn(pyxel.KEY_SPACE)
            or _btn(GAMEPAD_B)
        )

    def _reset_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_R)
            or _btnp(GAMEPAD_SELECT)
            or _btnp(GAMEPAD_START)
        )

    def _font_toggle_pressed(self):
        return (
            pyxel.btnp(pyxel.KEY_F)
            or _btnp(GAMEPAD_X)
        )

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        if self._reset_pressed():
            self.reset()
            return

        if self._font_toggle_pressed():
            self.toggle_font_size()
            return

        if self.skip_cooldown > 0:
            self.skip_cooldown -= 1
            return

        if self.page_index >= len(self.pages):
            if self._back_pressed() and self.pages:
                self.page_index = len(self.pages) - 1
                self.revealed = len(self.current_page_text)
                self.page_done = True
            return

        text = self.current_page_text

        if not self.page_done:
            if self._back_pressed() and self.page_index > 0:
                self.page_index -= 1
                self.revealed = len(self.current_page_text)
                self.page_done = True
                return

            if self._skip_pressed():
                self.revealed = len(text)
                self.page_done = True
                self.skip_cooldown = 8
                return

            interval = FAST_INTERVAL if self._fast_forward() else CHAR_INTERVAL
            self.timer += 1
            if self.timer >= interval:
                self.timer = 0
                while self.revealed < len(text) and text[self.revealed] == "\n":
                    self.revealed += 1
                if self.revealed < len(text):
                    self.revealed += 1
                if self.revealed >= len(text):
                    self.revealed = len(text)
                    self.page_done = True
        else:
            if self._next_pressed():
                self.page_index += 1
                self.revealed = 0
                self.timer = 0
                self.page_done = False
            elif self._back_pressed() and self.page_index > 0:
                self.page_index -= 1
                self.revealed = len(self.current_page_text)
                self.page_done = True

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
        """ページ番号とフォントサイズを右下に表示"""
        if not self.pages:
            return

        total = len(self.pages)
        current = min(self.page_index + 1, total)
        page_label = f"{current}/{total}"
        font_label = f"{self.current_size}px"

        # ページ番号（右下）
        x = BOX_X + BOX_W - PADDING - self.font.text_width(page_label)
        y = BOX_Y + BOX_H - 12
        pyxel.text(x, y, page_label, 5, font=self.font)

        # フォントサイズ表示（左下）
        pyxel.text(BOX_X + PADDING, y, font_label, 5, font=self.font)


App()