import pygame
from .round import Round


# -----------------------------
# Colors
# -----------------------------

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)
ORANGE = (210, 120, 40)


class GameEngine:
    def __init__(
        self,
        width,
        height,
        rounds_total=5,
        min_wait_ms=1000,
        max_wait_ms=3000
    ):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        # Current round
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

        # Stores only valid reaction times
        self.reaction_times = []

        # Used to pause briefly after a result/false start
        self.result_shown_at = None
        self.result_pause_ms = 800

        # Fonts
        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)

        # Game completion
        self.game_over = False

    # -----------------------------
    # Event handling
    # -----------------------------

    def handle_event(self, event):
        """
        Handle mouse clicks and SPACE key presses.
        """

        if self.game_over:
            return

        is_click = event.type == pygame.MOUSEBUTTONDOWN

        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        # Ignore unrelated events
        if not (is_click or is_space):
            return

        # Ignore input after a round has already finished
        if self.round.state in ("result", "false_start"):
            return

        # Register the player's input
        reaction_ms = self.round.register_input()

        # ----------------------------------
        # False start
        # ----------------------------------

        if reaction_ms is None:
            self.result_shown_at = pygame.time.get_ticks()
            return

        # ----------------------------------
        # Valid reaction
        # ----------------------------------

        self.reaction_times.append(reaction_ms)

        self.result_shown_at = pygame.time.get_ticks()

    # -----------------------------
    # Continuous input
    # -----------------------------

    def handle_input(self):
        """
        Reserved for continuously-held-key input.

        Player actions are handled as discrete
        events in handle_event().
        """
        pass

    # -----------------------------
    # Game update
    # -----------------------------

    def update(self):
        """
        Update the current round and move to
        the next round when necessary.
        """

        if self.game_over:
            return

        # Update the current round.
        self.round.update()

        # ----------------------------------
        # Valid reaction completed
        # ----------------------------------

        if self.round.state == "result":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and now - self.result_shown_at
                >= self.result_pause_ms
            ):
                self._start_next_round()

        # ----------------------------------
        # False start
        # ----------------------------------

        elif self.round.state == "false_start":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and now - self.result_shown_at
                >= self.result_pause_ms
            ):
                # Restart another round.
                self.round = Round(
                    self.min_wait_ms,
                    self.max_wait_ms
                )

    # -----------------------------
    # Start next round
    # -----------------------------

    def _start_next_round(self):
        """
        Start another round or finish the game
        after all required valid reactions.
        """

        # All valid rounds are complete.
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            return

        # Start a fresh round.
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # -----------------------------
    # Statistics
    # -----------------------------

    def average_reaction_ms(self):
        """
        Return the average of valid reaction times.
        """

        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times)
            / len(self.reaction_times)
        )

    # -----------------------------
    # Rendering
    # -----------------------------

    def render(self, screen):
        """
        Draw the current game state.
        """

        # ----------------------------------
        # Waiting state
        # ----------------------------------

        if self.round.state == "waiting":

            bg = GRAY
            message = "Wait for green..."

        # ----------------------------------
        # GO state
        # ----------------------------------

        elif self.round.state == "go":

            bg = GREEN
            message = "Click now!"

        # ----------------------------------
        # False start state
        # ----------------------------------

        elif self.round.state == "false_start":

            bg = ORANGE
            message = "FALSE START!"

        # ----------------------------------
        # Result state
        # ----------------------------------

        else:

            bg = BLUE
            message = f"{self.round.reaction_ms} ms"

        # Draw background
        screen.fill(bg)

        # Draw main message
        text_surf = self.big_font.render(
            message,
            True,
            WHITE
        )

        text_rect = text_surf.get_rect(
            center=(
                self.width // 2,
                self.height // 2
            )
        )

        screen.blit(
            text_surf,
            text_rect
        )

        # ----------------------------------
        # Round counter
        # ----------------------------------

        round_num = min(
            len(self.reaction_times) + 1,
            self.rounds_total
        )

        round_text = self.font.render(
            f"Round {round_num}/{self.rounds_total}",
            True,
            WHITE
        )

        screen.blit(
            round_text,
            (10, 10)
        )

        # ----------------------------------
        # Average reaction time
        # ----------------------------------

        avg_text = self.font.render(
            f"Avg: {self.average_reaction_ms()} ms",
            True,
            WHITE
        )

        screen.blit(
            avg_text,
            (
                self.width - avg_text.get_width() - 10,
                10
            )
        )

        # ----------------------------------
        # Game-over terminal output
        # ----------------------------------

        if (
            self.game_over
            and not getattr(
                self,
                "_game_over_logged",
                False
            )
        ):

            print(
                "Session complete! "
                "Reaction times (ms):",
                self.reaction_times
            )

            print(
                "Average:",
                self.average_reaction_ms(),
                "ms"
            )

            self._game_over_logged = True