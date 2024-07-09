import time

from kivymd.app import MDApp
from kivy.lang import Builder

from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.config import Config
from kivy.clock import mainthread

from kivymd.uix.list.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRectangleFlatButton


class MainScreen(Screen):
    main = None

    def connect_btn_press(self):
        username_text_input = self.ids.username_text_field.text
        self.main.make_tunnel(username_text_input.upper())


class SettingsScreen(Screen):
    main = None

    def save_username_btn_press(self):
        self.main.save_username_setting()

    def save_restriction_mode_btn_press(self):
        self.main.save_restriction_mode_setting()

    def save_all_btn_press(self):
        self.main.save_all_settings()


class MasDController(MDApp):
    information_dialog = None
    choose_tunnel_creation_dialog = None

    def __init__(self, main):
        super().__init__()

        Config.set('kivy', 'exit_on_escape', '0')  # when I press esc of any other fn key it closes, this negates that

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

    # don't sleep before this is called?? im not sure, have to double-check that
    @mainthread
    def maximize_screen(self):
        Window.minimize()
        Window.maximize()

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        return self.screen_manager

    def accept_tunnel_creation_btn_press(self, requester_name):
        self.choose_tunnel_creation_dialog.dismiss()
        self.main.accept_tunnel_creation(requester_name)

    def decline_tunnel_creation_btn_press(self, requester_name):
        self.choose_tunnel_creation_dialog.dismiss()
        self.main.decline_tunnel_creation(requester_name)

    @mainthread
    def open_choose_tunnel_dialog(self, requester_name):
        if not self.choose_tunnel_creation_dialog:
            self.choose_tunnel_creation_dialog = MDDialog(
                buttons=[
                    MDRectangleFlatButton(
                        text="Accept",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_press=lambda _: self.accept_tunnel_creation_btn_press(requester_name)
                    ),
                    MDRectangleFlatButton(
                        text="Decline",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_press=lambda _: self.decline_tunnel_creation_btn_press(requester_name)
                    ),
                ],
            )

        self.choose_tunnel_creation_dialog.text = str(f"User [b]{requester_name}[/b] is trying to connect")
        self.choose_tunnel_creation_dialog.open()

    @mainthread
    def open_information_dialog(self, msg):
        if not self.information_dialog:
            self.information_dialog = MDDialog(
                buttons=[
                    MDRectangleFlatButton(
                        text="Okay",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda _: self.information_dialog.dismiss()
                    ),
                ],
            )
        self.information_dialog.text = msg
        self.information_dialog.open()

    def on_stop(self):
        self.main.stop()

