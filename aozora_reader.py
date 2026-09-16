import pyxel

# ===== 設定 =====
FONT_PATH = "PixelMplus12-Regular.ttf"
FONT_SIZE = 12
SCREEN_W = 256
SCREEN_H = 256

BOX_X = 8
BOX_Y = 160
BOX_W = 240
BOX_H = 88
PADDING = 8
LINE_HEIGHT = FONT_SIZE + 6
MAX_TEXT_W = BOX_W - PADDING * 2

CHAR_INTERVAL = 2  # 通常時: 何フレームで1文字進めるか
FAST_INTERVAL = 1  # SPACE押しっぱなし時
FILE_PATH = "aozora_416.txt"


def load_paragraphs(path):
    """空行を段落区切りとして保持したまま読み込む"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return raw.split("\n")


def wrap_paragraphs(paragraphs, font, max_w):
    """text_width() で実測しながら折り返す"""
    wrapped = []
    for para in paragraphs:
        if para == "":
            wrapped.append("")
            continue
        line = ""
        for ch in para:
            test = line + ch
            if font.text_width(test) > max_w and line:
                wrapped.append(line)
                line = ch
            else:
                line = test
        wrapped.append(line)
    return wrapped


def paginate(lines, rows_per_page):
    return [lines[i:i + rows_per_page] for i in range(0, len(lines), rows_per_page)]


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Aozora Reader")
        self.font = pyxel.Font(FONT_PATH, FONT_SIZE)

        paragraphs = load_paragraphs(FILE_PATH)
        wrapped = wrap_paragraphs(paragraphs, self.font, MAX_TEXT_W)
        rows_per_page = max(1, BOX_H // LINE_HEIGHT)
        self.pages = paginate(wrapped, rows_per_page)

        self.page_index = 0
        self.revealed = 0
        self.timer = 0
        self.page_done = False

        pyxel.run(self.update, self.draw)

    @property
    def current_page_text(self):
        return "\n".join(self.pages[self.page_index])

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        if self.page_index >= len(self.pages):
            return

        text = self.current_page_text

        if not self.page_done:
            # 即表示（スキップ）
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.revealed = len(text)
                self.page_done = True
                return

            interval = FAST_INTERVAL if pyxel.btn(pyxel.KEY_SPACE) else CHAR_INTERVAL
            self.timer += 1
            if self.timer >= interval:
                self.timer = 0
                self.revealed += 1
                if self.revealed >= len(text):
                    self.revealed = len(text)
                    self.page_done = True
        else:
            if (
                pyxel.btnp(pyxel.KEY_RETURN)
                or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
                or pyxel.btnp(pyxel.KEY_SPACE)
            ):
                self.page_index += 1
                self.revealed = 0
                self.timer = 0
                self.page_done = False
            elif pyxel.btnp(pyxel.KEY_UP) and self.page_index > 0:
                self.page_index -= 1
                self.revealed = len(self.current_page_text)
                self.page_done = True

    def draw(self):
        pyxel.cls(0)

        # ノベルゲーム風ウィンドウ
        pyxel.rect(BOX_X + 1, BOX_Y + 1, BOX_W - 2, BOX_H - 2, 1)
        pyxel.rectb(BOX_X, BOX_Y, BOX_W, BOX_H, 7)

        if self.page_index >= len(self.pages):
            pyxel.text(BOX_X + PADDING, BOX_Y + PADDING, "-- 読了 --", 7, font=self.font)
            return

        text = self.current_page_text
        shown = text[: self.revealed]
        for i, line in enumerate(shown.split("\n")):
            y = BOX_Y + PADDING + i * LINE_HEIGHT
            pyxel.text(BOX_X + PADDING, y, line, 7, font=self.font)

        if self.page_done and pyxel.frame_count % 30 < 15:
            pyxel.text(BOX_X + BOX_W - 14, BOX_Y + BOX_H - 12, "▼", 7, font=self.font)


App()
