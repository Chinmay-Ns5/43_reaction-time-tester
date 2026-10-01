import math
from array import array

import pygame

from .round import Round


# =========================================================
# COLORS
# =========================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)

ORANGE = (210, 120, 40)
DARK_BLUE = (25, 35, 65)


class GameEngine:

    # =====================================================
    # DIFFICULTY SETTINGS
    # =====================================================

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

    # =====================================================
    # INITIALIZATION
    # =====================================================

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

        # =================================================
        # FONTS
        # =================================================

        self.font = pygame.font.SysFont(
            "Arial",
            30
        )

        self.big_font = pygame.font.SysFont(
            "Arial",
            46
        )

        self.title_font = pygame.font.SysFont(
            "Arial",
            46
        )

        self.small_font = pygame.font.SysFont(
            "Arial",
            22
        )

        self.result_font = pygame.font.SysFont(
            "Arial",
            26
        )

        # Sound setup
        self._initialize_sound()

    # =====================================================
    # SOUND INITIALIZATION
    # =====================================================

    def _initialize_sound(self):

        self.sound_enabled = False

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init(
                    frequency=44100,
                    size=-16,
                    channels=1,
                    buffer=512
                )

            # Green / GO sound
            self.go_sound = self._create_tone(
                frequency=900,
                duration_ms=150,
                volume=0.5
            )

            # False start sound
            self.false_start_sound = self._create_tone(
                frequency=250,
                duration_ms=300,
                volume=0.5
            )

            # Game completion sound
            self.session_end_sound = (
                self._create_completion_sound()
            )

            self.sound_enabled = True

        except pygame.error:

            self.sound_enabled = False

    # =====================================================
    # CREATE SIMPLE TONE
    # =====================================================

    def _create_tone(
        self,
        frequency,
        duration_ms,
        volume=0.5
    ):

        sample_rate = 44100

        sample_count = int(
            sample_rate * duration_ms / 1000
        )

        samples = array("h")

        amplitude = int(
            32767 * volume
        )

        for i in range(sample_count):

            value = int(
                amplitude
                * math.sin(
                    2
                    * math.pi
                    * frequency
                    * i
                    / sample_rate
                )
            )

            samples.append(value)

        return pygame.mixer.Sound(
            buffer=samples.tobytes()
        )

    # =====================================================
    # CREATE COMPLETION SOUND
    # =====================================================

    def _create_completion_sound(self):

        sample_rate = 44100

        frequencies = [600, 800]

        tone_duration_ms = 180
        gap_ms = 50

        samples = array("h")

        amplitude = int(
            32767 * 0.5
        )

        for frequency in frequencies:

            sample_count = int(
                sample_rate
                * tone_duration_ms
                / 1000
            )

            for i in range(sample_count):

                value = int(
                    amplitude
                    * math.sin(
                        2
                        * math.pi
                        * frequency
                        * i
                        / sample_rate
                    )
                )

                samples.append(value)

            gap_samples = int(
                sample_rate
                * gap_ms
                / 1000
            )

            samples.extend(
                [0] * gap_samples
            )

        return pygame.mixer.Sound(
            buffer=samples.tobytes()
        )

    # =====================================================
    # PLAY SOUND
    # =====================================================

    def _play_sound(self, sound):

        if not self.sound_enabled:
            return

        try:

            sound.play()

        except pygame.error:

            pass

    # =====================================================
    # START GAME
    # =====================================================

    def start_game(self, difficulty):

        config = self.DIFFICULTIES[difficulty]

        self.difficulty = difficulty

        self.rounds_total = config["rounds"]

        self.min_wait_ms = config["min_wait_ms"]

        self.max_wait_ms = config["max_wait_ms"]

        # Clear previous results
        self.reaction_times = []

        # Start first round
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

        self.result_shown_at = None

        self.state = "playing"

    # =====================================================
    # EVENT HANDLING
    # =====================================================

    def handle_event(self, event):

        if event.type == pygame.QUIT:

            return False

        if self.state == "menu":

            self._handle_menu_event(event)

        elif self.state == "playing":

            self._handle_game_event(event)

        elif self.state == "results":

            self._handle_results_event(event)

        return True

    # =====================================================
    # MENU INPUT
    # =====================================================

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
        elif event.key in (
            pygame.K_q,
            pygame.K_ESCAPE
        ):

            pygame.quit()

            raise SystemExit

    # =====================================================
    # GAME INPUT
    # =====================================================

    def _handle_game_event(self, event):

        is_click = (
            event.type == pygame.MOUSEBUTTONDOWN
        )

        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        if not (is_click or is_space):
            return

        # Ignore input while showing result
        if self.round.state in (
            "result",
            "false_start"
        ):
            return

        reaction_ms = self.round.register_input()

        # =================================================
        # FALSE START
        # =================================================

        if reaction_ms is None:

            self._play_sound(
                self.false_start_sound
            )

            self.result_shown_at = (
                pygame.time.get_ticks()
            )

            return

        # =================================================
        # VALID REACTION
        # =================================================

        self.reaction_times.append(
            reaction_ms
        )

        self.result_shown_at = (
            pygame.time.get_ticks()
        )

    # =====================================================
    # RESULTS SCREEN INPUT
    # =====================================================

    def _handle_results_event(self, event):

        if event.type != pygame.KEYDOWN:
            return

        # Play Easy again
        if event.key == pygame.K_1:

            self.start_game("Easy")

        # Play Medium again
        elif event.key == pygame.K_2:

            self.start_game("Medium")

        # Play Hard again
        elif event.key == pygame.K_3:

            self.start_game("Hard")

        # Difficulty menu
        elif event.key in (
            pygame.K_r,
            pygame.K_m
        ):

            self.state = "menu"

        # Quit
        elif event.key in (
            pygame.K_q,
            pygame.K_ESCAPE
        ):

            pygame.quit()

            raise SystemExit

    # =====================================================
    # CONTINUOUS INPUT
    # =====================================================

    def handle_input(self):
        pass

    # =====================================================
    # UPDATE GAME
    # =====================================================

    def update(self):

        if self.state != "playing":
            return

        previous_state = self.round.state

        self.round.update()

        # =================================================
        # GO SOUND
        # =================================================

        if (
            previous_state == "waiting"
            and self.round.state == "go"
        ):

            self._play_sound(
                self.go_sound
            )

        # =================================================
        # VALID RESULT
        # =================================================

        if self.round.state == "result":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and
                now - self.result_shown_at
                >= self.result_pause_ms
            ):

                self._start_next_round()

        # =================================================
        # FALSE START
        # =================================================

        elif self.round.state == "false_start":

            now = pygame.time.get_ticks()

            if (
                self.result_shown_at is not None
                and
                now - self.result_shown_at
                >= self.result_pause_ms
            ):

                self.round = Round(
                    self.min_wait_ms,
                    self.max_wait_ms
                )

    # =====================================================
    # START NEXT ROUND
    # =====================================================

    def _start_next_round(self):

        if (
            len(self.reaction_times)
            >= self.rounds_total
        ):

            self.state = "results"

            self._play_sound(
                self.session_end_sound
            )

            return

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # =====================================================
    # CALCULATE AVERAGE
    # =====================================================

    def average_reaction_ms(self):

        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times)
            / len(self.reaction_times)
        )

    # =====================================================
    # RENDER
    # =====================================================

    def render(self, screen):

        if self.state == "menu":

            self._render_menu(screen)

        elif self.state == "playing":

            self._render_game(screen)

        elif self.state == "results":

            self._render_game_over(screen)

    # =====================================================
    # MENU SCREEN
    # =====================================================

    def _render_menu(self, screen):

        screen.fill(DARK_BLUE)

        title = self.title_font.render(
            "REACTION TIME TESTER",
            True,
            WHITE
        )

        title_rect = title.get_rect(
            center=(
                self.width // 2,
                65
            )
        )

        screen.blit(
            title,
            title_rect
        )

        subtitle = self.font.render(
            "Choose Difficulty",
            True,
            WHITE
        )

        subtitle_rect = subtitle.get_rect(
            center=(
                self.width // 2,
                125
            )
        )

        screen.blit(
            subtitle,
            subtitle_rect
        )

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

        for index, (
            key,
            name,
            description
        ) in enumerate(options):

            y = start_y + index * 65

            option_text = self.font.render(
                f"[{key}] {name}",
                True,
                (
                    GREEN
                    if name == self.difficulty
                    else WHITE
                )
            )

            option_rect = option_text.get_rect(
                center=(
                    self.width // 2,
                    y
                )
            )

            screen.blit(
                option_text,
                option_rect
            )

            description_text = (
                self.small_font.render(
                    description,
                    True,
                    WHITE
                )
            )

            description_rect = (
                description_text.get_rect(
                    center=(
                        self.width // 2,
                        y + 28
                    )
                )
            )

            screen.blit(
                description_text,
                description_rect
            )

        instructions = self.small_font.render(
            "Press 1, 2 or 3 to start | Q to quit",
            True,
            WHITE
        )

        instructions_rect = instructions.get_rect(
            center=(
                self.width // 2,
                self.height - 30
            )
        )

        screen.blit(
            instructions,
            instructions_rect
        )

    # =====================================================
    # GAME SCREEN
    # =====================================================

    def _render_game(self, screen):

        if self.round.state == "waiting":

            bg = GRAY

            message = "Wait for green..."

        elif self.round.state == "go":

            bg = GREEN

            message = "Click now!"

        elif self.round.state == "false_start":

            bg = ORANGE

            message = "FALSE START!"

        else:

            bg = BLUE

            message = (
                f"{self.round.reaction_ms} ms"
            )

        screen.fill(bg)

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

        # Round counter
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

        # Running average
        avg_text = self.font.render(
            f"Avg: {self.average_reaction_ms()} ms",
            True,
            WHITE
        )

        screen.blit(
            avg_text,
            (
                self.width
                - avg_text.get_width()
                - 10,
                10
            )
        )

        # Difficulty
        difficulty_text = (
            self.small_font.render(
                self.difficulty,
                True,
                WHITE
            )
        )

        screen.blit(
            difficulty_text,
            (
                10,
                self.height - 30
            )
        )

    # =====================================================
    # FINAL RESULTS SCREEN
    # =====================================================

    def _render_game_over(self, screen):

        screen.fill(BLACK)

        # =================================================
        # TITLE
        # =================================================

        title = self.title_font.render(
            "GAME COMPLETE!",
            True,
            WHITE
        )

        title_rect = title.get_rect(
            center=(
                self.width // 2,
                55
            )
        )

        screen.blit(
            title,
            title_rect
        )

        # =================================================
        # DIFFICULTY
        # =================================================

        difficulty_text = self.font.render(
            f"{self.difficulty} Mode",
            True,
            GREEN
        )

        difficulty_rect = difficulty_text.get_rect(
            center=(
                self.width // 2,
                105
            )
        )

        screen.blit(
            difficulty_text,
            difficulty_rect
        )

        # =================================================
        # RESULT SETTINGS
        # =================================================

        row_start_y = 165

        row_spacing = 34

        # =================================================
        # HARD MODE
        # =================================================

        if self.rounds_total >= 7:

            left_results = (
                self.reaction_times[:4]
            )

            right_results = (
                self.reaction_times[4:]
            )

            left_x = self.width // 4

            right_x = (
                self.width * 3
            ) // 4

            # ---------------------------------------------
            # LEFT COLUMN
            # ---------------------------------------------

            for index, reaction_time in enumerate(
                left_results,
                start=1
            ):

                result_text = (
                    self.result_font.render(
                        f"Round {index}: "
                        f"{reaction_time} ms",
                        True,
                        WHITE
                    )
                )

                result_rect = (
                    result_text.get_rect(
                        center=(
                            left_x,
                            row_start_y
                            + (index - 1)
                            * row_spacing
                        )
                    )
                )

                screen.blit(
                    result_text,
                    result_rect
                )

            # ---------------------------------------------
            # RIGHT COLUMN
            # ---------------------------------------------

            for index, reaction_time in enumerate(
                right_results,
                start=5
            ):

                result_text = (
                    self.result_font.render(
                        f"Round {index}: "
                        f"{reaction_time} ms",
                        True,
                        WHITE
                    )
                )

                result_rect = (
                    result_text.get_rect(
                        center=(
                            right_x,
                            row_start_y
                            + (index - 5)
                            * row_spacing
                        )
                    )
                )

                screen.blit(
                    result_text,
                    result_rect
                )

            last_result_y = (
                row_start_y
                + 3 * row_spacing
            )

        # =================================================
        # EASY / MEDIUM
        # =================================================

        else:

            for index, reaction_time in enumerate(
                self.reaction_times,
                start=1
            ):

                result_text = (
                    self.result_font.render(
                        f"Round {index}: "
                        f"{reaction_time} ms",
                        True,
                        WHITE
                    )
                )

                result_rect = (
                    result_text.get_rect(
                        center=(
                            self.width // 2,
                            row_start_y
                            + (index - 1)
                            * row_spacing
                        )
                    )
                )

                screen.blit(
                    result_text,
                    result_rect
                )

            last_result_y = (
                row_start_y
                + (self.rounds_total - 1)
                * row_spacing
            )

        # =================================================
        # AVERAGE
        # =================================================

        # Average sits directly below the result section.
        average_y = (
            last_result_y + 48
        )

        average_text = self.font.render(
            f"Average: "
            f"{self.average_reaction_ms()} ms",
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

        # =================================================
        # SMALL BOTTOM CONTROLS
        # =================================================

        # Deliberately small so they don't compete with
        # the Average section.

        control_font = pygame.font.SysFont(
            "Arial",
            18
        )

        controls_y_1 = (
            self.height - 42
        )

        controls_y_2 = (
            self.height - 18
        )

        # Replay options
        replay_text = control_font.render(
            "1 = Easy    2 = Medium    3 = Hard",
            True,
            WHITE
        )

        replay_rect = replay_text.get_rect(
            center=(
                self.width // 2,
                controls_y_1
            )
        )

        screen.blit(
            replay_text,
            replay_rect
        )

        # Menu / quit
        menu_text = control_font.render(
            "R = Difficulty Menu    Q = Quit",
            True,
            WHITE
        )

        menu_rect = menu_text.get_rect(
            center=(
                self.width // 2,
                controls_y_2
            )
        )

        screen.blit(
            menu_text,
            menu_rect
        )