from typing import Iterable, Union
import pygame
from pygame.sprite import AbstractGroup

from Settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from Support import *
from Transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from menu import Menu

class Level:
    def __init__(self, switch_level, current_map = 'map', player = None):

        #get the display surface
        self.display_surface = pygame.display.get_surface()
        self.switch_level = switch_level

        #sprite groups
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        
        self.current_map = current_map
        if self.current_map == 'map':
            tmx_data = load_pygame("data/map.tmx")
            ground_image_path = "graphics/world/ground.png"
        else:
            tmx_data = load_pygame("data/map2.tmx")
            ground_image_path = "graphics/world/ground2.png"
        
        self.ground_sprite = Generic(pos=(0,0), surf=pygame.image.load(ground_image_path).convert_alpha(), groups=[], z=LAYERS["ground"])
        self.all_sprites = CameraGroup(self.ground_sprite)
        self.all_sprites.add(self.ground_sprite)

        self.setup(tmx_data, ground_image_path, player)
            
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        # sky
        if self.current_map == 'map':
            self.rain = Rain(self.all_sprites, "graphics/world/ground.png")
        else:
            self.rain = Rain(self.all_sprites, "graphics/world/ground2.png")
        self.raining = randint(0,10) > 7
        self.soil_layer.raining = self.raining
        self.sky = Sky()

        # shop
        self.menu = Menu(self.player, self.toggle_shop)
        self.shop_active = False

        # music
        self.success = pygame.mixer.Sound('audio/success.wav')
        self.success.set_volume(0.3)
        self.background_sound = pygame.mixer.Sound('audio/bg.mp3')
        self.background_sound.set_volume(0.2)
        self.background_sound.play(loops = -1)
        

    def setup(self, tmx_data, ground_image_path, player):
        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, tmx_data, ground_image_path)

        #house
        for layer in ["HouseFloor", "HouseFurnitureBottom"]:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), surf, self.all_sprites, LAYERS["house bottom"])

        for layer in ["HouseWalls", "HouseFurnitureTop"]:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), surf, self.all_sprites, LAYERS["main"])

        #fence
        try:
            for x, y, surf in tmx_data.get_layer_by_name("Fence").tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), surf, [self.all_sprites, self.collision_sprites])
        except ValueError:
            for x, y, surf in tmx_data.get_layer_by_name("Fences").tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), surf, [self.all_sprites, self.collision_sprites])

        #water
        water_frames = import_folder("graphics/water")
        for x, y, surf in tmx_data.get_layer_by_name("Water").tiles():
            Water((x * TITLE_SIZE, y * TITLE_SIZE), water_frames, self.all_sprites,)
        #trees
        for obj in tmx_data.get_layer_by_name("Trees"):
             Tree(
                 pos = (obj.x, obj.y),
                 surf = obj.image,
                 groups = [self.all_sprites, self.collision_sprites, self.tree_sprites],
                 name = obj.name,
                 player_add = self.player_add)
            

        #wildflowers
        for obj in tmx_data.get_layer_by_name("Decoration"):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        #collision tiles
        try:
            for x, y, surf in tmx_data.get_layer_by_name("Collision").tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), pygame.Surface((TITLE_SIZE, TITLE_SIZE)), self.collision_sprites)
        except ValueError:
            for x, y, surf in tmx_data.get_layer_by_name("Collision2").tiles():
                Generic((x * TITLE_SIZE, y * TITLE_SIZE), pygame.Surface((TITLE_SIZE, TITLE_SIZE)), self.collision_sprites)

        #Player
        if player:
            self.player = player
            self.player.kill()
            self.all_sprites.add(self.player)
            self.player.collision_sprites = self.collision_sprites
            self.player.tree_sprites = self.tree_sprites
            self.player.interaction = self.interaction_sprites
            self.player.soil_layer = self.soil_layer
            for obj in tmx_data.get_layer_by_name("Player"):
                if obj.name == "Start" or obj.name == "Spawn":
                    self.player.pos.x = obj.x
                    self.player.pos.y = obj.y
        else:
            for obj in tmx_data.get_layer_by_name("Player"):
                 if obj.name == "Start" or obj.name == "Spawn":
                    self.player = Player(
                        pos= (obj.x, obj.y), 
                        group = self.all_sprites, 
                        collision_sprites= self.collision_sprites,
                        tree_sprites = self.tree_sprites,
                        interaction = self.interaction_sprites,
                        soil_layer = self.soil_layer,
                        toggle_shop = self.toggle_shop)
                                   
                 if obj.name == "Bed":
                     Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)
    
                 if obj.name == "Trader":
                     Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)
        
    def player_add(self,item):

        self.player.item_inventory[item] += 1
        self.success.play()

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def reset(self):
        # plants
        self.soil_layer.update_plants()

        #soil
        self.soil_layer.remove_water()
        self.raining = randint(0,10) > 7
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        # apples on the trees
        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()

        # sky
        self.sky.start_color = [255,255,255]

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(
                        pos = plant.rect.topleft, 
                        surf = plant.image, 
                        groups = self.all_sprites, 
                        z = LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TITLE_SIZE][plant.rect.centerx // TITLE_SIZE].remove('P')

    def switch_map(self):
        if self.current_map == 'map':
            self.switch_level('map2')
        else:
            self.switch_level('map')


    def run(self,dt):
        # drawing logic
        self.display_surface.fill("black")
        self.all_sprites.custom_draw(self.player)

        # updates
        if self.shop_active:
            self.menu.update()
        else:
            self.all_sprites.update(dt)
            self.plant_collision()
        
        # weather
        self.overlay.display()
        if self.raining and not self.shop_active:
            self.rain.update()
        self.sky.display(dt)

        # transition overlay
        if self.player.sleep:
            self.transition.play()

        if self.player.rect.top < 0:
            self.switch_map()

        #print(self.player.item_inventory)
        #print(self.shop_active)

class CameraGroup(pygame.sprite.Group):
    def __init__(self, ground_sprite):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.ground_sprite = ground_sprite

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        # Clamp the offset to the map boundaries
        self.offset.x = max(0, min(self.offset.x, self.ground_sprite.rect.width - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, self.ground_sprite.rect.height - SCREEN_HEIGHT))

        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)

                    # analytics
                    #if sprite == player:
                    #    pygame.draw.rect(self.display_surface, 'red',offset_rect,4)
                    #    hitbox_rect = player.hitbox.copy()
                    #    hitbox_rect.center = offset_rect.center
                    #    pygame.draw.rect(self.display_surface, 'green', hitbox_rect,5)
                    #    target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
                    #    pygame.draw.circle(self.display_surface,'blue', target_pos,5)

        player.draw_stamina_bar(self.display_surface)
