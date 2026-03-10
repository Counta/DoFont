import os

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options


def detect_and_decode(path):
    with open(path, 'rb') as f:
        data = f.read()

    # BOM detection
    if data.startswith(b'\xEF\xBB\xBF'):
        return data[3:].decode('utf-8')
    if data.startswith(b'\xFF\xFE\x00\x00'):
        return data[4:].decode('utf-32le')
    if data.startswith(b'\x00\x00\xFE\xFF'):
        return data[4:].decode('utf-32be')
    if data.startswith(b'\xFF\xFE'):
        return data[2:].decode('utf-16le')
    if data.startswith(b'\xFE\xFF'):
        return data[2:].decode('utf-16be')

    # Heuristic: check for UTF-16/32 by null byte patterns
    if len(data) >= 4:
        even_nulls = sum(1 for i in range(0, len(data), 2) if data[i] == 0)
        odd_nulls = sum(1 for i in range(1, len(data), 2) if data[i] == 0)
        if even_nulls > odd_nulls * 2:
            try:
                return data.decode('utf-16be')
            except UnicodeDecodeError:
                pass
        if odd_nulls > even_nulls * 2:
            try:
                return data.decode('utf-16le')
            except UnicodeDecodeError:
                pass

        if len(data) % 4 == 0:
            cols = [0, 0, 0, 0]
            for i in range(0, len(data), 4):
                for c in range(4):
                    if data[i + c] == 0:
                        cols[c] += 1
            if cols[0] + cols[1] + cols[2] > cols[3] * 2:
                try:
                    return data.decode('utf-32be')
                except UnicodeDecodeError:
                    pass
            if cols[1] + cols[2] + cols[3] > cols[0] * 2:
                try:
                    return data.decode('utf-32le')
                except UnicodeDecodeError:
                    pass

    # Fallbacks
    for enc in ('utf-8', 'gb18030', 'latin1'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue

    return data.decode('utf-8', errors='ignore')


def build_unicode_set(text, mode):
    if mode == 'line':
        chars = [line.rstrip('\n\r') for line in text.splitlines()]
        return set(ord(ch[0]) for ch in chars if ch)
    # mode == 'all'
    return set(ord(ch) for ch in text if ch not in ('\n', '\r'))


def subset_font(font_in, charset_path, font_out, mode):
    text = detect_and_decode(charset_path)
    unicodes = build_unicode_set(text, mode)

    font = TTFont(font_in)

    opts = Options()
    opts.retain_gids = False
    opts.notdef_glyph = True
    opts.notdef_outline = True
    opts.recommended_glyphs = True
    opts.layout_features = '*'

    subsetter = Subsetter(options=opts)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)

    font.save(font_out, reorderTables=False)
    return len(unicodes)


def main():
    print('=== Subset Tool ===')
    base_dir = os.path.dirname(os.path.abspath(__file__))

    font_in = input('Input font path: ').strip().strip('"')
    if not os.path.isabs(font_in):
        font_in = os.path.join(base_dir, font_in)

    charset_path = input('Charset file path: ').strip().strip('"')
    if not os.path.isabs(charset_path):
        charset_path = os.path.join(base_dir, charset_path)

    if not os.path.isfile(font_in):
        print('Invalid font path.')
        return
    if not os.path.isfile(charset_path):
        print('Invalid charset path.')
        return

    mode = input('Charset mode (line/all, default all): ').strip().lower()
    if mode not in ('line', 'all'):
        mode = 'all'

    out_name = input('Output filename (e.g. subset.ttf): ').strip()
    if not out_name:
        print('Missing output filename.')
        return

    font_out = os.path.join(base_dir, out_name)

    count = subset_font(font_in, charset_path, font_out, mode)
    print('Done')
    print('Chars:', count)
    print('Output:', font_out)


if __name__ == '__main__':
    main()
