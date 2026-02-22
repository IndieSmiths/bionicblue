
### local imports

from ....ani2d.player import AnimationPlayer2D

from ....pygamesetup.constants import SCREEN



class Smartphone:
    
    def __init__(self, pos_name, pos_value):
        
        self.name = 'smartphone'
        self.layer_name = 'middleprops'
        self.aniplayer = AnimationPlayer2D(self, 'smartphone', 'ringing')

        setattr(self.rect, pos_name, pos_value)

    def update(self): pass

    def draw(self):
        self.aniplayer.draw()
