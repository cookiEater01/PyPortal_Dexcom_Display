import displayio
from adafruit_bitmap_font import bitmap_font
from sprites import Sprites
import terminalio
from adafruit_display_text.label import Label

soundBeep = "/sounds/beep.wav"


def play_tap_sound(pyportal):
    pyportal.play_file(soundBeep)
    print("Touch detected.")

def load_symbols_main():
    # Set the font and preload letters
    font = bitmap_font.load_font("/fonts/Roboto-Bold-60.bdf", displayio.Bitmap)
    font.load_glyphs(b"1234567890.-M")
    return font

def load_symbols_decimal():
    # Set the font and preload letters
    font = bitmap_font.load_font("/fonts/Roboto-Medium-40.bdf", displayio.Bitmap)
    font.load_glyphs(b"1234567890M")
    return font

def load_symbols():
    # Set the font and preload letters
    font = bitmap_font.load_font("/fonts/Roboto-Regular-12.bdf", displayio.Bitmap)
    font.load_glyphs(b"lmoLM1234567890- ()/.")
    return font


def create_and_show_group(display, width, height):
    group = displayio.Group()
    group.append(add_black_background(width, height))
    display.root_group = group
    return group


def add_black_background(width, height, colour=0xf1ecea):
    # Default is black background
    bg_bitmap = displayio.Bitmap(width, height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = colour
    return displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)


def prepare_group(x=0, y=0, scale=1):
    group = displayio.Group()
    group.x = x
    group.y = y
    group.scale = scale
    return group


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


def prepare_label(font, text: str, colour, anchor_point, anchored_position):
    label = Label(font)
    label.text = text
    label.color = colour
    label.anchor_point = anchor_point
    label.anchored_position = anchored_position
    return label


def create_glucose_group(font_main, font_decimal, font_other, use_us: bool):
    glucose_group = displayio.Group()

    # Groups
    glucose_image_group = prepare_group(37, 10)
    glucose_value_group = displayio.Group()
    glucose_unit_group = displayio.Group()
    sleep_icon_group = prepare_group(270, 0)
    glucose_update_dt_group = displayio.Group()
    warning_icon_group = prepare_group(0, 0)


    # Glucose image sprites
    glucose_tg = load_sprite_sheet("/images/glucose_sprites.bmp", 246, 220)
    glucose_sprites = Sprites(glucose_tg, 24, glucose_image_group)
    glucose_sprites.add_to_group()

    # Glucose - main - value
    glucose_main_label = prepare_label(font_main, "", 0x000000, (0.0, 0.0), (56, 25))
    glucose_value_group.append(glucose_main_label)

    # Glucose - decimal - value
    glucose_decimal_label = prepare_label(font_decimal, "", 0x000000, (1.0, 0.0), (56, 37))
    glucose_value_group.append(glucose_decimal_label)

    # Glucose unit
    glucose_unit_label = prepare_label(font_other, "mmol/L" if use_us is False else "mg/dl",
                                       0x616d7c, (0.5, 0.5), (160, 165))
    glucose_unit_group.append(glucose_unit_label)

    # Glucose time
    glucose_update_dt_label = prepare_label(terminalio.FONT, "", 0x000000, (0.5, 0.5), (160, 230))
    glucose_update_dt_group.append(glucose_update_dt_label)

    # Sleep button
    sleep_icon_tg = load_sprite_sheet("/images/sleep.bmp", 50, 50)
    sleep_sprites = Sprites(sleep_icon_tg, 1, sleep_icon_group)
    sleep_sprites.add_to_group()


    # Warning out of date
    warning_icon_tg = load_sprite_sheet("/images/warning.bmp", 50, 50)
    warning_sprites = Sprites(warning_icon_tg, 1, warning_icon_group)

    # Add subgroups to main group
    glucose_group.append(glucose_image_group)
    glucose_group.append(glucose_value_group)
    glucose_group.append(glucose_unit_group)
    glucose_group.append(glucose_update_dt_group)
    glucose_group.append(sleep_icon_group)
    glucose_group.append(warning_icon_group)

    return (glucose_group, glucose_sprites, glucose_main_label, glucose_decimal_label, glucose_unit_label,
            glucose_update_dt_label, warning_sprites)


def create_loading_group(width, height):
    loading_group = displayio.Group()
    # Group for loading image(s)
    loading_image_group = prepare_group(110, 40)

    # Loading images sprites
    loading_tg = load_sprite_sheet("/images/loading_sprites.bmp", 100, 100)
    loading_sprites = Sprites(loading_tg, 2, loading_image_group)
    loading_sprites.add_to_group()

    # Add loading image group to loading view
    loading_group.append(loading_image_group)

    # Group and loading label
    loading_label_group = displayio.Group()
    loading_status_label = prepare_label(terminalio.FONT, "Connecting to WIFI ...", 0x616d7c, (0.5, 0.5),
                                         (width / 2, height * 3 / 4))
    loading_label_group.append(loading_status_label)

    # Append loading_label_group to loading view
    loading_group.append(loading_label_group)

    return loading_group, loading_sprites, loading_status_label


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
