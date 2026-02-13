
### local import
from ....ani2d.player import AnimationPlayer2D



class LargeDish:

    def __init__(self, animation_name, center):

        self.name = 'large_dish'
        self.layer_name = 'middleprops'

        self.aniplayer = AnimationPlayer2D(self, animation_name, 'idle')

        setattr(self.rect, 'center', center)

    def update(self): pass

    def draw(self):
        self.aniplayer.draw()
