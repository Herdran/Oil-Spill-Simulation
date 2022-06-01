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
        self.allow_stretch = True
        self.keep_ratio = False
        self.texture = Texture.create(size=(CELL_SIDE_SIZE, CELL_SIDE_SIZE))
        self.coords = None

    def update(self, arr):
        self.texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')
        self.texture.flip_vertical()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = False
        self.clock = None
        self.grid_size = GRID_SIDE_SIZE * GRID_SIDE_SIZE
        self.grid_parent = GridLayout(cols=self.grid_size // (int(self.grid_size ** 0.5)), spacing=2)
        self.sea_color = [15, 10, 222]
        self.land_color = [38, 166, 91]
        self.oil_color = [200, 101, 0]
        self.engine = simulation.SimulationEngine()
        self.engine.start("bruh")

        for i in range(self.grid_size):
            ind = (i % (int(self.grid_size ** 0.5)), (i - i % (int(self.grid_size ** 0.5))) // int(self.grid_size ** 0.5))

            buf = self.generate_buf(ind)
            buf2 = [buf[x][y] for x in range(self.grid_size) for y in range(3)]
            arr = array('B', buf2)

            btn = MyButton()
            btn.text = (ind[0], ind[1])
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

    def generate_buf(self, ind):
        return [self.land_color if self.engine.world[i % CELL_SIDE_SIZE + 10 * ind[0]][
                                       i // CELL_SIDE_SIZE + 10 * ind[
                                           1]].topography == simulation.TopographyState.LAND else self.oil_color if
        self.engine.world[i % CELL_SIDE_SIZE + 10 * ind[0]][
            i // CELL_SIDE_SIZE + 10 * ind[1]].oil_mass > 0.01 else self.sea_color for i in range(self.grid_size)]

    def on_press_func(self, instance):
        self.manager.get_screen('child').curr = instance.text

    def update(self):
        if self.flag:
            self.engine.update(20)
            for child in self.grid_parent.children:
                self.update_texture(child)

    def update_texture(self, child):
        ind = child.coords
        buf = self.generate_buf(ind)
        buf2 = [buf[x][y] for x in range(self.grid_size) for y in range(3)]
        arr = array('B', buf2)
        texture = Texture.create(size=(CELL_SIDE_SIZE, CELL_SIDE_SIZE))
        texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        child.texture = texture

    def start_stop(self, *args):
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

        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(), float(instance.text))
        self.manager.get_screen('child').update_interval(float(instance.text))

    def oil_to_add_change(self, instance):
        if instance.text == '':
            instance.text = '0'
        self.manager.get_screen('child').oil_to_add_on_click = int(instance.text)

    def change_screen(self, *args):
        self.manager.get_screen('child').update_before_entering()
        self.manager.current = 'child'


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.curr = (0, 0)
        self.flag = False
        self.button_object = None
        self.grid_size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.oil_to_add_on_click = 2
        self.decimal_places = 3

        btn = Button(background_normal='', background_color=[random.random(), random.random(), random.random(), 1],
                     text='<-- Main screen', size_hint=(.2, 1))
        btn.bind(on_press=self.change_screen)

        up_widget = BoxLayout(orientation='horizontal', size_hint=(1, .1))
        up_widget.add_widget(btn)

        self.num_label = Label(text='')
        up_widget.add_widget(self.num_label)

        self.grid_parent = GridLayout(cols=self.grid_size // (int(self.grid_size ** 0.5)), spacing=1)
        self.sea_color = [15 / 255, 10 / 255, 222 / 255, 1]
        self.land_color = [38 / 255, 166 / 255, 91 / 255, 1]
        self.oil_color = [200 / 255, 101 / 255, 0, 1]

        for i in range(self.grid_size):
            ind = ((i - i % (int(self.grid_size ** 0.5))) // int(self.grid_size ** 0.5), i % (int(self.grid_size ** 0.5)))

            btn = Button(background_normal='', background_color=self.sea_color, text="")
            btn.coords = (ind[0], ind[1])
            btn.bind(on_press=self.on_press_func)
            self.grid_parent.add_widget(btn)

        self.clock = Clock.schedule_interval(lambda a: self.update(), 2)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up_widget)
        main_widget.add_widget(self.grid_parent)

        self.add_widget(main_widget)

    def get_point_object(self, coords):
        return self.manager.get_screen('main').engine.world[coords[1] + 10 * self.curr[0]][coords[0] + 10 * self.curr[1]]

    def on_press_func(self, instance):
        point = self.get_point_object(instance.coords)
        if self.oil_to_add_on_click > 0 and point.topography == simulation.TopographyState.SEA:
            point.oil_mass += self.oil_to_add_on_click
            if instance.background_color != self.oil_color:
                instance.background_color = self.oil_color
                self.manager.get_screen('main').update_texture(self.button_object)
            instance.text = str(round(point.oil_mass, self.decimal_places))

    def update(self, entering=False):
        if self.flag or entering:
            x = 99
            for child in self.grid_parent.children:
                coords = (x // CELL_SIDE_SIZE, x % CELL_SIDE_SIZE)
                point = self.get_point_object(coords)
                child.text = ''
                if point.topography == simulation.TopographyState.LAND:
                    child.background_color = self.land_color
                elif point.oil_mass > 0.01:
                    child.background_color = self.oil_color
                    child.text = str(round(point.oil_mass, self.decimal_places))
                else:
                    child.background_color = self.sea_color
                x -= 1

    def change_screen(self, *args):
        self.manager.current = 'main'

    def update_interval(self, new_interval):
        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), new_interval)

    def update_before_entering(self):
        self.num_label.text = 'Currently viewing %d, %d' % (self.curr[0], self.curr[1])
        self.button_object = self.manager.get_screen('main').grid_parent.children[-(self.curr[0] + self.curr[1] * 10) + 99]
        self.update(True)


class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)


class MainApp(App):
    def build(self):
        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ChildGridScreen(name='child'))
        return sm


if __name__ == '__main__':
    MainApp().run()
