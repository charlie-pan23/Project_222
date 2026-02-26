from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.table import Table

class UIOverlays:
    """
    Handles transient UI elements like dialogs, alerts, and end-game results.
    Standardized for 180x50 resolution.
    """

    @staticmethod
    def calibration_request():
        """Prompts user to decide whether to run calibration."""
        content = Text.from_markup(
            "\n[bold white]System Core Initialized.[/]\n\n"
            "Would you like to perform board alignment calibration?\n\n"
            "[bold green]\[Y][/] - Yes (Recommended)  |  [bold red]\[N][/] - No (Skip to Game)"
        )
        return Panel(
            Align.center(content, vertical="middle"),
            title="[bold yellow] CALIBRATION REQUIRED [/]",
            border_style="bright_magenta",
            width=80,
            height=12
        )

    @staticmethod
    def game_over(result, winner, move_count):
        """Displays the final result of the chess match."""
        result_text = Text.from_markup(
            f"\n[bold yellow]GAME OVER[/]\n\n"
            f"Result: [bold cyan]{result}[/]\n"
            f"Winner: [bold green]{winner}[/]\n"
            f"Total Moves: [bold white]{move_count}[/]\n\n"
            "Press [bold reverse] ESC [/] to exit or [bold reverse] R [/] to restart."
        )
        return Panel(
            Align.center(result_text, vertical="middle"),
            title="[bold red] MATCH SUMMARY [/]",
            border_style="bright_red",
            width=60,
            height=15
        )

    @staticmethod
    def processing_move(uci):
        """Warning overlay to prevent board interference during vision processing."""
        content = Text.from_markup(
            f"\n[blink bold red]PROCESSING MOVE: {uci}[/]\n\n"
            "Please [bold white]DO NOT[/] touch the board or the robotic arm."
        )
        return Panel(
            Align.center(content, vertical="middle"),
            border_style="red",
            width=70,
            height=8
        )

    @staticmethod
    def module_config_overlay(v_status, a_status):
        """
        Visual indicator of which modules are being loaded.
        """
        v_text = "[green]ENABLED[/]" if v_status else "[red]DISABLED[/]"
        a_text = "[green]ENABLED[/]" if a_status else "[red]DISABLED[/]"

        content = Text.from_markup(
            f"\n[bold white]Target Environment Configuration[/]\n\n"
            f"Vision System: {v_text}\n"
            f"Robotic Arm:   {a_text}\n\n"
            "Initializing System..."
        )
        return Panel(Align.center(content, vertical="middle"), border_style="cyan", width=60, height=10)
