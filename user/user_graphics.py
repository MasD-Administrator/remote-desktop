from kivymd.app import MDApp
from kivy.lang import Builder

from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import mainthread
from kivy.config import Config


from kivymd.uix.list.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRectangleFlatButton

from user_network import ControllerNetwork


class MainScreen(Screen):
    main = None

class SettingsScreen(Screen):
    main = None
    def save_username(self):
        self.main.save_username_setting()

    def save_restriction_mode(self):
        self.main.save_restriction_mode_setting()
    def save_all(self):
        self.main.save_all_settings()


class MasDController(MDApp):
    dialog = None

    def __init__(self, main):
        super().__init__()

        Config.set('kivy', 'exit_on_escape', '0')

        # Window.size = (800, 450)
        # Window.maximize()
        Window.minimum_width = 450
        Window.minimum_height = 600

        Builder.load_file("user_graphics.kv")

        self.screen_manager = ScreenManager()

        self.main = main

        self.settings_screen = SettingsScreen(name="settings")
        self.main_screen = MainScreen(name="main")

        self.settings_screen.main = main
        self.main_screen.main = main

        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.settings_screen)

        self.settings_screen.ids.restriction_mode_switch.active = self.main.restriction_mode

        for i in range(0, 10):
            item = TwoLineIconListItem()
            item.text = "NHLCOLPOS29"
            item.secondary_text = "Offline"
            item.add_widget(IconLeftWidget(icon="account"))
            self.main_screen.ids.user_list.add_widget(item)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        return self.screen_manager

    @mainthread
    def open_dialog(self, msg):
        if not self.dialog:
            self.dialog = MDDialog(
                buttons=[
                    MDRectangleFlatButton(
                        text="Okay",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda _: self.dialog.dismiss()
                    ),
                ],
            )
        self.dialog.text = msg
        self.dialog.open()

    def on_stop(self):
        self.main.stop()


if __name__ == "__main__":
    MasDController().run()
