from adafruit_display_text.label import Label
import displayio


def black_background(displayio, width, height, colour=0x0):
    # Default is black background
    bg_bitmap = displayio.Bitmap(width, height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = colour
    return displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)


def text_box(target, top, max_chars: int, string: str, pyportal, font):
    text_hight = Label(font, text="M", color=0x03AD31)
    text = pyportal.wrap_nicely(string, max_chars)
    new_text = ""
    test = ""
    for w in text:
        new_text += "\n" + w
        test += "M\n"
    text_hight.text = test
    glyph_box = text_hight.bounding_box
    print(glyph_box[3])
    target.text = ""  # Odd things happen without this
    target.y = round(glyph_box[3] / 2) + int(top)
    target.text = new_text


def load_sprite_sheet(location: str, tile_width: int, tile_height: int):
    image = displayio.OnDiskBitmap(location)
    return displayio.TileGrid(
        image,
        pixel_shader=image.pixel_shader,
        width=1,
        height=1,
        tile_width=tile_width,
        tile_height=tile_height,
    )


# This will handel switching Images and Icons
def set_image_sprites(group, filename, displayio, width, height, default_sprite):
    print("Set image to ", filename)
    if group:
        group.pop()
    if not filename:
        return  # we're done, no icon desired
    try:
        if image_file:
            image_file.close
    except NameError:
        pass
    image = displayio.OnDiskBitmap(filename)
    image_sprite = displayio.TileGrid(
        image,
        pixel_shader=image.pixel_shader,
        width=1,
        height=1,
        tile_width=width,
        tile_height=height,
        default_tile=default_sprite,
    )

    group.append(image_sprite)

def prepare_label(font, text: str, colour, anchor_point, anchored_position, group):
    label = Label(font)
    label.text = text
    label.color = colour
    label.anchor_point = anchor_point
    label.anchored_position = anchored_position
    group.append(label)
    return label

def prepare_group(x=0, y=0, scale=1):
    group = displayio.Group()
    group.x = x
    group.y = y
    group.scale = scale
    return group

