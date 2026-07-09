import sys
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
import argparse
import fileinput

console = Console()

def get_input_command(args):
    """Get command either from CLI args or piped stdin."""
    if args:
        return " ".join(args).strip()
    else:
        return "".join(line for line in fileinput.input()).strip()

def explain(command):
    encoded = quote_plus(command)
    url = f"https://explainshell.com/explain?cmd={encoded}"
    
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as e:
        console.print(f"[bold red]Network error:[/bold red] {e}")
        sys.exit(1)

    if resp.status_code == 429:
        console.print("[bold yellow]Rate limited by explainshell.com. Try again later.[/bold yellow]")
        sys.exit(1)
    elif not resp.ok:
        console.print(f"[bold red]Error fetching explanation.[/bold red] Status code: {resp.status_code}")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, 'html.parser')
    help_boxes = soup.find_all(class_='help-box')

    if not help_boxes:
        console.print("[yellow]No explanations found. Try a simpler or different command.[/yellow]")
        sys.exit(0)

    for box in help_boxes:
        text = box.get_text(strip=True, separator="\n")
        console.print(Panel.fit(text, title="🔍 Explanation", padding=(1, 2)))

def main():
    parser = argparse.ArgumentParser(
        description="Explain shell commands using explainshell.com",
        add_help=False
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Shell command to explain")
    args = parser.parse_args()

    command = get_input_command(args.command)

    if not command or command in ("-h", "--help"):
        console.print("[bold red]Usage:[/bold red] explainshell-cli COMMAND [ARGS...]")
        console.print("       echo \"COMMAND\" | explainshell-cli")
        console.print("Example: explainshell-cli tar -xzvf file.tar.gz")
        sys.exit(1)

    explain(command)
