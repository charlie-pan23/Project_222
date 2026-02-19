import time
import psutil
from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.console import Console
from rich.live import Live

class ChessDashboard:
    """
    TUI Dashboard for Raspberry Pi 4B Chess Robot.
    Optimized for 180x50 terminal with a square board layout.
    """
    def __init__(self):
        self.console = Console(width=180, height=50)
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        """Define the structural regions of the TUI."""
        self.layout.split_column(
            Layout(name="main_area", ratio=32),
            Layout(name="hardware", ratio=4),
            Layout(name="logger", ratio=12),
        )
        self.layout["main_area"].split_row(
            Layout(name="board_zone", ratio=4),
            Layout(name="captured_zone", ratio=1),
            Layout(name="info_zone", ratio=3),
        )
        self.layout["info_zone"].split_column(
            Layout(name="steps", ratio=3),
            Layout(name="machine_state", ratio=1),
            Layout(name="check_state", ratio=1),
        )

    def format_piece(self, char):
        """Style chess pieces: White (Yellow), Black (Cyan), Empty (Dim White)."""
        if char == ".":
            return Text(".", style="dim white")
        if char.isupper():
            return Text(char, style="bold yellow")
        return Text(char, style="bold cyan")

    def make_board(self, fen):
        """Generate a square board with coordinates outside the frame."""
        # Create the inner board with a border
        inner_table = Table(
            show_header=False,
            show_edge=True,
            box=None,
            padding=(1, 1), # Horizontal padding to make cells look square
            border_style="bright_blue"
        )

        # Define 8 columns for the board
        for _ in range(8):
            inner_table.add_column(justify="center", width=3)

        board_str = fen.split(' ')[0]
        rows = board_str.split('/')

        # Build the outer table to hold coordinates (no borders)
        outer_table = Table.grid(padding=(0, 1))
        outer_table.add_column(justify="right") # Rank labels
        outer_table.add_column(justify="center") # The Board

        for i, row in enumerate(rows):
            rank = str(8 - i)
            row_data = []
            for char in row:
                if char.isdigit():
                    row_data.extend([self.format_piece(".")] * int(char))
                else:
                    row_data.append(self.format_piece(char))

            # Add rank label and the board row
            inner_table.add_row(*row_data)

        # Create the file labels (a-h)
        file_labels = Text("    a    b    c    d    e    f    g    h", style="bold magenta")

        # Combine everything into a display group
        board_with_ranks = Table.grid(padding=1)
        board_with_ranks.add_column() # For ranks 1-8
        board_with_ranks.add_column() # For the inner table

        # Create rank column
        rank_col = Table.grid(padding=(2, 0))
        for i in range(8, 0, -1):
            rank_col.add_row(Text(f"{i} ", style="bold magenta"), end_section=True)

        board_with_ranks.add_row(
            Align(rank_col, vertical="middle"), # <--- Change to "top" or "bottom"
            Panel(inner_table, border_style="bright_blue", padding=0))

        # Final layout assembly
        final_stack = Table.grid()
        final_stack.add_row(Align.center(board_with_ranks))
        final_stack.add_row(Align.center(file_labels))

        return Panel(
            Align.center(final_stack, vertical="middle"),
            title="[bold blue]CHESSBOARD (TOP VIEW)[/]",
            border_style="blue",
            padding=(1, 2)
        )

    def make_system_status(self):
        """Generate hardware monitoring for Raspberry Pi 4B."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000
        except:
            temp = 0.0

        status_table = Table.grid(expand=True)
        status_table.add_column(justify="center", ratio=1)
        status_table.add_column(justify="center", ratio=1)
        status_table.add_column(justify="center", ratio=1)

        t_style = "green" if temp < 60 else "red"
        status_table.add_row(
            f"CPU Usage: [bold cyan]{cpu}%[/]",
            f"SoC Temp: [bold {t_style}]{temp:.1f}°C[/]",
            f"RAM Usage: [bold yellow]{ram}%[/]"
        )
        return Panel(status_table, title="[bold white]SYSTEM STATUS[/]", border_style="white")

    def make_log_panel(self, logs):
        """Generate the scrolling logger area."""
        log_text = Text("\n".join(logs))
        return Panel(log_text, title="[bold green]LOGGER[/]", border_style="green")

    def make_state_box(self, label, content, color):
        """Create status indicators for Waiting/Check states."""
        return Panel(
            Align.center(Text(content, style=f"bold {color}"), vertical="middle"),
            title=f"[bold]{label}[/]",
            border_style=color
        )
    def make_taken_panel(self, white_taken, black_taken):

    # Use format_piece to keep colors consistent (White=Yellow, Black=Cyan)
        top_str = "\n".join([self.format_piece(p).markup for p in white_taken])
        bottom_str = "\n".join([self.format_piece(p).markup for p in black_taken])

        # Separate them with some space in the narrow 'TAKEN' column
        combined_content = f"{top_str}\n\n---\n\n{bottom_str}"

        return Panel(
            Align.center(Text.from_markup(combined_content), vertical="middle"),
            title="TAKEN",
            border_style="white"
        )

if __name__ == "__main__":
    db = ChessDashboard()

    # Static test data
    test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR"
    test_logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] Booting System...",
        f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to Raspberry Pi 4B...",
        f"[{datetime.now().strftime('%H:%M:%S')}] UI Render Initialized."
    ]

    with Live(db.layout, refresh_per_second=4, screen=True) as live:
        while True:
            db.layout["board_zone"].update(db.make_board(test_fen))
            db.layout["captured_zone"].update(Panel(Align.center("\n\n\n\n\n\n\n"), title="TAKEN"))
            db.layout["steps"].update(Panel("> e2e4\n> Waiting...", title="STEPS"))
            db.layout["machine_state"].update(db.make_state_box("STATUS", "WAITING", "yellow"))
            db.layout["check_state"].update(db.make_state_box("STATE", "NORMAL", "white"))
            db.layout["hardware"].update(db.make_system_status())
            db.layout["logger"].update(db.make_log_panel(test_logs))
            time.sleep(0.5)
