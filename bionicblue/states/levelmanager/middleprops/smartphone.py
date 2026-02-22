
### local imports

from ....ani2d.player import AnimationPlayer2D

from ....pygamesetup.constants import SCREEN



class Smartphone:
    
    def __init__(self):
        
        self.name = 'smartphone'
        self.layer_name = 'middleprops'
        self.aniplayer = AnimationPlayer2D(self, 'smartphone', 'ringing')

    def update(self): pass

    def draw(self):
        self.aniplayer.draw()
