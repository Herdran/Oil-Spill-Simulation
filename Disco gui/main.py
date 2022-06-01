from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from array import array
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior

import random

from constatnts import WORLD_SIDE_SIZE, CELL_SIDE_SIZE, POINT_SIDE_SIZE, GRID_SIDE_SIZE
import simulation


class MyButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.background_disabled_down = "atlas://data/images/defaulttheme/button_disabled_pressed"
        # self.background_disabled_normal = "atlas://data/images/defaulttheme/button_disabled"
        self.allow_stretch = True
        self.keep_ratio = False
        self.texture = Texture.create(size=(CELL_SIDE_SIZE, CELL_SIDE_SIZE))
        self.coords = None

    # def texture_handler(self, arr):
    #     self.texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')

    # def on_press(self):
    #     pass
    #     print("aaa")
    #     self.source = 'atlas://data/images/defaulttheme/checkbox_on'

    # def on_release(self):
    #     self.source = 'atlas://data/images/defaulttheme/checkbox_off'

    def update(self, arr):
        self.texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')
        self.texture.flip_vertical()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = False
        self.amount = GRID_SIDE_SIZE * GRID_SIDE_SIZE
        self.clock = None
        self.engine = simulation.SimulationEngine()
        self.engine.start("bruh")

        self.grid_parent = GridLayout(cols=self.amount // (int(self.amount ** 0.5)), spacing=2)
        self.white_color = [255, 255, 255, 1]
        self.oil_color = [195, 81, 24, 1]  # Honestly looks shitty

        for i in range(self.amount):
            ind = ((i - i % (int(self.amount ** 0.5))) // int(self.amount ** 0.5), i % (int(self.amount ** 0.5)))
            size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
            buf = [self.oil_color if self.engine.world[i // CELL_SIDE_SIZE + 10 * ind[0]][
                i % CELL_SIDE_SIZE + 10 * ind[1]].contain_oil() else self.white_color for i in range(size)]
            buf2 = [buf[x][y] for x in range(size) for y in range(3)]
            arr = array('B', buf2)

            btn = MyButton()
            btn.text = '%s, %s' % (ind[0], ind[1])
            btn.bind(on_press=self.on_press_func)
            btn.update(arr)
            btn.coords = ind
            self.grid_parent.add_widget(btn)

        self.clock = Clock.schedule_interval(lambda a: self.update(), 2)

        config_parent = BoxLayout(orientation='vertical', size_hint=(.2, 1))
        btn = Button(background_normal='', background_color=[random.random(), random.random(), random.random(), 1],
                     text='Child screen -->', size_hint=(1, .1))
        btn.bind(on_press=self.change_screen)
        config_parent.add_widget(btn)

        config = BoxLayout(orientation='vertical', size_hint=(1, .9))

        config.add_widget(
            Label(text='Amount of oil added on click', halign='left', valign='middle', text_size=(self.width, None)))
        oil_amount_to_add = TextInput(text='2', multiline=False, input_filter='float')
        oil_amount_to_add.bind(on_text_validate=self.oil_to_add_change)
        config.add_widget(oil_amount_to_add)

        config.add_widget(Label(text='Interval of changes'))
        interval_of_changes = TextInput(text='2', multiline=False, input_filter='float')
        interval_of_changes.bind(on_text_validate=self.interval_change)
        config.add_widget(interval_of_changes)

        config_parent.add_widget(config)

        up = BoxLayout(orientation='horizontal')
        up.add_widget(self.grid_parent)
        up.add_widget(config_parent)

        screen_change_button = Button(background_normal='',
                                      background_color=[random.random(), random.random(), random.random(), 1],
                                      text='START/STOP', size_hint=(1, .05))
        screen_change_button.bind(on_press=self.start_stop)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up)
        main_widget.add_widget(screen_change_button)

        self.add_widget(main_widget)

    def on_press_func(self, instance):
        self.manager.get_screen('child').curr = (int(instance.text[0]), int(instance.text[3]))

    def update(self):
        if self.flag:
            self.engine.update(1)
            # i = 99
            size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
            for child in self.grid_parent.children:
                self.update_texture(child, size)
                # i -= 1

    def update_texture(self, child, size):
        ind = child.coords
        buf = [self.oil_color if self.engine.world[i // CELL_SIDE_SIZE + 10 * ind[0]][
            i % CELL_SIDE_SIZE + 10 * ind[1]].contain_oil() else self.white_color for i in range(size)]
        buf2 = [buf[x][y] for x in range(size) for y in range(3)]
        arr = array('B', buf2)
        texture = Texture.create(size=(CELL_SIDE_SIZE, CELL_SIDE_SIZE))
        texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        child.texture = texture

    def start_stop(self, instance):
        if self.flag:
            self.flag = False
        else:
            self.flag = True
        self.manager.get_screen('child').flag = self.flag

    def interval_change(self, instance):
        if instance.text == '':
            instance.text = '0'
            self.flag = False
            self.manager.get_screen('child').flag = False
            # self.manager.get_screen('child').flag = self.flag

        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(), float(instance.text))
        self.manager.get_screen('child').update_interval(float(instance.text))

    def oil_to_add_change(self, instance):
        if instance.text == '':
            instance.text = '0'
        self.manager.get_screen('child').oil_to_add_on_click = int(instance.text)

    def change_screen(self, instance):
        self.manager.get_screen('child').update_before_entering()
        self.manager.current = 'child'


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.curr = (0, 0)
        self.flag = False
        self.button_object = None
        self.amount = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.oil_to_add_on_click = 2
        self.decimal_places = 3

        btn = Button(background_normal='', background_color=[random.random(), random.random(), random.random(), 1],
                     text='<-- Main screen', size_hint=(.2, 1))
        btn.bind(on_press=self.change_screen)

        up_widget = BoxLayout(orientation='horizontal', size_hint=(1, .1))
        up_widget.add_widget(btn)

        self.num_label = Label(text='Currently viewing %d, %d' % (self.curr[0], self.curr[1]))
        up_widget.add_widget(self.num_label)

        self.grid_parent = GridLayout(cols=self.amount // (int(self.amount ** 0.5)), spacing=1)
        self.white_color = [255, 255, 255, 1]
        self.oil_color = [195 / 255, 81 / 255, 24 / 255, 1]

        for i in range(self.amount):
            ind = ((i - i % (int(self.amount ** 0.5))) // int(self.amount ** 0.5), i % (int(self.amount ** 0.5)))

            btn = Button(background_normal='', background_color=self.white_color, text="0.0")
            btn.coords = '%s, %s' % (ind[0], ind[1])
            btn.bind(on_press=self.on_press_func)
            self.grid_parent.add_widget(btn)

        self.clock = Clock.schedule_interval(lambda a: self.update(), 2)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up_widget)
        main_widget.add_widget(self.grid_parent)

        self.add_widget(main_widget)

    def on_press_func(self, instance):
        if self.oil_to_add_on_click > 0:
            self.manager.get_screen('main').engine.world[int(instance.coords[0]) + 10 * self.curr[0]][
                int(instance.coords[3]) + 10 * self.curr[1]].oil_mass += self.oil_to_add_on_click
            if instance.background_color != self.oil_color:
                instance.background_color = self.oil_color
                self.manager.get_screen('main').update_texture(self.button_object, self.amount)
        instance.text = str(round(
            self.manager.get_screen('main').engine.world[int(instance.coords[0]) + 10 * self.curr[0]][
                int(instance.coords[3]) + 10 * self.curr[1]].oil_mass, self.decimal_places))

    def update(self, entering=False):
        if self.flag or entering:
            x = 99
            for child in self.grid_parent.children:
                if self.manager.get_screen('main').engine.world[x // CELL_SIDE_SIZE + 10 * self.curr[0]][
                    x % CELL_SIDE_SIZE + 10 * self.curr[1]].oil_mass > 0.1:
                    child.background_color = self.oil_color
                    child.text = str(
                        round(self.manager.get_screen('main').engine.world[x // CELL_SIDE_SIZE + 10 * self.curr[0]][
                                  x % CELL_SIDE_SIZE + 10 * self.curr[1]].oil_mass, self.decimal_places))
                else:
                    child.background_color = self.white_color
                x -= 1

    def change_screen(self, instance):
        self.manager.current = 'main'

    def update_interval(self, new_interval):
        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), new_interval)

    def update_before_entering(self):
        self.num_label.text = 'Currently viewing %d, %d' % (self.curr[0], self.curr[1])
        self.button_object = self.manager.get_screen('main').grid_parent.children[
            -(self.curr[0] * 10 + self.curr[1]) + 99]
        self.update(True)


class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)


class MainApp(App):
    # def __init__(self, **kwargs):
    #     super(MainApp, self).__init__(**kwargs)
    #
    #     self.engine = simulation.SimulationEngine()

    def build(self):
        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ChildGridScreen(name='child'))
        # self.engine.start("bruh")
        # print(self.engine.world[0][0].oil_mass)
        return sm


if __name__ == '__main__':
    MainApp().run()
