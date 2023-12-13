COLOR_RANGE_MAX = 255.0


def blend_color(color1, color2, ratio) -> tuple[int, ...]:
    ratio = min(ratio, 1)
    return tuple(int(color1[i] * ratio + color2[i] * (1 - ratio)) for i in range(len(color1)))
