#-*- coding: utf-8 -*-
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'

from traits.api import *
from traitsui.api import *
from pyface.image_resource import ImageResource

from network import Network
from data import TrainingData
from dumper import Dumper
from training import *
from shared import Shared
from logger import Logger
from animations import *
from plots.mplfigure import MPLPlotter
from actions import toolbar


class View(View):
    icon = ImageResource('ffnetui128x128.ico')


class SettingsHandler(Handler):
    def close(self, info, is_ok):
        if is_ok:
            obj = info.object
            status = obj.data.load()
            if not status:
                return False
            if obj._pmode != obj.mode or len(obj.plist) == 0:
                obj.arrange_plots()
            else:
                obj.selected.replot()
        return True
        #return Handler.close(self, info, is_ok)

class FFnetApp(HasTraits):
    network = Instance(Network)
    data = Instance(TrainingData)
    dumper = Instance(Dumper)
    trainer = Instance(Trainer)
    shared = Instance(Shared)
    logs = Instance(Logger)
    plist = List([], value=MPLPlotter, transient=True)
    selected = Instance(MPLPlotter, transient=True)  # Cannot be pickled when animation runs
    shell = PythonValue(Dict)
    mode = Enum('train', 'test', 'recall')
    algorithm = Enum('tnc', 'bfgs', 'cg')
    running = DelegatesTo('trainer')
    net = DelegatesTo('network')
    data_status = DelegatesTo('data',  prefix='status')
    #data_info = DelegatesTo('data',  prefix='status_info')
    #net_info = DelegatesTo('network', 'filename')

    def __init__(self, **traits):
        super(FFnetApp, self).__init__(**traits)
        self.network = Network(app = self)
        self.data = TrainingData(app = self)
        self.dumper = Dumper(app=self)
        self.trainer = TncTrainer(app = self) # default trainer
        self.shared = Shared()
        self.logs = Logger()
        from ffnet import version
        self.logs.logger.info('Welcome! You are using ffnet-%s.' %version)
        self.shell = {'app':self}

    def new(self):
        net = self.network.create()
        if net is not None:
            self.mode = 'train'
            self.data.normalize = True
            data_status = False
            if self.data.status == 2:
                data_status = self.data.load()  # here we test data
            if not data_status:
                self.data = TrainingData(app=self) 
                self.settings()
            else:
                self.logs.logger.info('Using previously loaded data.')

    def load(self):
        net = self.network.load()
        if net is not None:
            self.mode = 'recall'
            data_status = False
            if self.data.status > 0:
                data_status = self.data.load()  # here we test data
            if not data_status:
                self.data = TrainingData(app=self) 
                self.settings()
            else:
                self.logs.logger.info('Using previously loaded data.')

    def save_as(self):
        self.network.save_as()

    def export(self):
        raise NotImplementedError

    def dump(self):
        self.dumper.configure_traits(kind='modal')

    def settings(self):
        if self.net:
            self._pmode = self.mode
            self.edit_traits(view='settings_view', kind='livemodal')

    def train_start(self):
        self.logs.logger.info('Training network: %s' %self.network.filename)
        self.trainer.train()

    def train_stop(self):
        self.trainer.running = False

    def reset(self):
        if self.net:
            self.net.randomweights()
            self.logs.logger.info('Weights has been randomized!')
        self.clear()

    def clear(self):
        self.shared.populate() 
        if self.selected is not None:
            self.selected.replot()

    def add_plot(self, cls):
        if any(isinstance(p, cls) for p in self.plist):  # plot is just opened
            for p in self.plist:
                if isinstance(p, cls):
                    if self.selected == p:
                        self.selected.replot()
                    else:
                        self.selected = p  # will be replotted automatically
                    break
        else:
            p = cls(app = self, interval=250)
            self.plist = self.plist + [p]
            self.selected = p

    def arrange_plots(self):
        self.plist = []
        if self.mode == 'train':
            plots = [ErrorAnimation, RegressionAnimation, TOAnimation, ITOAnimation, DIOAnimation, GraphAnimation]
        elif self.mode == 'test':
            plots = [RegressionPlot, TOPlot, ITOPlot, DIOAnimation, GraphAnimation]
        else:
            plots = [IOPlot, DIOAnimation, GraphAnimation]
        for p in plots:
            self.add_plot(p)
        self.selected = self.plist[0]

    def _algorithm_changed(self, new):
        if new == 'tnc':
            self.trainer = TncTrainer(app=self)
        if new == 'cg':
            self.trainer = CgTrainer(app=self)
        if new == 'bfgs':
            self.trainer = BfgsTrainer(app=self)

    def _selected_changed(self, old, new):
        if self.trainer.running:
            try:
                old.stop()  # Assume we have animation
            except:
                pass  # But simple plot can be also
            try:
                new.start()  # Assume we have animation
            except:
                new.replot()  # But simple plot can be also
        else:
            new.replot()

    traits_view = View(VSplit(Item('plist',
                            visible_when = 'len(plist) > 0',
                            style='custom',
                            show_label=False,
                            height = 0.75,
                            editor=ListEditor(use_notebook=True,
                                              show_notebook_menu = False,
                                              deletable=False,
                                              dock_style='tab',
                                              selected='selected',
                                              view = 'figure_view',
                                              page_name = '.name')),
                              Tabbed(UItem('logs',
                                           style='custom',
                                           dock = 'tab',
                                           export = 'DockWindowShell'),
                                     UItem('shell',
                                           label  = 'Shell',
                                           editor = ShellEditor( share = True ),
                                           dock   = 'tab',
                                           export = 'DockWindowShell'
                                           ),
                                     #show_labels = False
                                    )
                              ),
                             #),
                       title = 'Feed-forward neural network trainer',
                       width = 0.6,
                       height = 0.8,
                       resizable = True,
                       toolbar = toolbar,
                       #menubar = menubar,
                       #statusbar = [StatusItem(name = 'net_info', width=0.5),
                                    #StatusItem(name = 'data_info', width=0.5)]
                       )

    settings_view = View(Item('mode', emphasized=True),
                         '_',
                        Group(Item('object.data.input_loader',
                                   style='custom',
                                   label='Input file',),
                             Item('object.data.target_loader',
                                   style='custom',
                                   label='Target file'),
                             Group(Item('object.data.validation_patterns',
                                        label = 'Validation patterns [%]'),
                                   Item('object.data.validation_type'),
                                   Item('object.data.normalize')),
                             visible_when = 'mode == "train"'),
                       Group(Item('object.data.input_loader',
                                   style='custom',
                                   label='Input file',),
                             Item('object.data.target_loader',
                                   style='custom',
                                   label='Target file'),
                             visible_when = 'mode == "test"'),
                       Group(Item('object.data.input_loader',
                                   style='custom',
                                   label='Input file',),
                             visible_when = 'mode == "recall"'),
                         '_',
                         Group(Item('algorithm', label = 'Training algorithm'), 
                               UItem('object.trainer', style='custom'),
                               Item('object.trainer.best_weights'),
                               visible_when='mode == "train"'),
                         buttons = ['OK', 'Cancel'],
                         handler = SettingsHandler(),
                         title = 'Settings...',
                         resizable = True,
                         scrollable = True,
                         width = 0.4)



def main():
    app = FFnetApp()
    app.configure_traits()

def test():
    app = FFnetApp()
    # Add test network
    from ffnet import loadnet
    n = app.network
    path = 'data/testnet.net'
    n.net = loadnet(path)
    n.filename = path
    ## Add test data
    app.data.input_loader.filename = 'data/black-scholes-input.dat'
    app.data.target_loader.filename = 'data/black-scholes-target.dat'
    app.data.load()
    app.mode = 'recall'
    app.arrange_plots()
    # Run
    app.configure_traits()

if __name__=="__main__":
    import multiprocessing as mp
    mp.freeze_support()
    #main()
    test()
