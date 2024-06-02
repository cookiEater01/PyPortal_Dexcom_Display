from display_utils import create_glucose_group, create_and_show_group, create_loading_group
from adafruit_display_text.label import Label
from dexcom_glucose import DexcomGlucose


class DisplayMode:
    def __init__(self, display, width, height, font_main, font_decimal, font_other, use_us: bool):
        self.mode = ""
        self.height = height
        self.width = width
        self.display = display
        self.use_us = use_us
        self.loading_displayed = False
        self.glucose_displayed = False
        self.font_main = font_main
        self.font_decimal = font_decimal
        self.font_other = font_other
        self.screen_group = create_and_show_group(display, width, height)
        self.loading_group, self.loading_sprites, self.loading_status_label = create_loading_group(width, height, font_other)
        (self.glucose_group, self.glucose_sprites, self.glucose_main_label, self.glucose_decimal_label, self.glucose_unit_label,
         self.glucose_update_dt_label, self.warning_sprites, self.refreshing_sprites) = (
            create_glucose_group(font_main, font_decimal, font_other, use_us)
        )

    def change(self, new_mode: str):
        print("Trigger display change from " + self.mode + " to " + new_mode)
        self.mode = new_mode
        if self.mode == "GLUCOSE":
            if self.loading_displayed is True:
                self.screen_group.remove(self.loading_group)
                self.loading_displayed = False
            if self.glucose_displayed is False:
                self.screen_group.append(self.glucose_group)
                self.glucose_displayed = True
        elif self.mode == "LOADING":
            if self.glucose_displayed is True:
                self.screen_group.remove(self.glucose_group)
                self.glucose_displayed = False
            if self.loading_displayed is False:
                self.screen_group.append(self.loading_group)
                self.loading_displayed = True
        else:
            if self.glucose_displayed is True:
                self.screen_group.remove(self.glucose_group)
                self.glucose_displayed = False
            if self.loading_displayed is True:
                self.screen_group.remove(self.loading_group)
                self.loading_displayed = False

    def display_loading_time(self):
        self.loading_sprites.update_tile(1)
        self.loading_status_label.text = "Acquiring time ..."

    def display_loading_dexcom(self, py_portal):
        self.loading_sprites.update_tile(2)
        text_height = Label(self.font_other, text="M", color=0x616d7c)
        text = py_portal.wrap_nicely("Initializing Dexcom connection ...", 20)
        new_text = ""
        test = ""
        for w in text:
            new_text += "\n" + w
            test += "M\n"
        text_height.text = test
        glyph_box = text_height.bounding_box
        print(glyph_box[3])
        self.loading_status_label.text = ""  # Odd things happen without this
        self.loading_status_label.y = round(glyph_box[3] / 2) + int(self.height * 3 / 4)
        self.loading_status_label.text = new_text

    def update_glucose(self, glucose: DexcomGlucose):
        print("Updating displayed glucose")
        if glucose.mmol is None:
            self.glucose_sprites.update_tile(glucose.trend_numeric)
            self.glucose_main_label.color = 0x000000
            self.glucose_unit_label.color = 0x616d7c
            self.glucose_main_label.text = "--"
            self.glucose_decimal_label.text = ""
            self.glucose_main_label.anchored_position = (56, 95)
        else:
            if glucose.mmol <= 4.0:
                self.glucose_sprites.update_tile(glucose.trend_numeric + 8)
                self.glucose_main_label.color = 0xFFFFFF
                self.glucose_unit_label.color = 0xFFFFFF
            elif glucose.mmol >= 8.0:
                self.glucose_sprites.update_tile(glucose.trend_numeric + 16)
                self.glucose_main_label.color = 0x000000
                self.glucose_unit_label.color = 0x616d7c
            else:
                self.glucose_sprites.update_tile(glucose.trend_numeric)
                self.glucose_main_label.color = 0x000000
                self.glucose_unit_label.color = 0x616d7c
            if self.use_us is False:
                self.glucose_main_label.text = str(glucose.mmol)[0: -1]
                self.glucose_decimal_label.text = str(glucose.mmol)[-1]

                both_label_width = self.glucose_main_label.bounding_box[2] + self.glucose_decimal_label.bounding_box[2]
                start_margin = (320 - both_label_width) // 2

                print(both_label_width)
                print(start_margin)

                self.glucose_main_label.anchored_position = (start_margin, 95)
                self.glucose_main_label.anchor_point = (0.0, 0.0)
                self.glucose_decimal_label.anchored_position = (320 - start_margin, 107)
                self.glucose_decimal_label.anchor_point = (1.0, 0.0)

                self.glucose_unit_label.text = "mmol/L"
            else:
                self.glucose_main_label.text = str(glucose.mgdl)
                self.glucose_unit_label.text = "mg/dL"
        tmp_time = glucose.local_time
        self.glucose_update_dt_label.text = "{:02d}:{:02d}".format(
            tmp_time.time().hour, tmp_time.time().minute
        )

    def add_warning(self):
        print("Displaying warning icon.")
        self.warning_sprites.add_to_group()

    def remove_warning(self):
        print("Removing warning icon.")
        self.warning_sprites.remove_from_group()

    def add_refreshing(self):
        print("Displaying refreshing icon.")
        self.refreshing_sprites.add_to_group()

    def remove_refreshing(self):
        print("Removing refreshing icon.")
        self.refreshing_sprites.remove_from_group()
