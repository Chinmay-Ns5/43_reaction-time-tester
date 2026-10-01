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
DARK_BLUE = (25, 35, 65)


class GameEngine:
    """
    Controls the reaction-time game.

    Features:
    - Difficulty selection
    - Multiple rounds
    - False-start detection
    - Reaction-time measurement
    - Results screen
    - Replay
    """

    DIFFICULTIES = {
        "Easy": {
            "rounds": 3,
            "min_wait_ms": 1500,
            "max_wait_ms": 3000,
        },
        "Medium": {
            "rounds": 5,
            "min_wait_ms": 1000,
            "max_wait_ms": 2500,
        },
        "Hard": {
            "rounds": 7,
            "min_wait_ms": 700,
            "max_wait_ms": 1800,
        },
    }

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

        # Default difficulty
        self.difficulty = "Medium"

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        # Game states:
        # menu -> playing -> results
        self.state = "menu"

        self.round = None
        self.reaction_times = []

        self.result_shown_at = None
        self.result_pause_ms = 800

        # Fonts
        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.title_font = pygame.font.SysFont("Arial", 52)
        self.small_font = pygame.font.SysFont("Arial", 22)

    # =========================================================
    # GAME START / REPLAY
    # =========================================================

    def start_game(self, difficulty):
        """
        Start a new game using the selected difficulty.
        """

        config = self.DIFFICULTIES[difficulty]

        self.difficulty = difficulty

        self.rounds_total = config["rounds"]
        self.min_wait_ms = config["min_wait_ms"]
        self.max_wait_ms = config["max_wait_ms"]

        # Clear previous results
        self.reaction_times = []

        # Create first round
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

        self.result_shown_at = None

        self.state = "playing"

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def handle_event(self, event):

        # Quit window
        if event.type == pygame.QUIT:
            return False

        # Menu
        if self.state == "menu":
            self._handle_menu_event(event)

        # Game
        elif self.state == "playing":
            self._handle_game_event(event)

        # Results
        elif self.state == "results":
            self._handle_results_event(event)

        return True

    # =========================================================
    # MENU INPUT
    # =========================================================

    def _handle_menu_event(self, event):

        if event.type != pygame.KEYDOWN:
            return

        # Easy
        if event.key == pygame.K_1:
            self.start_game("Easy")

        # Medium
        elif event.key == pygame.K_2:
            self.start_game("Medium")

        # Hard
        elif event.key == pygame.K_3:
            self.start_game("Hard")

        # Quit
        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
            pygame.quit()
            raise SystemExit

    # =========================================================
    # GAME INPUT
    # =========================================================

    def _handle_game_event(self, event):

        is_click = event.type == pygame.MOUSEBUTTONDOWN

        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        if not (is_click or is_space):
            return

        # Ignore input after round is finished
        if self.round.state in ("result", "false_start"):
            return

        reaction_ms = self.round.register_input()

        # -----------------------------
        # False start
        # -----------------------------

        if reaction_ms is None:
            self.result_shown_at = pygame.time.get_ticks()
            return

        # -----------------------------
        # Valid reaction
        # -----------------------------

        self.reaction_times.append(reaction_ms)

        self.result_shown_at = pygame.time.get_ticks()

    # =========================================================
    # RESULTS INPUT
    # =========================================================

    def _handle_results_event(self, event):

        if event.type != pygame.KEYDOWN:
            return

        # Replay Easy
        if event.key == pygame.K_1:
            self.start_game("Easy")

        # Replay Medium
        elif event.key == pygame.K_2:
            self.start_game("Medium")

        # Replay Hard
        elif event.key == pygame.K_3:
            self.start_game("Hard")

        # Return to difficulty menu
        elif event.key in (pygame.K_r, pygame.K_m):
            self.state = "menu"

        # Quit
        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
            pygame.quit()
            raise SystemExit

    # =========================================================
    # CONTINUOUS INPUT
    # =========================================================

    def handle_input(self):
        """
        Reserved for continuously-held-key input.

        Discrete clicks and key presses are handled
        through handle_event().
        """
        pass

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):

        if self.state != "playing":
            return

        # Update current round
        self.round.update()

        # -----------------------------
        # Valid reaction completed
        # -----------------------------

        if self.round.state == "result":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and now - self.result_shown_at
                >= self.result_pause_ms
            ):
                self._start_next_round()

        # -----------------------------
        # False start
        # -----------------------------

        elif self.round.state == "false_start":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and now - self.result_shown_at
                >= self.result_pause_ms
            ):
                self.round = Round(
                    self.min_wait_ms,
                    self.max_wait_ms
                )

    # =========================================================
    # START NEXT ROUND
    # =========================================================

    def _start_next_round(self):

        # All required valid rounds completed
        if len(self.reaction_times) >= self.rounds_total:

            self.state = "results"

            return

        # Start another round
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # =========================================================
    # STATISTICS
    # =========================================================

    def average_reaction_ms(self):

        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times)
            / len(self.reaction_times)
        )

    def best_reaction_ms(self):

        if not self.reaction_times:
            return 0

        return min(self.reaction_times)

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, screen):

        if self.state == "menu":
            self._render_menu(screen)

        elif self.state == "playing":
            self._render_game(screen)

        elif self.state == "results":
            self._render_game_over(screen)

    # =========================================================
    # MENU SCREEN
    # =========================================================

    def _render_menu(self, screen):

        screen.fill(DARK_BLUE)

        # Title
        title = self.title_font.render(
            "REACTION TIME TESTER",
            True,
            WHITE
        )

        title_rect = title.get_rect(
            center=(self.width // 2, 65)
        )

        screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.font.render(
            "Choose Difficulty",
            True,
            WHITE
        )

        subtitle_rect = subtitle.get_rect(
            center=(self.width // 2, 125)
        )

        screen.blit(subtitle, subtitle_rect)

        # Difficulty options
        options = [
            (
                "1",
                "Easy",
                "3 rounds | 1.5 - 3.0 sec"
            ),
            (
                "2",
                "Medium",
                "5 rounds | 1.0 - 2.5 sec"
            ),
            (
                "3",
                "Hard",
                "7 rounds | 0.7 - 1.8 sec"
            ),
        ]

        start_y = 190

        for index, (key, name, description) in enumerate(options):

            y = start_y + index * 65

            option_text = self.font.render(
                f"[{key}] {name}",
                True,
                GREEN if name == self.difficulty else WHITE
            )

            option_rect = option_text.get_rect(
                center=(self.width // 2, y)
            )

            screen.blit(
                option_text,
                option_rect
            )

            description_text = self.small_font.render(
                description,
                True,
                WHITE
            )

            description_rect = description_text.get_rect(
                center=(self.width // 2, y + 28)
            )

            screen.blit(
                description_text,
                description_rect
            )

        # Instructions
        instructions = self.small_font.render(
            "Press 1, 2 or 3 to start | Q to quit",
            True,
            WHITE
        )

        instructions_rect = instructions.get_rect(
            center=(self.width // 2, self.height - 30)
        )

        screen.blit(
            instructions,
            instructions_rect
        )

    # =========================================================
    # GAME SCREEN
    # =========================================================

    def _render_game(self, screen):

        # Waiting
        if self.round.state == "waiting":

            bg = GRAY
            message = "Wait for green..."

        # GO
        elif self.round.state == "go":

            bg = GREEN
            message = "Click now!"

        # False start
        elif self.round.state == "false_start":

            bg = ORANGE
            message = "FALSE START!"

        # Result
        else:

            bg = BLUE
            message = f"{self.round.reaction_ms} ms"

        screen.fill(bg)

        # Main message
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

        # Round number
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

        # Average
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

        # Difficulty
        difficulty_text = self.small_font.render(
            self.difficulty,
            True,
            WHITE
        )

        screen.blit(
            difficulty_text,
            (
                10,
                self.height - 30
            )
        )

    # =========================================================
    # GAME OVER SCREEN
    # =========================================================

    def _render_game_over(self, screen):

        screen.fill(BLACK)

        # Title
        title = self.big_font.render(
            "GAME COMPLETE!",
            True,
            WHITE
        )

        title_rect = title.get_rect(
            center=(self.width // 2, 45)
        )

        screen.blit(
            title,
            title_rect
        )

        # Difficulty
        difficulty_text = self.font.render(
            f"{self.difficulty} Mode",
            True,
            GREEN
        )

        difficulty_rect = difficulty_text.get_rect(
            center=(self.width // 2, 90)
        )

        screen.blit(
            difficulty_text,
            difficulty_rect
        )

        # Individual results
        start_y = 125
        line_spacing = 30

        for index, reaction_time in enumerate(
            self.reaction_times,
            start=1
        ):

            result_text = self.small_font.render(
                f"Round {index}: {reaction_time} ms",
                True,
                WHITE
            )

            result_rect = result_text.get_rect(
                center=(
                    self.width // 2,
                    start_y + (index - 1) * line_spacing
                )
            )

            screen.blit(
                result_text,
                result_rect
            )

        # Average
        average_y = (
            start_y
            + self.rounds_total * line_spacing
            + 10
        )

        average_text = self.font.render(
            f"Average: {self.average_reaction_ms()} ms",
            True,
            GREEN
        )

        average_rect = average_text.get_rect(
            center=(
                self.width // 2,
                average_y
            )
        )

        screen.blit(
            average_text,
            average_rect
        )

        # Replay instructions
        replay_text = self.small_font.render(
            "1 = Easy   2 = Medium   3 = Hard",
            True,
            WHITE
        )

        replay_rect = replay_text.get_rect(
            center=(
                self.width // 2,
                self.height - 55
            )
        )

        screen.blit(
            replay_text,
            replay_rect
        )

        # Menu / quit instructions
        menu_text = self.small_font.render(
            "R = Difficulty Menu   Q = Quit",
            True,
            WHITE
        )

        menu_rect = menu_text.get_rect(
            center=(
                self.width // 2,
                self.height - 25
            )
        )

        screen.blit(
            menu_text,
            menu_rect
        )