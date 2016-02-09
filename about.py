#-*- coding: utf-8 -*-
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'

from pyface.image_resource import ImageResource
from pyface.api import AboutDialog

about = AboutDialog(parent = None,
                    image = ImageResource('ffnetui256x256'),
                    additions = ['<b>ffnetui-0.8.1</b>', '[EVALUATION ONLY!]',
                                 '',
                                 'This is user interface for ffnet - ',
                                 'feed-forward neural network for python',
                                 '<a href=ffnet.sourceforge.net>http://ffnet.sourceforge.net</a>',
                                 '',
                                 'Copyright &copy; 2011-2015', '<b>Marek Wojciechowski</b>',
                                 'Technical University of Lodz, Poland',
                                 '<a href=mailto:mwojc@p.lodz.pl>mwojc@p.lodz.pl</a>',
                                 '',
                                 ''])

if __name__ == "__main__":
    about.open()