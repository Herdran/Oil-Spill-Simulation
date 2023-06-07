from array import array

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.textinput import TextInput
from kivymd.uix.behaviors import HoverBehavior

Config.set("input", "mouse", "mouse,disable_multitouch")

from constatnts import CELL_SIDE_SIZE, GRID_SIDE_SIZE, ITER_AS_SEC
import simulation

MINIMAL_VALUE_TO_SHOW = 100

GUI_MAIN_COLOR = [51 / 255, 96 / 255, 121 / 255, 1]
GUI_SEC_COLOR = [121 / 255, 111 / 255, 51 / 255, 1]
GUI_TER_COLOR = [121 / 255, 51 / 255, 61 / 255, 1]

sea_color = [15 / 255, 10 / 255, 222 / 255, 1]
land_color = [38 / 255, 166 / 255, 91 / 255, 1]
oil_color = [0 / 255, 0 / 255, 0 / 255, 1]
land_with_oil_color = [0, 100 / 255, 0, 1]
highlight_when_hover_value = 30


def blend_color(color1, color2, ratio, rgb=False):
    ratio = min(ratio, 1)
    if rgb:
        return [int(255 * (color1[i] * ratio + color2[i] * (1 - ratio))) for i in range(len(color1))]
    return [color1[i] * ratio + color2[i] * (1 - ratio) for i in range(len(color1))]


