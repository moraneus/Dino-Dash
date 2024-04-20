import pygame
import random
import os
from typing import List

# Initialize Pygame
pygame.init()

# Set up the game window
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600

# Dino params
DINO_START_X = 50
DINO_START_Y_OFFSET = 10
DINO_JUMP_SPEED = -15
DINO_GRAVITY = 0.8

# Obstacle params
INITIAL_OBSTACLE_SPEED = 5
SPEED_INCREASE_FACTOR = 1.05
OBSTACLE_SPAWN_DELAY_MIN = 50
OBSTACLE_SPAWN_DELAY_MAX = 150

# Background details
BACKGROUND_TRANSITION_SPEED = 5
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Dinosaur(pygame.sprite.Sprite):
    """A class to represent the dinosaur character."""

    def __init__(self, images: List[pygame.Surface]):
        """Initialize the dinosaur."""
        super().__init__()
        self.images = images
        self.image = images[0]  # Set the initial image
        self.rect = self.image.get_rect()
        self.rect.x = DINO_START_X
        self.rect.y = SCREEN_HEIGHT - self.rect.height - DINO_START_Y_OFFSET
        self.jump_speed = 0
        self.frame = 0
        self.frame_count = 0

    def update(self):
        """Update the dinosaur's position and handle jumping."""
        self.jump_speed += DINO_GRAVITY
        self.rect.y += self.jump_speed

        # Keep the dinosaur on the ground
        if self.rect.y > SCREEN_HEIGHT - self.rect.height - DINO_START_Y_OFFSET:
            self.rect.y = SCREEN_HEIGHT - self.rect.height - DINO_START_Y_OFFSET
            self.jump_speed = 0

        # Update the animation frame
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            self.frame = (self.frame + 1) % len(self.images)
        self.image = self.images[self.frame]

    def jump(self):
        """Make the dinosaur jump."""
        if self.rect.y == SCREEN_HEIGHT - self.rect.height - DINO_START_Y_OFFSET:
            self.jump_speed = DINO_JUMP_SPEED


class Obstacle(pygame.sprite.Sprite):
    """A class to represent an obstacle."""

    def __init__(self, image: pygame.Surface, speed: int):
        """Initialize the obstacle."""
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = SCREEN_HEIGHT - self.rect.height
        self.speed = speed
        self.passed = False

    def update(self):
        """Update the obstacle's position."""
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


class Background:
    """A class to represent the scrolling background."""

    def __init__(self, images: List[pygame.Surface]):
        """Initialize the background."""
        self.images = images
        self.current_image = random.choice(self.images)
        self.next_image = None
        self.x = 0
        self.transition_alpha = 0
        self.changed = False

    def update(self, score: int):
        """Update the background and handle transitions."""
        # Check if it's time to change the background
        if score > 0 and score % 10 == 0 and not self.changed:
            self.next_image = random.choice([image for image in self.images if image != self.current_image])
            self.transition_alpha = 0
            self.changed = True

        # Update the background transition
        if self.next_image is not None:
            self.transition_alpha += BACKGROUND_TRANSITION_SPEED
            if self.transition_alpha >= 255:
                self.current_image = self.next_image
                self.next_image = None
                self.changed = False

        # Scroll the background
        self.x -= 2
        if self.x <= -self.current_image.get_width():
            self.x = 0

    def draw(self, screen: pygame.Surface):
        """Draw the background on the screen."""
        screen.blit(self.current_image, (self.x, 0))
        screen.blit(self.current_image, (self.x + self.current_image.get_width(), 0))
        if self.next_image is not None:
            self.next_image.set_alpha(self.transition_alpha)
            screen.blit(self.next_image, (self.x, 0))
            screen.blit(self.next_image, (self.x + self.next_image.get_width(), 0))


