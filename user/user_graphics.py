from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window

Window.maximize()

class ControllerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        return Builder.load_file("user_graphics.kv")


if __name__ == "__main__":
    ControllerApp().run()