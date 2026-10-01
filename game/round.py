import random
import pygame


class Round:
    def __init__(self, min_wait_ms=1000, max_wait_ms=3000):
        self.wait_delay_ms = random.randint(
            min_wait_ms,
            max_wait_ms
        )

        self.state = "waiting"
        # waiting -> go -> result
        # waiting -> false_start

        self.start_time = pygame.time.get_ticks()
        self.go_time = None
        self.reaction_ms = None

    def update(self):
        if self.state == "waiting":

            now = pygame.time.get_ticks()

            if now - self.start_time >= self.wait_delay_ms:

                self.state = "go"

                # IMPORTANT:
                # Record the exact moment the screen
                # changes to green.
                self.go_time = now

    def register_input(self):
        """
        Register player input.

        Returns:
            reaction time in milliseconds for a valid reaction
            None for a false start
        """

        now = pygame.time.get_ticks()

        # ----------------------------------
        # Clicked before green
        # ----------------------------------

        if self.state == "waiting":

            self.state = "false_start"

            return None

        # ----------------------------------
        # Ignore input outside GO state
        # ----------------------------------

        if self.state != "go":
            return None

        # ----------------------------------
        # Valid reaction
        # ----------------------------------

        self.reaction_ms = now - self.go_time

        self.state = "result"

        return self.reaction_ms