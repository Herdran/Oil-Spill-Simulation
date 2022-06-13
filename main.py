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
        self.app_running = False
        self.clock = None
        self.grid_size = GRID_SIDE_SIZE * GRID_SIDE_SIZE
        self.grid_parent = GridLayout(cols=self.grid_size // (int(self.grid_size ** 0.5)), spacing=0,
                                      size_hint=(.85, 1))
        self.sea_color = [15, 10, 222]
        self.land_color = [38, 166, 91]
        self.oil_color = [0, 0, 0]
        self.land_with_oil_color = [0, 100, 0]
        self.currently_viewed = True
        self.curr_iter = 0
        self.sim_sec_passed = 0
        self.global_oil_amount_sea = 0
        self.global_oil_amount_land = 0
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

        self.clock = Clock.schedule_interval(lambda a: self.update(), 1)

        side_panel_parent = BoxLayout(orientation='vertical', size_hint=(.18, 1))

        self.info_tab = BoxLayout(orientation='vertical', size_hint=(1, .55), spacing=1)

        info_tab_1 = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        info_tab_2 = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        info_tab_3 = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        info_tab_4 = BoxLayout(orientation='horizontal', size_hint=(1, 1))

        info_tab_1.add_widget(Button(text='Current iteration', halign='center', valign='middle',
                                     text_size=(self.width, None), background_color=GUI_MAIN_COLOR,
                                     disabled=True, background_normal='', background_disabled_normal='',
                                     disabled_color=[1, 1, 1, 1], size_hint=(.7, 1)))
        info_tab_1.add_widget(Button(text='0', halign='center', valign='bottom',
                                     text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                                     disabled=True, background_normal='', background_disabled_normal='',
                                     disabled_color=[1, 1, 1, 1], size_hint=(.3, 1)))
        self.info_tab.add_widget(info_tab_1)

        info_tab_2.add_widget(Button(text='Simulation time', halign='center', valign='middle',
                                     text_size=(self.width, None), background_color=GUI_MAIN_COLOR,
                                     disabled=True, background_normal='', background_disabled_normal='',
                                     disabled_color=[1, 1, 1, 1], size_hint=(.7, 1)))
        sim_time_box = BoxLayout(orientation='vertical', size_hint=(.3, 1))
        sim_time_box.add_widget(Button(text='0h', halign='center', valign='bottom',
                                       text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                                       disabled=True, background_normal='', background_disabled_normal='',
                                       disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_time_box.add_widget(Button(text='0m', halign='center', valign='bottom',
                                       text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                                       disabled=True, background_normal='', background_disabled_normal='',
                                       disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_time_box.add_widget(Button(text='0s', halign='center', valign='bottom',
                                       text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                                       disabled=True, background_normal='', background_disabled_normal='',
                                       disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        info_tab_2.add_widget(sim_time_box)
        self.info_tab.add_widget(info_tab_2)

        info_tab_3.add_widget(Button(text='Global oil amount [sea]', halign='center', valign='middle',
                                     text_size=(self.width, None), background_color=GUI_MAIN_COLOR,
                                     disabled=True, background_normal='', background_disabled_normal='',
                                     disabled_color=[1, 1, 1, 1], size_hint=(.7, 1)))
        sim_mass_box_sea = BoxLayout(orientation='vertical', size_hint=(.3, 1))
        sim_mass_box_sea.add_widget(
            Button(text=str(self.global_oil_amount_sea // 10 ** 9) + 'Mt', halign='center', valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_mass_box_sea.add_widget(
            Button(text=str((self.global_oil_amount_sea // 10 ** 6) % 10 ** 3) + 'kt', halign='center', valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_mass_box_sea.add_widget(
            Button(text=str((self.global_oil_amount_sea // 10 ** 3) % 10 ** 3) + 't', halign='center', valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        info_tab_3.add_widget(sim_mass_box_sea)
        self.info_tab.add_widget(info_tab_3)

        info_tab_4.add_widget(Button(text='Global oil amount [land]', halign='center', valign='middle',
                                     text_size=(self.width, None), background_color=GUI_MAIN_COLOR,
                                     disabled=True, background_normal='', background_disabled_normal='',
                                     disabled_color=[1, 1, 1, 1], size_hint=(.7, 1)))
        sim_mass_box_land = BoxLayout(orientation='vertical', size_hint=(.3, 1))
        sim_mass_box_land.add_widget(
            Button(text=str(self.global_oil_amount_land // 10 ** 9) + 'Mt', halign='center', valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_mass_box_land.add_widget(
            Button(text=str((self.global_oil_amount_land // 10 ** 6) % 10 ** 3) + 'kt', halign='center',
                   valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        sim_mass_box_land.add_widget(
            Button(text=str((self.global_oil_amount_land // 10 ** 3) % 10 ** 3) + 't', halign='center', valign='bottom',
                   text_size=(self.width, None), background_color=GUI_SEC_COLOR,
                   disabled=True, background_normal='', background_disabled_normal='',
                   disabled_color=[1, 1, 1, 1], size_hint=(1, 1)))
        info_tab_4.add_widget(sim_mass_box_land)
        self.info_tab.add_widget(info_tab_4)

        config = BoxLayout(orientation='vertical', size_hint=(1, .45), padding=14, spacing=10)

        with config.canvas.before:
            Color(GUI_TER_COLOR[0], GUI_TER_COLOR[1], GUI_TER_COLOR[2], 1)
            config.rect = Rectangle(size=config.size, pos=config.pos)

        config.bind(pos=update_rect, size=update_rect)

        config.add_widget(
            Label(text='Oil added on click [kg]', halign='left', valign='middle', text_size=(self.width, None)))
        oil_amount_to_add = TextInput(text='10000', multiline=False, input_filter='float')
        oil_amount_to_add.bind(on_text_validate=self.oil_to_add_change)
        config.add_widget(oil_amount_to_add)

        config.add_widget(
            Label(text='Interval of changes [s]', halign='left', valign='middle', text_size=(self.width, None)))
        interval_of_changes = TextInput(text='1', multiline=False, input_filter='float')
        interval_of_changes.bind(on_text_validate=self.interval_change)
        config.add_widget(interval_of_changes)

        config.add_widget(Label(text='Grid switch'))

        self.switch = Switch()
        self.switch.bind(active=self.change_spacing)
        config.add_widget(self.switch)

        side_panel_parent.add_widget(self.info_tab)
        side_panel_parent.add_widget(config)

        up = BoxLayout(orientation='horizontal')
        up.add_widget(self.grid_parent)
        up.add_widget(side_panel_parent)

        screen_change_button = Button(background_normal='',
                                      background_color=GUI_MAIN_COLOR,
                                      text='START/STOP', size_hint=(1, .05))
        screen_change_button.bind(on_press=self.start_stop)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up)
        main_widget.add_widget(screen_change_button)

        self.add_widget(main_widget)

    def generate_buf(self, ind):
        arr = []
        for i in range(self.grid_size):
            curr_point = self.engine.world[i % CELL_SIDE_SIZE + 10 * ind[0]][i // CELL_SIDE_SIZE + 10 * ind[1]]
            arr.append((self.land_with_oil_color if curr_point.oil_mass > MINIMAL_VALUE_TO_SHOW else self.land_color)
                       if curr_point.topography == simulation.TopographyState.LAND else self.oil_color
                       if curr_point.oil_mass > MINIMAL_VALUE_TO_SHOW else self.sea_color)
            if curr_point.topography == simulation.TopographyState.SEA:
                self.global_oil_amount_sea += curr_point.oil_mass
            else:
                self.global_oil_amount_land += curr_point.oil_mass
        return arr

    def on_press_func(self, instance):
        self.manager.get_screen('child').curr = instance.text
        self.manager.get_screen('child').update_before_entering()
        self.currently_viewed = False
        self.manager.current = 'child'

    def update(self, entering=False):
        if self.app_running and not entering:
            self.engine.update(ITER_AS_SEC)
            self.curr_iter += 1
            self.sim_sec_passed += ITER_AS_SEC
        if self.currently_viewed:
            self.global_oil_amount_sea = 0
            for child in self.grid_parent.children:
                self.update_texture(child)
            self.info_tab.children[3].children[0].text = str(self.curr_iter)

            self.info_tab.children[2].children[0].children[0].text = str(self.sim_sec_passed % 60) + 's'
            self.info_tab.children[2].children[0].children[1].text = str((self.sim_sec_passed // 60) % 60) + 'm'
            self.info_tab.children[2].children[0].children[2].text = str(self.sim_sec_passed // 3600) + 'h'

            self.info_tab.children[1].children[0].children[0].text = str(
                int(self.global_oil_amount_sea // 10 ** 3) % 10 ** 3) + 't'
            self.info_tab.children[1].children[0].children[1].text = str(
                int(self.global_oil_amount_sea // 10 ** 6) % 10 ** 3) + 'kt'
            self.info_tab.children[1].children[0].children[2].text = str(
                int(self.global_oil_amount_sea // 10 ** 9)) + 'Mt'

            self.info_tab.children[0].children[0].children[0].text = str(
                int(self.global_oil_amount_land // 10 ** 3) % 10 ** 3) + 't'
            self.info_tab.children[0].children[0].children[1].text = str(
                int(self.global_oil_amount_land // 10 ** 6) % 10 ** 3) + 'kt'
            self.info_tab.children[0].children[0].children[2].text = str(
                int(self.global_oil_amount_land // 10 ** 9)) + 'Mt'

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
        if self.app_running:
            self.app_running = False
        else:
            self.app_running = True
        self.manager.get_screen('child').app_running = self.app_running

    def interval_change(self, instance):
        if instance.text == '' or float(instance.text) < 0.1:
            instance.text = '0.1'

        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(), float(instance.text))
        self.manager.get_screen('child').interval_change_child(float(instance.text))

    def oil_to_add_change(self, instance):
        if instance.text == '':
            instance.text = '0'
        self.manager.get_screen('child').oil_to_add_on_click = float(instance.text)

    def change_spacing(self, switch_object, switch_value):
        if switch_value:
            self.grid_parent.spacing = 1
            self.manager.get_screen('child').grid_parent.spacing = 1
        else:
            self.grid_parent.spacing = 0
            self.manager.get_screen('child').grid_parent.spacing = 0

    def update_before_entering(self):
        self.currently_viewed = True
        self.update(True)


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_running = False
        self.clock = None
        self.grid_size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.button_object = None
        self.sea_color = [15 / 255, 10 / 255, 222 / 255, 1]
        self.land_color = [38 / 255, 166 / 255, 91 / 255, 1]
        self.oil_color = [0 / 255, 0 / 255, 0 / 255, 1]
        self.currently_viewed = False
        self.curr = (0, 0)
        self.oil_to_add_on_click = 10000
        self.decimal_places = 2
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

        self.clock = Clock.schedule_interval(lambda a: self.update(), 1)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up_widget)
        main_widget.add_widget(self.grid_parent)

        self.add_widget(main_widget)

    def get_point_object(self, coords):
        return self.manager.get_screen('main').engine.world[coords[1] + 10 * self.curr[0]][
            coords[0] + 10 * self.curr[1]]

    def on_press_func(self, instance):
        point = self.get_point_object(instance.coords)
        if self.oil_to_add_on_click > 0 and point.topography == simulation.TopographyState.SEA:
            point.oil_mass += self.oil_to_add_on_click
            if instance.background_color != self.oil_color:
                instance.background_color = self.oil_color
                self.manager.get_screen('main').update_texture(self.button_object)
            self.manager.get_screen('main').global_oil_amount_sea += self.oil_to_add_on_click
            instance.text = str(round(point.oil_mass, self.decimal_places))

    def update(self, entering=False):
        if (self.app_running or entering) and self.currently_viewed:
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

    def interval_change_child(self, new_interval):
        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), new_interval)

    def update_before_entering(self):
        self.currently_viewed = True
        self.num_label.text = 'Currently viewing %d, %d' % (self.curr[0], self.curr[1])
        self.button_object = self.manager.get_screen('main').grid_parent.children[
            -(self.curr[0] + self.curr[1] * 10) + 99]
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
