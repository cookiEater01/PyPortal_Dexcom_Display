from adafruit_display_text.label import Label

def black_background(displayio, width, height):
    BACKGROUND = 0x0
    bg_bitmap = displayio.Bitmap(width, height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = BACKGROUND
    return displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)


def text_box(target, top, max_chars: int, string: str, pyportal, font):
    text_hight = Label(font, text="M", color=0x03AD31)
    text = pyportal.wrap_nicely(string, max_chars)
    new_text = ""
    test = ""
    for w in text:
        new_text += '\n'+w
        test += 'M\n'
    text_hight.text = test
    glyph_box = text_hight.bounding_box
    print(glyph_box[3])
    target.text = "" # Odd things happen without this
    target.y = round(glyph_box[3]/2) + int(top)
    target.text = new_text

# This will handel switching Images and Icons
def set_image(group, filename, displayio):
    """Set the image file for a given goup for display.
    This is most useful for Icons or image slideshows.
        :param group: The chosen group
        :param filename: The filename of the chosen image
    """
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
    # CircuitPython 7+ compatible
    image = displayio.OnDiskBitmap(filename)
    image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)

    group.append(image_sprite)
