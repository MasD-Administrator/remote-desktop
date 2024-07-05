from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.screenmanager import FadeTransition
from kivymd.uix.list.list import TwoLineIconListItem, IconLeftWidget


Window.size = (800, 450)
Window.maximize()
Window.minimum_width = 450
Window.minimum_height = 600

Builder.load_file("user_graphics.kv")


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    ...


class MasDController(MDApp):
    def foo(self):
        ...

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"


        sm = ScreenManager()

        settings_screen = SettingsScreen(name="settings")
        main_screen = MainScreen(name="main")

        sm.add_widget(settings_screen)
        sm.add_widget(main_screen)

        for i in range(0, 10):
            item = TwoLineIconListItem()
            item.text = "NHLCOLPOS29"
            item.secondary_text = "Offline"
            item.add_widget(IconLeftWidget(icon="account"))
            main_screen.ids.user_list.add_widget(item)
        return sm


if __name__ == "__main__":
    MasDController().run()
