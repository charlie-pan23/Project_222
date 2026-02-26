import psutil
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.console import Console
from Utils.Logger import LOG_BUFFER

class ChessDashboard:
    """
    TUI Dashboard for Raspberry Pi 4B Chess Robot.
    Updated: Removed internal logger to allow standard terminal scrolling.
    """
    def __init__(self):
        self.console = Console(width=180)
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        """
        Define the structural regions.
        Divided into Main Area, Log Zone, Input Zone, and Hardware Status.
        """
        self.layout.split_column(
            Layout(name="main_area", size=32),   # Main visual data (Board, Info)
            Layout(name="log_zone", size=12),     # Scrolling system logs
            Layout(name="input_zone", size=3),   # Real-time UCI input area
            Layout(name="hardware", size=3),     # System telemetry
        )

        # Internal split for main_area remains largely the same
        self.layout["main_area"].split_row(
            Layout(name="board_zone", ratio=4),
            Layout(name="captured_zone", size=25),
            Layout(name="info_zone", ratio=1),
        )
        self.layout["info_zone"].split_column(
            Layout(name="steps", ratio=3),
            Layout(name="machine_state", size=3),
            Layout(name="check_state", size=3),
        )
    def make_log_panel(self):
        """Retrieve logs from LOG_BUFFER and render as a scrolling panel."""
        log_content = "\n".join(list(LOG_BUFFER))
        return Panel(
            Text(log_content, style="white"),
            title="[bold yellow]SYSTEM LOGS[/]",
            border_style="yellow",
            padding=(0, 1)
        )

    def make_input_panel(self, current_input=""):
        """Displays the text currently being typed by the user."""
        return Panel(
            Text(f"> {current_input}", style="bold green"),
            title="[bold cyan]UCI COMMAND INPUT[/]",
            border_style="cyan",
            padding=(0, 1)
        )

    def format_piece(self, char):
        """Style chess pieces: White (Yellow), Black (Cyan), Empty (Dim White)."""
        if char == ".":
            return Text(".", style="dim white")
        if char.isupper():
            return Text(char, style="bold yellow")
        return Text(char, style="bold cyan")

    def make_board(self, fen):
        """Generate a square board with coordinates."""
        inner_table = Table(
            show_header=False,
            show_edge=True,
            box=None,
            padding=(1, 1),
            border_style="bright_blue"
        )

        for _ in range(8):
            inner_table.add_column(justify="center",width=5)

        board_str = fen.split(' ')[0]
        rows = board_str.split('/')

        for i, row in enumerate(rows):
            row_data = []
            for char in row:
                if char.isdigit():
                    row_data.extend([self.format_piece(".")] * int(char))
                else:
                    row_data.append(self.format_piece(char))
            inner_table.add_row(*row_data)

        rank_col = Table.grid(padding=(2, 0))
        for i in range(8, 0, -1):
            rank_col.add_row(Text(f"{i} ", style="bold magenta"))

        file_labels = Text("    a      b      c      d      e      f      g      h", style="bold magenta")

        board_with_ranks = Table.grid(padding=0)
        board_with_ranks.add_column()
        board_with_ranks.add_column()
        board_with_ranks.add_row(Align(rank_col, vertical="middle"), Panel(inner_table, border_style="bright_blue", padding=0))

        final_stack = Table.grid()
        final_stack.add_row(Align.center(board_with_ranks))
        final_stack.add_row(Align.center(file_labels))

        return Panel(
            Align.center(final_stack, vertical="middle"),
            title="[bold blue]CHESSBOARD[/]",
            border_style="blue",
            padding=(0, 1)
        )

    def make_system_status(self):
        """Hardware monitoring panel."""
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
            f"CPU: [bold cyan]{cpu}%[/]",
            f"Temp: [bold {t_style}]{temp:.1f}°C[/]",
            f"RAM: [bold yellow]{ram}%[/]"
        )
        return Panel(status_table, title="[bold white]SYSTEM STATUS[/]", border_style="white")

    def make_state_box(self, label, content, color):
        """Status indicators for Waiting/Check states."""
        return Panel(
            Align.center(Text(content, style=f"bold {color}"), vertical="middle"),
            title=f"[bold]{label}[/]",
            border_style=color,
            padding=0
        )

    def make_taken_panel(self, white_taken, black_taken):
        """Captured pieces panel with wider spacing and clear labels."""
        top_str = " ".join([self.format_piece(p).markup for p in white_taken])
        bottom_str = " ".join([self.format_piece(p).markup for p in black_taken])

        # Use placeholders if lists are empty
        w_display = top_str if top_str else "[dim]No captures[/]"
        b_display = bottom_str if bottom_str else "[dim]No captures[/]"

        combined_content = f"[bold yellow]White holds:[/]\n{w_display}\n\n[dim]------------------[/]\n\n[bold cyan]Black holds:[/]\n{b_display}"

        return Panel(
            Align.center(Text.from_markup(combined_content), vertical="middle"),
            title="[bold white]PIECES TAKEN[/]",
            border_style="white",
            padding=(1, 1)
        )
    def make_steps_panel(self, move_history):
        recent_moves = move_history[-10:]
        steps_text = "\n".join([f"[bold cyan]{i+1}.[/] {move}" for i, move in enumerate(recent_moves)])

        return Panel(
            Text.from_markup(steps_text if steps_text else "No moves yet..."),
            title="[bold green]MOVE HISTORY[/]",
            border_style="green",
            padding=(1, 2)
        )
