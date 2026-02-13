
### local import
from ....ani2d.player import AnimationPlayer2D



class FoodBox:

    def __init__(self):

        self.name = 'food_box'
        self.layer_name = 'middleprops'

        self.aniplayer = AnimationPlayer2D(self, 'food_box', 'idle')

    def update(self): pass

    def draw(self):
        self.aniplayer.draw()
