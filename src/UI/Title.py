import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

class StartupUI:
    """
    Startup screen handler located in the ui package.
    Managed exclusively by Main and Coordinator.
    """
    def __init__(self):
        self.console = Console(width=180, height=50)
        self.title_art = """
 ██████╗██╗  ██╗███████╗███████╗███████╗    ██████╗  ██████╗ ████████╗
██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝
██║     ███████║█████╗  ███████╗███████╗    ██████╔╝██║   ██║   ██║
██║     ██╔══██║██╔══╝  ╚════██║╚════██║    ██╔══██╗██║   ██║   ██║
╚██████╗██║  ██║███████╗███████║███████║    ██████╔╝╚██████╔╝   ██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝
        """
        self.binary_chess_art = """
                     ...
                    .X+.
             .::    :X;.                ..;:
             .;Xx:  .;;.               ..+&X:
               .;+...:;:.             .:$&&&$+.
         ..::::. .+&&&&$;.            :$&&&&&&+.
         .;x;;x+..+&&&&&X;:..         .x&&&&&$;
                .;&&&&&&&&x..         .:&&&&&+.
                 ...:x$&&&&$;..       .;$&&&&+.
                     +x+$&&&&&$Xxx...  .+&&&x.
                        .x&&&&&&&&&&&+ :X&&&$;
                         .X&&&&&&&&&+..+&&&&&x.
                          :$&&&&&&x:..X&&&&&&&X:.
                          .X&&&&X: .:X&&&&&&&&&X:.
                           +&&$;   .+&&&&&&&&&&&x.
                            .:.
        """

    def render(self, subtitle="Loading Core Modules..."):
        """
        Renders the title screen with a dynamic subtitle.
        """
        grid = Table.grid(expand=True, padding=(0, 5))
        grid.add_column(justify="center", ratio=3)
        grid.add_column(justify="center", ratio=2)

        grid.add_row(
            Text(self.title_art, style="bold cyan"),
            Text(self.binary_chess_art, style="dim green")
        )

        main_panel = Panel(
            grid,
            title="[bold yellow] SYSTEM INITIALIZATION [/]",
            subtitle=f"[white]{subtitle}[/]", # Dynamic subtitle
            border_style="bright_blue",
            padding=(4, 4),
            width=176,
        )

        self.console.clear()
        self.console.print(
            Align(main_panel, align="center", vertical="middle"),
            height=self.console.height
        )

