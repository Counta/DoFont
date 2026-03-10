import os
from fontTools.ttLib import TTFont
from copy import deepcopy

weights = [
    'Thin','ExtraLight','Light','Regular','Medium','SemiBold','Bold','ExtraBold','Black'
]

for w in weights:
    a_path = f'GoogleSansFlex_120pt-{w}.ttf'
    b_path = f'NotoSansSC-{w}.ttf'
    out_path = f'NotoSansSC_GoogleSansFlex_120pt-{w}.ttf'
    if not (os.path.exists(a_path) and os.path.exists(b_path)):
        print('SKIP missing', w)
        continue

    A = TTFont(a_path)
    B = TTFont(b_path)

    cmapA = A.getBestCmap()
    cmapB = B.getBestCmap()

    upmA = A['head'].unitsPerEm
    upmB = B['head'].unitsPerEm
    scale = upmB / upmA

    glyfA = A['glyf']
    glyfB = B['glyf']

    glyphOrderB = B.getGlyphOrder()
    glyphSetB = set(glyphOrderB)

    def unique_name(base):
        if base not in glyphSetB:
            return base
        i = 1
        while True:
            name = f"{base}.{i}"
            if name not in glyphSetB:
                return name
            i += 1

    component_map = {}

    def scale_component(comp):
        if hasattr(comp, 'x'):
            comp.x = int(round(comp.x * scale))
        if hasattr(comp, 'y'):
            comp.y = int(round(comp.y * scale))
        for attr in ('xScale','yScale','scale','xyScale','yxScale'):
            if hasattr(comp, attr):
                setattr(comp, attr, getattr(comp, attr) * scale)

    def scale_glyph(g):
        g = deepcopy(g)
        if g.isComposite():
            for comp in g.components:
                scale_component(comp)
        else:
            coords, endPts, flags = g.getCoordinates(glyfA)
            coords.transform(((scale, 0), (0, scale)))
            g.coordinates = coords
            g.endPtsOfContours = endPts
            g.flags = flags
            g.recalcBounds(glyfB)
        return g

    def ensure_component(a_name):
        if a_name in component_map:
            return component_map[a_name]
        target = unique_name('A.' + a_name)
        component_map[a_name] = target
        glyphOrderB.append(target)
        glyphSetB.add(target)
        g = scale_glyph(glyfA[a_name])
        if g.isComposite():
            for comp in g.components:
                comp.glyphName = ensure_component(comp.glyphName)
            g.recalcBounds(glyfB)
        glyfB.glyphs[target] = g
        if 'hmtx' in B:
            aw, alsb = A['hmtx'].metrics[a_name]
            B['hmtx'].metrics[target] = (int(round(aw * scale)), int(round(alsb * scale)))
        return target

    def copy_glyph_to_target(a_name, target_name):
        g = scale_glyph(glyfA[a_name])
        if g.isComposite():
            for comp in g.components:
                comp.glyphName = ensure_component(comp.glyphName)
            g.recalcBounds(glyfB)
        glyfB.glyphs[target_name] = g
        if 'hmtx' in B:
            aw, alsb = A['hmtx'].metrics[a_name]
            B['hmtx'].metrics[target_name] = (int(round(aw * scale)), int(round(alsb * scale)))

    unicode_cmap_tables = [t for t in B['cmap'].tables if t.isUnicode()]

    replaced = 0
    added = 0

    for cp, a_glyph in cmapA.items():
        if cp in cmapB:
            b_glyph = cmapB[cp]
            copy_glyph_to_target(a_glyph, b_glyph)
            replaced += 1
        else:
            target = unique_name('A.' + a_glyph)
            glyphOrderB.append(target)
            glyphSetB.add(target)
            copy_glyph_to_target(a_glyph, target)
            for t in unicode_cmap_tables:
                if t.format == 4 and cp > 0xFFFF:
                    continue
                t.cmap[cp] = target
            added += 1

    B.setGlyphOrder(glyphOrderB)
    B.save(out_path, reorderTables=False)

    print(w, 'scale', scale, 'Replaced', replaced, 'Added', added, 'Output', out_path)
