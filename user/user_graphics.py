from kivymd.app import MDApp
from kivy.lang import Builder

from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.list.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRectangleFlatButton

from user_network import ControllerNetwork


class MainScreen(Screen):
    main = None

class SettingsScreen(Screen):
    main = None
    def save_username(self):
        ...

    def save_restriction_mode(self):
        self.main.save_restriction_mode()
    def save_all(self):
        ...


class MasDController(MDApp):
    dialog = None

    def __init__(self, main):
        super().__init__()
        Window.size = (800, 450)
        Window.maximize()
        Window.minimum_width = 450
        Window.minimum_height = 600

        Builder.load_file("user_graphics.kv")

        self.screen_manager = ScreenManager()

        self.main = main

        self.settings_screen = SettingsScreen(name="settings")
        self.main_screen = MainScreen(name="main")

        self.settings_screen.main = main
        self.main_screen.main = main

        self.screen_manager.add_widget(self.settings_screen)
        self.screen_manager.add_widget(self.main_screen)

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

    def open_dialog(self, msg):
        if not self.dialog:
            self.dialog = MDDialog(
                text=msg,
                buttons=[
                    MDRectangleFlatButton(
                        text="Okay",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda _: self.dialog.dismiss()
                    ),
                ],
            )
        self.dialog.open()

    def dialog_close(self, *args):
        self.dialog.dismiss(force=True)

    def on_stop(self):
        self.main.stop()


if __name__ == "__main__":
    MasDController().run()
