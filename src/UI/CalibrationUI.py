from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

class CalibrationUI:
    """
    Provides specific guidance text for Arm and Vision calibration steps.
    """

    def __init__(self):
        self.width = 176 # Optimized for 180 total width

    def arm_calibration_guide(self, current_point, description):
        """Displays instructions for physical arm alignment."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="center")

        guide_text = Text.from_markup(
            f"\n[bold cyan]STEP: Physical Arm Alignment[/]\n\n"
            f"Current Target: [bold yellow]{current_point}[/]\n"
            f"Instructions: [white]{description}[/]\n\n"
            "Controls: [bold reverse] SPACE [/] - Next Point | [bold reverse] ENTER [/] - Finish Alignment"
        )
        grid.add_row(guide_text)

        return Panel(
            Align.center(grid, vertical="middle"),
            title="[bold green] HARDWARE CALIBRATION MODE [/]",
            border_style="green",
            width=self.width,
            height=10
        )

    def vision_calibration_guide(self, current_set):
        """Displays instructions for visual camera alignment."""
        content = Text.from_markup(
            f"\n[bold cyan]STEP: Camera View Alignment[/]\n\n"
            f"Active Reference: [bold yellow]{current_set}[/]\n"
            "Instructions: Ensure the green boxes on the video feed align with physical squares.\n\n"
            "Controls: [bold reverse] SPACE [/] - Switch Point Set | [bold reverse] ENTER [/] - Save & Exit"
        )
        return Panel(
            Align.center(content, vertical="middle"),
            title="[bold magenta] VISION CALIBRATION MODE [/]",
            border_style="magenta",
            width=self.width,
            height=10
        )
