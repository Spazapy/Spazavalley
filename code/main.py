import pygame, sys
from Settings import *
from level import Level

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Spaza Valley")
        self.clock = pygame.time.Clock()
        self.levels = {}
        
        # Create the first level and cache it
        first_level = Level(self.switch_level, 'map', 'Start')
        self.levels['map'] = first_level
        self.level = first_level

    def switch_level(self, new_map, spawn_location):
        player = self.level.player # Get player from the current level
        
        if new_map in self.levels:
            # The level is already cached, just switch to it
            self.level = self.levels[new_map]
        else:
            # Create the new level and cache it
            new_level_instance = Level(self.switch_level, new_map, spawn_location, player)
            self.levels[new_map] = new_level_instance
            self.level = new_level_instance
            return # The setup for the new level already places the player correctly

        # If we are switching to an *existing* level, we need to manually place the player
        # and make sure the player is in the correct sprite groups.
        self.level.player.kill() # remove from all groups
        self.level.all_sprites.add(self.level.player)
        self.level.player.collision_sprites = self.level.collision_sprites
        self.level.player.tree_sprites = self.level.tree_sprites
        self.level.player.interaction = self.level.interaction_sprites
        self.level.player.soil_layer = self.level.soil_layer
        
        for obj in self.level.tmx_data.get_layer_by_name("Player"):
            if obj.name == spawn_location:
                self.level.player.pos.x = obj.x
                self.level.player.pos.y = obj.y
                break

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            dt = self.clock.tick() / 1000
            self.level.run(dt)
            pygame.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
