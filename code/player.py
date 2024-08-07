import pygame
from Settings import *
from Support import *
from Timer import Timer

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer, toggle_shop):
        super().__init__(group)

        self.import_assets()
        self.status = "down_idle"
        self.frame_index = 0
        
        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS["main"]

        #movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200
        self.stamina = 100
        self.stamina_cooldown = 0

        self.stamina_bar_width = 200  
        self.stamina_bar_height = 10  
        self.stamina_bar_color_full = GREEN  
        self.stamina_bar_color_empty = BLACK  

        #collision
        self.collision_sprites = collision_sprites
        self.hitbox = self.rect.copy().inflate((-126,-70))
        #timers
        self.timers = {
            "tool use": Timer(350,self.use_tool),
            "tool switch": Timer(200),
            "seed use": Timer(350, self.use_seed),
            "seed switch": Timer(200)
        }

        #tools
        self.tools = ["hoe","axe","water"]
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        #seeds
        self.seeds = ["corn", "tomato"]
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        #inventory
        self.item_inventory = {
            'wood':   0,
            'apple':  0,
            'corn':   0,
            'tomato': 0, 
        }
        self.seed_inventory = {
        'corn': 5,
        'tomato': 5
        }
        self.money = 200

        #intercation
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop

        # sound
        self.watering = pygame.mixer.Sound('audio/water.mp3')
        self.watering.set_volume(0.2)

    def draw_stamina_bar(self, screen):
        # Calculate width of the stamina bar based on current stamina
        current_stamina_width = int((self.stamina / 100) * self.stamina_bar_width)
        # Create the stamina bar rectangle
        stamina_bar_rect = pygame.Rect(540, 700, self.stamina_bar_width, self.stamina_bar_height)
        # Create a smaller rectangle representing current stamina
        current_stamina_rect = pygame.Rect(stamina_bar_rect.x, stamina_bar_rect.y,current_stamina_width, stamina_bar_rect.height)
        # Draw the empty stamina bar
        pygame.draw.rect(screen, self.stamina_bar_color_empty, stamina_bar_rect)
        # Draw the current stamina bar
        pygame.draw.rect(screen, self.stamina_bar_color_full, current_stamina_rect)

    def get_target_pos(self):
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def use_tool(self):
        if self.selected_tool == "hoe":
            self.soil_layer.get_hit(self.target_pos)
            
        if self.selected_tool == "axe":
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()

        if self.selected_tool == "water":
            self.soil_layer.water(self.target_pos)
            self.watering.play()

    def use_seed(self):
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1

    def import_assets(self):    
        self.animations = {'up': [],'down': [],'left': [],'right': [],
			                'right_idle':[],'left_idle':[],'up_idle':[],'down_idle':[],
			                'right_hoe':[],'left_hoe':[],'up_hoe':[],'down_hoe':[],
			                'right_axe':[],'left_axe':[],'up_axe':[],'down_axe':[],
			                'right_water':[],'left_water':[],'up_water':[],'down_water':[]}

        for animation in self.animations.keys():
            full_path = './/graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)


    def animate(self,dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    def input(self, dt):
        keys = pygame.key.get_pressed()

        # Directions
        if not self.timers["tool use"].active and not self.sleep:
            if self.stamina_cooldown > 0:
                self.stamina_cooldown -= dt
            # Sprint & Stamina logic
            if keys[pygame.K_LSHIFT] and self.stamina > 0 and self.stamina_cooldown <= 0:
                self.speed = 500
                self.stamina -= 0.1
                if self.stamina <= 0:
                    self.stamina = 0
                    self.stamina_cooldown = 5
            else:
                self.speed = 200
                if self.stamina < 100 and self.stamina_cooldown <= 0:
                    self.stamina += 0.1

        # Movement directions
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
            self.status = "up"
            
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
            self.status = "down"
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
            self.status = "right"
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
            self.status = "left"
        else:
            self.direction.x = 0

        # Tool use
        if keys[pygame.K_SPACE]:
            self.timers["tool use"].activate()
            self.direction = pygame.math.Vector2()
            self.frame_index = 0

        # Change tool
        if keys[pygame.K_q] and not self.timers["tool switch"].active:
            self.timers["tool switch"].activate()
            self.tool_index += 1
            self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
            self.selected_tool = self.tools[self.tool_index]

        # Seed use
        if keys[pygame.K_LCTRL]:
            self.timers["seed use"].activate()
            self.direction = pygame.math.Vector2()
            self.frame_index = 0

        # Seed change
        if keys[pygame.K_e] and not self.timers["seed switch"].active:
            self.timers["seed switch"].activate()
            self.seed_index += 1
            self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
            self.selected_seed = self.seeds[self.seed_index]

        # Interaction
        if keys[pygame.K_RETURN]:
            collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
            if collided_interaction_sprite:
                if collided_interaction_sprite[0].name == 'Trader':
                    self.toggle_shop()
                else:
                    self.status = 'left_idle'
                    self.sleep = True        



    def get_status(self):
        # if the player is not moving so IDLE:
        if self.direction.magnitude() == 0:
        #add _idle to the status
            self.status = self.status.split("_")[0] + "_idle"

        #tool use
        if self.timers["tool use"].active:
            self.status = self.status.split("_")[0] + "_" + self.selected_tool

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, "hitbox"):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == "horizontal":
                        if self.direction.x > 0: #moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0: #moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == "vertical":
                        if self.direction.y > 0: #moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0: #moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery
        
    def move(self,dt):

        #normalizing a vecto
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()
        
        #horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision("horizontal")
        #vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision("vertical")

    def update(self, dt):
        self.input(dt)
        self.get_status()
        self.update_timers()
        self.get_target_pos()

        self.move(dt)
        self.animate(dt)