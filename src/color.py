COLOR_RANGE_MAX = 255.0

def rgba(r, g, b, a=255):
    into_color_range = lambda x: min(max(x / COLOR_RANGE_MAX, 0.0), 1.0)
    return [into_color_range(x) for x in [r, g, b, a]]

def blend_color(color1, color2, ratio, rgb=False):
    ratio = min(ratio, 1)
    if rgb:
        return [int(COLOR_RANGE_MAX * (color1[i] * ratio + color2[i] * (1 - ratio))) for i in range(len(color1))]
    return [color1[i] * ratio + color2[i] * (1 - ratio) for i in range(len(color1))]