class CustomGridElementWidget(HoverBehavior, ButtonBehavior, Image):
    def __init__(self, coords, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self.texture = Texture.create(size=(CELL_SIDE_SIZE, CELL_SIDE_SIZE))
        self.texture.flip_vertical()
        self.coords = coords
        self.oil_mass_sea = 0
        self.oil_mass_land = 0
        self.texture_arr = [0 for _ in range(CELL_SIDE_SIZE * CELL_SIDE_SIZE * 3)]
        self.hover = False
        # self.highlight = 0

    def set_texture_pixel_val(self, ind, var):
        self.texture_arr[ind * 3] = var[0]
        self.texture_arr[ind * 3 + 1] = var[1]
        self.texture_arr[ind * 3 + 2] = var[2]

    def on_enter(self, *args):
        self.hover = True
        self.update()

    def on_leave(self, *args):
        self.hover = False
        self.update()

    def update(self):
        arr = array('B', [self.texture_arr[i] + (highlight_when_hover_value if self.hover else 0) for i in range(len(self.texture_arr))])
        self.texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')
        self.property('texture').dispatch(self)


def update_rect(instance, *args):
    instance.rect.pos = instance.pos
    instance.rect.size = instance.size


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_running = False
        self.grid_size = GRID_SIDE_SIZE * GRID_SIDE_SIZE
        self.cell_size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.currently_viewed = True
        self.curr_iter = 0
        self.sim_sec_passed = 0
        self.global_oil_amount_sea = 0
        self.global_oil_amount_land = 0
        self.engine = simulation.SimulationEngine()

        self.engine.start()

        self.grid_parent = GridLayout(cols=GRID_SIDE_SIZE, spacing=0, size_hint=(.85, 1))
        with self.grid_parent.canvas.before:
            Color(1, 1, 1, 1)
            self.grid_parent.rect = Rectangle(size=self.grid_parent.size, pos=self.grid_parent.pos)

        self.grid_parent.bind(pos=update_rect, size=update_rect)

        for i in range(self.grid_size):
            ind = (i % GRID_SIDE_SIZE, (i - i % GRID_SIDE_SIZE) // GRID_SIDE_SIZE)
            button_kinda_image_widget = CustomGridElementWidget(ind)

            self.update_texture(button_kinda_image_widget)
            button_kinda_image_widget.bind(on_press=self.on_press_func)

            self.grid_parent.add_widget(button_kinda_image_widget)

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

        settings = BoxLayout(orientation='vertical', size_hint=(1, .45), padding=14, spacing=10)

        with settings.canvas.before:
            Color(GUI_TER_COLOR[0], GUI_TER_COLOR[1], GUI_TER_COLOR[2], 1)
            settings.rect = Rectangle(size=settings.size, pos=settings.pos)

        settings.bind(pos=update_rect, size=update_rect)

        settings.add_widget(Label(text='Oil added on click [kg]', halign='left', valign='middle', text_size=(self.width, None)))
        oil_amount_to_add = TextInput(text='10000', multiline=False, input_filter='float')
        oil_amount_to_add.bind(on_text_validate=self.oil_to_add_change)
        settings.add_widget(oil_amount_to_add)

        settings.add_widget(Label(text='Interval of changes [s]', halign='left', valign='middle', text_size=(self.width, None)))
        interval_of_changes = TextInput(text='1', multiline=False, input_filter='float')
        interval_of_changes.bind(on_text_validate=self.interval_change)
        settings.add_widget(interval_of_changes)

        side_panel_parent.add_widget(self.info_tab)
        side_panel_parent.add_widget(settings)

        up = BoxLayout(orientation='horizontal')
        up.add_widget(self.grid_parent)
        up.add_widget(side_panel_parent)

        start_stop_button = Button(background_normal='',
                                   background_color=GUI_MAIN_COLOR,
                                   text='START SIMULATION', size_hint=(1, .05))
        start_stop_button.bind(on_press=self.start_stop)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up)
        main_widget.add_widget(start_stop_button)

        self.add_widget(main_widget)
        self.clock = Clock.schedule_interval(lambda a: self.update(), 0.001)

    def on_press_func(self, instance):
        self.manager.get_screen('child').curr = instance.coords
        self.manager.get_screen('child').update_before_entering()
        self.currently_viewed = False
        self.manager.current = 'child'

    def update(self, entering=False):
        if self.app_running and not entering:
            self.engine.update(ITER_AS_SEC)
            self.curr_iter += 1
            self.sim_sec_passed += ITER_AS_SEC
        if self.app_running and self.currently_viewed:
            for child in self.grid_parent.children:
                self.update_texture(child)

            self.info_tab.children[3].children[0].text = str(self.curr_iter)

            self.info_tab.children[2].children[0].children[0].text = str(self.sim_sec_passed % 60) + 's'
            self.info_tab.children[2].children[0].children[1].text = str((self.sim_sec_passed // 60) % 60) + 'm'
            self.info_tab.children[2].children[0].children[2].text = str(self.sim_sec_passed // 3600) + 'h'

            self.info_tab.children[1].children[0].children[0].text = str(int(self.global_oil_amount_sea // 10 ** 3) % 10 ** 3) + 't'
            self.info_tab.children[1].children[0].children[1].text = str(int(self.global_oil_amount_sea // 10 ** 6) % 10 ** 3) + 'kt'
            self.info_tab.children[1].children[0].children[2].text = str(int(self.global_oil_amount_sea // 10 ** 9)) + 'Mt'

            self.info_tab.children[0].children[0].children[0].text = str(int(self.global_oil_amount_land // 10 ** 3) % 10 ** 3) + 't'
            self.info_tab.children[0].children[0].children[1].text = str(int(self.global_oil_amount_land // 10 ** 6) % 10 ** 3) + 'kt'
            self.info_tab.children[0].children[0].children[2].text = str(int(self.global_oil_amount_land // 10 ** 9)) + 'Mt'

    def update_texture(self, child):
        ind = child.coords
        new_oil_mass_sea = 0
        new_oil_mass_land = 0
        for i in range(self.cell_size):
            curr_point = self.engine.world[i % CELL_SIDE_SIZE + CELL_SIDE_SIZE * ind[0]][i // CELL_SIDE_SIZE + CELL_SIDE_SIZE * ind[1]]
            if curr_point.change_occurred:
                # curr_point.change_occurred = False  TODO to be used after implementation of "change_occurred" in simulation
                if curr_point.topography == simulation.TopographyState.LAND:
                    var = blend_color(land_with_oil_color, land_color, curr_point.oil_mass / MINIMAL_VALUE_TO_SHOW, True)
                    new_oil_mass_land += curr_point.oil_mass
                else:
                    var = blend_color(oil_color, sea_color, curr_point.oil_mass / MINIMAL_VALUE_TO_SHOW, True)
                    new_oil_mass_sea += curr_point.oil_mass
                child.set_texture_pixel_val(i, var)
        self.global_oil_amount_sea += new_oil_mass_sea - child.oil_mass_sea
        self.global_oil_amount_land += new_oil_mass_land - child.oil_mass_land
        child.oil_mass_sea = new_oil_mass_sea
        child.oil_mass_land = new_oil_mass_land
        child.update()

    def start_stop(self, instance):
        if self.app_running:
            self.app_running = False
            instance.text = "START SIMULATION"
        else:
            self.app_running = True
            instance.text = "STOP SIMULATION"
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

    def update_before_entering(self):
        self.currently_viewed = True
        self.update(True)


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_running = False
        self.clock = None
        self.grid_size = CELL_SIDE_SIZE * CELL_SIDE_SIZE
        self.grid_parent = GridLayout(cols=CELL_SIDE_SIZE, spacing=0)
        self.currently_viewed = False
        self.button_object = None
        self.curr = (0, 0)
        self.oil_to_add_on_click = 10000
        self.decimal_places = 2

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

        for i in range(self.grid_size):
            ind = (
                (i - i % CELL_SIDE_SIZE) // CELL_SIDE_SIZE, i % CELL_SIDE_SIZE)

            btn = Button(background_normal='', background_color=sea_color, text="")
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
            point.add_oil(self.oil_to_add_on_click)
            if instance.background_color != oil_color:
                instance.background_color = oil_color
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
                else:
                    child.text = ''
                if point.topography == simulation.TopographyState.LAND:
                    child.background_color = blend_color(land_with_oil_color, land_color, point.oil_mass / MINIMAL_VALUE_TO_SHOW)
                else:
                    child.background_color = blend_color(oil_color, sea_color, point.oil_mass / MINIMAL_VALUE_TO_SHOW)
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
