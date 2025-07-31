from typing import Optional

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

def print_success(text: str, end: Optional[str] = "\n"):
    print(f"{GREEN}{BOLD}{text}{RESET}", end=end)
def print_error(text: str, end: Optional[str] = "\n"):
    print(f"{RED}{BOLD}{text}{RESET}", end=end)
def print_warning(text: str, end: Optional[str] = "\n"):
    print(f"{YELLOW}{BOLD}{text}{RESET}", end=end)
def print_info(text: str, end: Optional[str] = "\n"):
    print(f"{BLUE}{BOLD}{text}{RESET}", end=end)
def print_red_bg(text: str, end: Optional[str] = "\n"):
    print(f"{BG_RED}{BOLD}{text}{RESET}", end=end)
def print_green_bg(text: str, end: Optional[str] = "\n"):
    print(f"{BG_GREEN}{BOLD}{text}{RESET}", end=end)
def print_yellow_bg(text: str, end: Optional[str] = "\n"):
    print(f"{BG_YELLOW}{BOLD}{text}{RESET}", end=end)
    
