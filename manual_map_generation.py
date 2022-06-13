from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle, Color
from array import array
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.switch import Switch
import numpy as np

from constatnts import WORLD_SIDE_SIZE, CELL_SIDE_SIZE, POINT_SIDE_SIZE, GRID_SIDE_SIZE, GUI_MAIN_COLOR, GUI_SEC_COLOR, \
    GUI_TER_COLOR, ITER_AS_SEC
import simulation

MINIMAL_VALUE_TO_SHOW = 10


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


def update_rect(instance, *args):
    instance.rect.pos = instance.pos
    instance.rect.size = instance.size


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_size = GRID_SIDE_SIZE * GRID_SIDE_SIZE
        self.grid_parent = GridLayout(cols=self.grid_size // (int(self.grid_size ** 0.5)), spacing=0,
                                      size_hint=(1, 1))
        self.sea_color = [15, 10, 222]
        self.land_color = [38, 166, 91]
        self.oil_color = [0, 0, 0]
        self.land_with_oil_color = [0, 100, 0]
        self.currently_viewed = True
        self.engine = simulation.SimulationEngine()
        self.engine.start("bruh")

        for i in range(self.grid_size):
            ind = (
                i % (int(self.grid_size ** 0.5)), (i - i % (int(self.grid_size ** 0.5))) // int(self.grid_size ** 0.5))

            buf = self.generate_buf(ind)
            buf2 = [buf[x][y] for x in range(self.grid_size) for y in range(3)]
            arr = array('B', buf2)

            btn = MyButton()
            btn.text = (ind[0], ind[1])
            btn.bind(on_press=self.on_press_func)
            btn.update(arr)
            btn.coords = ind
            self.grid_parent.add_widget(btn)

        with self.grid_parent.canvas.before:
            Color(1, 1, 1, 1)
            self.grid_parent.rect = Rectangle(size=self.grid_parent.size, pos=self.grid_parent.pos)

        self.grid_parent.bind(pos=update_rect, size=update_rect)

        self.switch = Switch(size_hint=(.15, 1))
        self.switch.bind(active=self.change_spacing)

        bottom = BoxLayout(orientation='horizontal', size_hint=(1, .05))

        screen_change_button = Button(background_normal='',
                                      background_color=GUI_MAIN_COLOR,
                                      text='START/STOP')
        screen_change_button.bind(on_press=self.start_stop)

        bottom.add_widget(screen_change_button)
        bottom.add_widget(self.switch)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(self.grid_parent)
        main_widget.add_widget(bottom)

        self.add_widget(main_widget)

    def generate_buf(self, ind):
        arr = []
        for i in range(self.grid_size):
            curr_point = self.engine.world[i % CELL_SIDE_SIZE + 10 * ind[0]][i // CELL_SIDE_SIZE + 10 * ind[1]]
            arr.append((self.land_with_oil_color if curr_point.oil_mass > MINIMAL_VALUE_TO_SHOW else self.land_color)
                       if curr_point.topography == simulation.TopographyState.LAND else self.oil_color
                       if curr_point.oil_mass > MINIMAL_VALUE_TO_SHOW else self.sea_color)
        return arr

    def on_press_func(self, instance):
        self.manager.get_screen('child').curr = instance.text
        self.manager.get_screen('child').update_before_entering()
        self.currently_viewed = False
        self.manager.current = 'child'

    def update(self):
        if self.currently_viewed:
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
        map_arr = np.array([[0 for _ in range(100)] for __ in range(100)])
        for i in range(100):
            for j in range(100):
                map_arr[i][j] = (1 if self.engine.world[j][i].topography == simulation.TopographyState.LAND else 0)
        np.savetxt('topography.csv', map_arr, delimiter='', fmt='%d')

    def change_spacing(self, switch_object, switch_value):
        if switch_value:
            self.grid_parent.spacing = 1
            self.manager.get_screen('child').grid_parent.spacing = 1
        else:
            self.grid_parent.spacing = 0
            self.manager.get_screen('child').grid_parent.spacing = 0

    def update_before_entering(self):
        self.currently_viewed = True
        self.update()


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_running = False
        self.grid_size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.button_object = None
        self.sea_color = [15 / 255, 10 / 255, 222 / 255, 1]
        self.land_color = [38 / 255, 166 / 255, 91 / 255, 1]
        self.oil_color = [0 / 255, 0 / 255, 0 / 255, 1]
        self.currently_viewed = False
        self.curr = (0, 0)
        self.land_with_oil_color = [0, 100 / 255, 0, 1]

        btn = Button(background_normal='', background_color=GUI_TER_COLOR,
                     text='<-- Main screen', size_hint=(.2, 1))
        btn.bind(on_press=self.change_screen)

        up_widget = BoxLayout(orientation='horizontal', size_hint=(1, .1))
        with up_widget.canvas.before:
            Color(GUI_MAIN_COLOR[0], GUI_MAIN_COLOR[1], GUI_MAIN_COLOR[2], 1)
            up_widget.rect = Rectangle(size=up_widget.size, pos=up_widget.pos)

        up_widget.bind(pos=update_rect, size=update_rect)

        up_widget.add_widget(btn)

        self.num_label = Label(text='')
        up_widget.add_widget(self.num_label)

        self.grid_parent = GridLayout(cols=self.grid_size // (int(self.grid_size ** 0.5)), spacing=0)

        for i in range(self.grid_size):
            ind = (
                (i - i % (int(self.grid_size ** 0.5))) // int(self.grid_size ** 0.5), i % (int(self.grid_size ** 0.5)))

            btn = Button(background_normal='', background_color=self.sea_color, text="")
            btn.coords = (ind[0], ind[1])
            btn.bind(on_press=self.on_press_func)
            self.grid_parent.add_widget(btn)

        with self.grid_parent.canvas.before:
            Color(1, 1, 1, 1)
            self.grid_parent.rect = Rectangle(size=self.grid_parent.size, pos=self.grid_parent.pos)

        self.grid_parent.bind(pos=update_rect, size=update_rect)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up_widget)
        main_widget.add_widget(self.grid_parent)

        self.add_widget(main_widget)

    def get_point_object(self, coords):
        return self.manager.get_screen('main').engine.world[coords[1] + 10 * self.curr[0]][
            coords[0] + 10 * self.curr[1]]

    def on_press_func(self, instance):
        point = self.get_point_object(instance.coords)
        if point.topography == simulation.TopographyState.SEA:
            point.topography = simulation.TopographyState.LAND
            instance.background_color = self.land_color
        else:
            point.topography = simulation.TopographyState.SEA
            instance.background_color = self.sea_color
        self.manager.get_screen('main').update_texture(self.button_object)

    def update(self):
        if self.currently_viewed:
            x = 99
            for child in self.grid_parent.children:
                coords = (x // CELL_SIDE_SIZE, x % CELL_SIDE_SIZE)
                point = self.get_point_object(coords)
                if point.oil_mass > MINIMAL_VALUE_TO_SHOW:
                    child.text = str(round(point.oil_mass, self.decimal_places))
                    if point.topography == simulation.TopographyState.LAND:
                        child.background_color = self.land_with_oil_color
                    else:
                        child.background_color = self.oil_color
                else:
                    child.text = ''
                    if point.topography == simulation.TopographyState.LAND:
                        child.background_color = self.land_color
                    else:
                        child.background_color = self.sea_color
                x -= 1

    def change_screen(self, *args):
        self.manager.get_screen('main').update_before_entering()
        self.currently_viewed = False
        self.manager.current = 'main'

    def update_before_entering(self):
        self.currently_viewed = True
        self.num_label.text = 'Currently viewing %d, %d' % (self.curr[0], self.curr[1])
        self.button_object = self.manager.get_screen('main').grid_parent.children[
            -(self.curr[0] + self.curr[1] * 10) + 99]
        self.update()


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
