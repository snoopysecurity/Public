# explainshell-cli

A simple CLI wrapper for [explainshell.com](https://explainshell.com) to explain shell commands in your terminal.

Usage:
```bash
explainshell-cli tar -xzvf
```

```
❯ explainshell-cli ls -la
╭───── 🔍 Explanation ──────╮
│                           │
│  list directory contents  │
│                           │
╰───────────────────────────╯
╭────── 🔍 Explanation ───────╮
│                             │
│  -l                         │
│  use a long listing format  │
│                             │
╰─────────────────────────────╯
╭──────────── 🔍 Explanation ─────────────╮
│                                         │
│  -a                                     │
│  ,                                      │
│  --all                                  │
│  do not ignore entries starting with .  │
│                                         │
╰─────────────────────────────────────────╯
```


## 📦 Installation

Clone the repo and install it with pip:

```bash
git clone https://github.com/snoopysecurity/explainshell-cli.git
cd explainshell-cli
pip install .
```
