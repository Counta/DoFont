import os
import re
from fontTools.ttLib import TTFont

# Apply mapping rules from a tab-separated text file.
# Lines starting with # are ignored.
# Rule A<TAB>B => map A to B
# Rule A<TAB>B<TAB>C => map A and B to C
# Only single-codepoint mappings are applied.

def parse_map(path):
    rules = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            if not line:
                continue
            if line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                a, b = parts
                rules.append((a, None, b))
            elif len(parts) == 3:
                a, b, c = parts
                rules.append((a, b, c))
    return rules


def apply_mapping(font_path, map_path, out_path):
    rules = parse_map(map_path)
    font = TTFont(font_path)

    unicode_tables = [t for t in font['cmap'].tables if t.isUnicode()]
    best = font.getBestCmap()

    updated = 0
    missing_dst = 0

    for a, b, c in rules:
        if len(a) != 1:
            continue
        if b is not None and len(b) != 1:
            continue
        if len(c) != 1:
            continue

        dst_cp = ord(c)
        if dst_cp not in best:
            missing_dst += 1
            continue
        dst_glyph = best[dst_cp]

        src_cps = [ord(a)]
        if b is not None:
            src_cps.append(ord(b))

        for cp in src_cps:
            for t in unicode_tables:
                if t.format == 4 and cp > 0xFFFF:
                    continue
                t.cmap[cp] = dst_glyph
            updated += 1

    font.save(out_path, reorderTables=False)
    return updated, missing_dst


def expand_patterns(raw, base_dir):
    files = []
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    for p in parts:
        # Support regex-like .* in filename
        if '.*' in p:
            dir_part = os.path.dirname(p) if os.path.dirname(p) else base_dir
            name_part = os.path.basename(p)
            try:
                rx = re.compile('^' + name_part.replace('.', '\\.').replace('\\.\\*', '.*') + '$')
            except re.error:
                continue
            try:
                for fn in os.listdir(dir_part):
                    if rx.match(fn):
                        files.append(os.path.join(dir_part, fn))
            except FileNotFoundError:
                continue
        else:
            if not os.path.isabs(p):
                p = os.path.join(base_dir, p)
            files.append(p)

    # De-dup while keeping order
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def main():
    print('=== Mapping Applier ===')
    base_dir = os.path.dirname(os.path.abspath(__file__))

    map_path = input('Mapping file path: ').strip().strip('"')
    if not os.path.isabs(map_path):
        map_path = os.path.join(base_dir, map_path)

    if not os.path.isfile(map_path):
        print('Invalid mapping file.')
        return

    raw_fonts = input('Font files (comma separated, supports .* in names): ').strip()
    if not raw_fonts:
        print('No input fonts.')
        return

    in_files = expand_patterns(raw_fonts, base_dir)
    in_files = [f for f in in_files if os.path.isfile(f)]

    if not in_files:
        print('No valid font files found.')
        return

    suffix = input('Output suffix (default _mapped): ').strip()
    if not suffix:
        suffix = '_mapped'

    for font_path in in_files:
        root, ext = os.path.splitext(font_path)
        out_path = root + suffix + ext
        updated, missing_dst = apply_mapping(font_path, map_path, out_path)
        print(os.path.basename(font_path), 'mapped', updated, 'missing_dst', missing_dst, 'out', os.path.basename(out_path))


if __name__ == '__main__':
    main()
