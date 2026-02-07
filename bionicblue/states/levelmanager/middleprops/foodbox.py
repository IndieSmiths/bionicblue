
### third-party import
from pygame import Surface


### local import
from ....ani2d.player import AnimationPlayer2D



class FoodBox:

    def __init__(self, name, midbottom):

        self.name = name

        self.aniplayer = AnimationPlayer2D(self, 'food_box', 'idle')

        setattr(self.rect, 'midbottom', midbottom)

    def update(self): pass

    def draw(self):
        self.aniplayer.draw()
