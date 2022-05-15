from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
# from kivy.graphics import Color

import random

import constatnts
import simulation

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = False
        self.amount = constatnts.GRID_SIDE_SIZE * constatnts.GRID_SIDE_SIZE
        self.clock = None
        # self.randrangee = [0, 255]

        self.grid_parent = GridLayout(cols=self.amount // (int(self.amount ** 0.5)), spacing=2)
        color = [255, 255, 255, 1]

        for i in range(self.amount):
            ind = ((i - i % (int(self.amount ** 0.5))) // int(self.amount ** 0.5), i % (int(self.amount ** 0.5)))

            btn = Button(background_normal='', background_color=color, text='%s, %s' % (ind[0], ind[1]))
            btn.bind(on_press=self.on_press_func)
            self.grid_parent.add_widget(btn)

        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), 2)

        config_parent = BoxLayout(orientation='vertical', size_hint=(.2, 1))
        btn = Button(background_normal='', background_color=[random.random(), random.random(), random.random(), 1],
                     text='Child screen -->', size_hint=(1, .1))
        btn.bind(on_press=self.change_screen)
        config_parent.add_widget(btn)

        config = BoxLayout(orientation='vertical', size_hint=(1, .9))

        config.add_widget(Label(text='Amount of oil added on click', halign='left', valign='middle', text_size=(self.width, None)))
        config.add_widget(TextInput(text='2', multiline=False, input_filter='float'))

        config.add_widget(Label(text='Interval of changes'))
        aa = TextInput(text='2', multiline=False, input_filter='float')
        aa.bind(on_text_validate=self.interval_change)
        config.add_widget(aa)

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
        instance.background_color = [random.random(), random.random(), random.random(), 1]
        self.manager.get_screen('child').curr = (int(instance.text[0]), int(instance.text[3]))

    def update(self, grid):
        if self.flag:
            for child in grid.children:
                child.background_color = [random.random(), random.random(), random.random(), 1]
                # TODO something that generates background from array containing current state of square,
                #  cause currently it makes disco party

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
            self.manager.get_screen('child').flag = self.flag

        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), float(instance.text))
        self.manager.get_screen('child').update_interval(float(instance.text))

    def change_screen(self, instance):
        self.manager.get_screen('child').update_before_entering()
        self.manager.current = 'child'


class ChildGridScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.curr = (0, 0)
        self.flag = False
        self.amount = constatnts.CELL_SIDE_SIZE * constatnts.CELL_SIDE_SIZE
        # self.randrangee = [0, 255]

        btn = Button(background_normal='', background_color=[random.random(), random.random(), random.random(), 1],
                     text='<-- Main screen', size_hint=(.2, 1))
        btn.bind(on_press=self.change_screen)

        up_widget = BoxLayout(orientation='horizontal', size_hint=(1, .1))
        up_widget.add_widget(btn)

        self.num_label = Label(text='Currently viewing %d, %d' % (self.curr[0], self.curr[1]))
        up_widget.add_widget(self.num_label)

        self.grid_parent = GridLayout(cols=self.amount // (int(self.amount ** 0.5)), spacing=1)
        color = [255, 255, 255, 1]

        for i in range(self.amount):
            btn = Button(background_normal='', background_color=color)
            btn.bind(on_press=self.on_press_func)
            self.grid_parent.add_widget(btn)

        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), 2)

        main_widget = BoxLayout(orientation='vertical')
        main_widget.add_widget(up_widget)
        main_widget.add_widget(self.grid_parent)

        self.add_widget(main_widget)

    def on_press_func(self, instance):
        instance.background_color = [random.random(), random.random(), random.random(), 1]

    def update(self, grid):
        if self.flag:
            for child in grid.children:
                child.background_color = [random.random(), random.random(), random.random(), 1]

    def change_screen(self, instance):
        self.manager.current = 'main'

    def update_interval(self, new_interval):
        self.clock.cancel()
        self.clock = Clock.schedule_interval(lambda a: self.update(self.grid_parent), new_interval)

    def update_before_entering(self):
        self.num_label.text = 'Currently viewing %d, %d' % (self.curr[0], self.curr[1])
        # TODO update grid based on currently viewed parent


class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)


class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        
        self.engine = simulation.SimulationEngine() 


    def build(self):
        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ChildGridScreen(name='child'))

        return sm


if __name__ == '__main__':
    MainApp().run()