class Game:
    """A class to handle the game loop and manage game objects."""

    def __init__(self):
        """Initialize the game."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dino Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.score = 0
        self.obstacle_speed = INITIAL_OBSTACLE_SPEED
        self.obstacle_spawn_timer = 0

        # Load and scale the dinosaur images
        dino_files = [file for file in os.listdir("dino") if file.endswith(".png")]
        dino_images = [
            pygame.transform.scale(
                pygame.image.load(os.path.join("dino", file)), (40, 60)) for file in dino_files
        ]
        self.dinosaur = Dinosaur(dino_images)

        # Load obstacle images
        obstacle_files = [file for file in os.listdir("obstacles") if file.endswith(".png")]
        self.obstacle_images = [pygame.image.load(os.path.join("obstacles", file)) for file in obstacle_files]

        # Load background images
        background_files = [
            file for file in os.listdir("backgrounds") if file.endswith((".jpg", ".png"))
        ]
        background_images = [pygame.image.load(os.path.join("backgrounds", file)) for file in background_files]
        self.background = Background(background_images)

        self.obstacles = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group(self.dinosaur)

    def spawn_obstacles(self):
        """Spawn obstacles at random intervals."""
        if self.obstacle_spawn_timer <= 0 and self.obstacle_images:
            obstacle_image = random.choice(self.obstacle_images)
            obstacle_width, obstacle_height = random.randint(20, 50), random.randint(30, 90)
            obstacle_image = pygame.transform.scale(obstacle_image, (obstacle_width, obstacle_height))
            obstacle = Obstacle(obstacle_image, self.obstacle_speed)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)
            self.obstacle_spawn_timer = random.randint(OBSTACLE_SPAWN_DELAY_MIN, OBSTACLE_SPAWN_DELAY_MAX)

        self.obstacle_spawn_timer -= 1

    def update_score(self):
        """Update the score and increase obstacle speed."""
        for obstacle in self.obstacles:
            if self.dinosaur.rect.right > obstacle.rect.right and not obstacle.passed:
                self.score += 1
                obstacle.passed = True

        # Update obstacle speed based on score
        if self.score > 0 and self.score % 10 == 0:
            self.obstacle_speed = INITIAL_OBSTACLE_SPEED * (SPEED_INCREASE_FACTOR ** (self.score // 10))

    def check_collisions(self) -> bool:
        """Check for collisions between the dinosaur and obstacles."""
        return bool(pygame.sprite.spritecollide(self.dinosaur, self.obstacles, dokill=False))

    def game_over_screen(self) -> bool:
        """Display the game over screen and handle user input."""
        game_over_text = self.font.render("GAME OVER", True, BLACK)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))

        continue_text = self.font.render("Press 'C' to Continue or 'Q' to Quit", True, BLACK)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        self.reset_game()
                        return True
                    elif event.key == pygame.K_q:
                        return False

            self.screen.fill(WHITE)
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(continue_text, continue_rect)
            pygame.display.flip()

    def reset_game(self):
        """Reset the game to its initial state."""
        self.score = 0
        self.obstacle_speed = INITIAL_OBSTACLE_SPEED
        self.obstacle_spawn_timer = 0

        self.dinosaur.rect.x = DINO_START_X
        self.dinosaur.rect.y = SCREEN_HEIGHT - self.dinosaur.rect.height - DINO_START_Y_OFFSET
        self.dinosaur.jump_speed = 0
        self.dinosaur.frame = 0
        self.dinosaur.frame_count = 0

        self.obstacles.empty()
        self.all_sprites.empty()
        self.all_sprites.add(self.dinosaur)

        self.background.current_image = random.choice(self.background.images)
        self.background.next_image = None
        self.background.x = 0
        self.background.transition_alpha = 0

    def run(self):
        """Run the game loop."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.dinosaur.jump()

            self.screen.fill(WHITE)
            self.background.update(self.score)
            self.background.draw(self.screen)

            self.spawn_obstacles()
            self.all_sprites.update()
            self.update_score()

            if self.check_collisions():
                if not self.game_over_screen():
                    break

            self.all_sprites.draw(self.screen)
            score_text = self.font.render(f"Score: {self.score}", True, BLACK)
            self.screen.blit(score_text, (10, 10))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()