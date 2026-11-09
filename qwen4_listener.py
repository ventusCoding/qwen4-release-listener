"""Watches Hugging Face for Qwen4 and sends a phone message through ntfy the moment it appears.
Run: double-click "Start Qwen4 Listener.bat" (or: python qwen4_listener.py). Close the window to stop. Standard library only.
  python qwen4_listener.py --once   one check, then exit (sends nothing unless something new is found)
  python qwen4_listener.py --test   checks the name matching and sends one test message"""
import hashlib, io, json, math, os, platform, random, re, secrets, shutil, sys, tarfile, time, urllib.request, zipfile

NTFY = "https://ntfy.sh"
DEFAULT_TOPIC = "qwen4"
TOPIC = DEFAULT_TOPIC
DEV = False
MODELS_URL = "https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=100"
SEARCH_URL = "https://huggingface.co/api/models?author=Qwen&search=qwen4&limit=100"
COLLECTIONS_URL = "https://huggingface.co/Qwen/collections"
DEFAULT_SECONDS = 60
RELEASE_TITLE = "QWEN4 IS RELEASED!"
PING_RESERVE = 50          # ntfy.sh allows 250 messages a day from one PC; every-check messages stop at this many left
SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "already_notified.json")
TOPIC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_topic.json")

# Qwen4, Qwen-4, Qwen 4, Qwen4.5, Qwen4-27B... but not Qwen-4B, Qwen3.4 or Qwen40.
NAME = re.compile(r"(?<![a-z0-9])qwen[-_ ]?4(?:\.\d+)?(?![0-9a-z.])", re.I)
UA = {"User-Agent": "Mozilla/5.0 qwen4-listener"}


GLYPHS = {
    "Q": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║▄▄ ██║", "╚██████╔╝", " ╚══▀▀═╝ "],
    "W": ["██╗    ██╗", "██║    ██║", "██║ █╗ ██║", "██║███╗██║", "╚███╔███╔╝", " ╚══╝╚══╝ "],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "4": ["██╗  ██╗", "██║  ██║", "███████║", "╚════██║", "     ██║", "     ╚═╝"],
}
STOPS = [(59, 130, 246), (124, 92, 242), (168, 85, 247), (236, 72, 153)]    # blue, violet, purple, pink
RESET, DIM, BOLD = "\x1b[0m", "\x1b[2m", "\x1b[1m"
GREEN, RED, BLUE, VIOLET = "\x1b[38;2;74;222;128m", "\x1b[38;2;248;113;113m", "\x1b[38;2;96;165;250m", "\x1b[38;2;192;132;252m"
WIDTH = 64


GLYPHS.update({
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
})
FIREWORK_COLORS = [(59, 130, 246), (168, 85, 247), (236, 72, 153), (250, 204, 21), (74, 222, 128), (255, 255, 255)]


def gradient_rgb(x):
    """(r, g, b) at position x, wrapping around the blue to pink gradient."""
    x = (x % 1.0) * 2
    x = x if x <= 1 else 2 - x          # back and forth, so the wave has no hard seam
    x = min(x, 0.999) * (len(STOPS) - 1)
    i = int(x); f = x - i
    a, b = STOPS[i], STOPS[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


def big_text(word):
    return [" ".join(GLYPHS[c][row] for c in word) for row in range(6)]


def celebrate(names=()):
    """The release show: rocket, flash, fireworks, giant animated title. About 10 seconds, then back to the normal screen."""
    if not sys.stdout.isatty():
        return
    cols, rows = shutil.get_terminal_size((100, 30))
    rows -= 1
    title = big_text("QWEN4")
    if rows >= 20 and cols >= 76:
        title = title + [""] + big_text("RELEASED")
        small = ""
    else:
        small = "R E L E A S E D"
    lines = [("title", t) for t in title]
    if small:
        lines += [("", ""), ("msg", small)]
    lines += [("", ""), ("msg", "CONGRATULATIONS!  IT IS FINALLY HERE!")]
    if names:
        lines += [("", ""), ("name", str(sorted(names)[0])[:cols - 4])]
    top = max((rows - len(lines)) // 2, 0)
    width = max(len(t) for _, t in lines)
    left = max((cols - width) // 2, 0)
    mask = (left - 2, top - 1, left + width + 2, top + len(lines) + 1)
    sparks = []

    def burst(x, y, n, color=None):
        color = color or random.choice(FIREWORK_COLORS)
        speed_top = random.uniform(13, 24)
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi); v = random.uniform(0.25, 1.0) * speed_top
            life = random.uniform(0.7, 1.6)
            sparks.append([x, y, math.cos(a) * v * 2.0, math.sin(a) * v, life, life, color])

    fps, total, launch = 30, 10.0, 0.9
    out = sys.stdout
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    try:
        boomed, next_burst, t0, frame = False, launch + 0.5, time.time(), 0
        cx, peak = cols / 2, max(rows * 0.38, 3)
        while True:
            t = time.time() - t0
            if t >= total:
                break
            grid = [[None] * cols for _ in range(rows)]
            flash = 0
            if t < launch:
                y = rows - 1 - (rows - 1 - peak) * (t / launch) ** 0.7
                sparks.append([cx + random.uniform(-0.6, 0.6), y + 1, random.uniform(-3, 3), random.uniform(4, 10), 0.35, 0.35, (250, 204, 21)])
                if 0 <= int(y) < rows:
                    grid[int(y)][int(cx)] = ("^", (255, 255, 255))
            elif not boomed:
                boomed = True
                out.write("\a")
                burst(cx, peak, 320, (255, 255, 255))
                burst(cx, peak, 160, (168, 85, 247))
            if boomed and t - launch < 0.14:
                flash = int(235 * (1 - (t - launch) / 0.14))
            if boomed and t < total - 1.6 and t >= next_burst:
                next_burst = t + random.uniform(0.18, 0.42)
                burst(random.uniform(cols * 0.08, cols * 0.92), random.uniform(rows * 0.08, rows * 0.72), random.randint(70, 130))
            dt = 1.0 / fps
            for s in sparks:
                s[0] += s[2] * dt; s[1] += s[3] * dt; s[3] += 13 * dt; s[2] *= 0.982; s[4] -= dt
            sparks[:] = [s for s in sparks if s[4] > 0]
            for s in sparks:
                x, y = int(s[0]), int(s[1])
                if not (0 <= x < cols and 0 <= y < rows):
                    continue
                if t > launch + 0.5 and mask[0] <= x < mask[2] and mask[1] <= y < mask[3]:
                    continue
                k = s[4] / s[5]
                grid[y][x] = ("*" if k > 0.66 else "+" if k > 0.33 else ".", tuple(int(c * (0.3 + 0.7 * k)) for c in s[6]))
            reveal = (t - launch - 0.5) / 0.7
            if reveal > 0:
                for i, (kind, text) in enumerate(lines):
                    y = top + i
                    if not text or not (0 <= y < rows):
                        continue
                    if kind != "title":
                        x0 = left + (width - len(text)) // 2
                    else:
                        x0 = left + (width - len(title[0])) // 2 if len(text) <= len(title[0]) else left
                    show = int(len(text) * min(reveal, 1.0))
                    for j, ch in enumerate(text[:show]):
                        if ch != " " and 0 <= x0 + j < cols:
                            if kind == "name":
                                color = (96, 165, 250)
                            elif kind == "msg":
                                color = (255, 255, 255) if int(t * 4) % 2 else (250, 204, 21)
                            else:
                                color = gradient_rgb(j / 46.0 + i / 28.0 - t * 0.55)
                            grid[y][x0 + j] = (ch, color)
            buf = ["\x1b[H"]
            bg = f"\x1b[48;2;{flash};{flash};{flash}m" if flash else ""
            for r, row in enumerate(grid):
                cur, parts = None, [bg]
                for cell in row:
                    if cell is None:
                        parts.append(" ")
                    else:
                        if cell[1] != cur:
                            cur = cell[1]; parts.append("\x1b[1;38;2;%d;%d;%dm" % cur)
                        parts.append(cell[0])
                parts.append("\x1b[0m")
                if r < rows - 1:
                    parts.append("\r\n")
                buf.append("".join(parts))
            out.write("".join(buf)); out.flush()
            frame += 1
            time.sleep(max(0.0, t0 + frame / fps - time.time()))
    finally:
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l"); out.flush()


def rgb(x):
    """Color at position x (0..1) along the blue to pink gradient."""
    x = min(max(x, 0.0), 0.999) * (len(STOPS) - 1)
    i = int(x); f = x - i
    a, b = STOPS[i], STOPS[i + 1]
    return "\x1b[38;2;%d;%d;%dm" % tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


def gradient(text):
    n = max(len(text) - 1, 1)
    return "".join(rgb(i / n) + c if c != " " else c for i, c in enumerate(text)) + RESET


def setup_console():
    os.system("")                       # turns on colors in the Windows console
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def box(lines, color=VIOLET):
    print(f"  {color}╭{'─' * WIDTH}╮{RESET}")
    for visible, styled in lines:
        print(f"  {color}│{RESET}  {styled}{' ' * max(WIDTH - 2 - len(visible), 0)}{color}│{RESET}")
    print(f"  {color}╰{'─' * WIDTH}╯{RESET}")


def banner():
    print()
    for row in range(6):
        print("    " + BOLD + gradient(" ".join(GLYPHS[c][row] for c in "QWEN4")))
    print()
    print("    " + BOLD + gradient("R E L E A S E   L I S T E N E R") + "\n")
    box([("Watching   huggingface.co/Qwen", f"{DIM}Watching{RESET}   {BLUE}huggingface.co/Qwen{RESET}"),
         ("Stop       close this window", f"{DIM}Stop{RESET}       close this window")])
    print()


def private_topic():
    """This person's own topic: made once on the first run, then always the same. Returns (topic, already set up)."""
    try:
        d = json.load(open(TOPIC_FILE, encoding="utf-8"))
        return d["topic"], bool(d.get("confirmed"))
    except Exception:
        letters = "abcdefghjkmnpqrstuvwxyz23456789"
        t = "qwen4-" + "".join(secrets.choice(letters) for _ in range(10))
        save_private_topic(t, False)
        return t, False


def save_private_topic(topic, confirmed):
    json.dump({"topic": topic, "confirmed": confirmed}, open(TOPIC_FILE, "w", encoding="utf-8"))


def setup_guide(topic):
    """First run: asks about the ntfy phone app, tells the person exactly what to do, then proves the phone receives messages."""
    print()
    while True:
        choice = select("Do you have the ntfy app on your phone?", [("Yes, it is installed", True), ("No, show me how to install it", True),
                                                                    ("Skip for now, keep listening", True), ("Close", True)])
        if choice == 0:
            break
        if choice == 1:
            print()
            box([("Install ntfy on your phone:", f"{BOLD}Install ntfy on your phone:{RESET}"),
                 ("", ""),
                 ("Android  play.google.com, search ntfy", f"{DIM}Android{RESET}  {BLUE}play.google.com{RESET}, search {BOLD}ntfy{RESET}"),
                 ("iPhone   App Store, search ntfy", f"{DIM}iPhone{RESET}   {BLUE}App Store{RESET}, search {BOLD}ntfy{RESET}"),
                 ("No app   open ntfy.sh/app in your browser", f"{DIM}No app{RESET}   open {BLUE}ntfy.sh/app{RESET} in your browser")])
            print()
            continue
        if choice == 2:
            print(f"  {DIM}Skipped. This question comes back next time. Alerts only reach you once you subscribe to {RESET}{BLUE}{topic}{RESET}\n")
            return
        print(f"\n  {DIM}Closed.{RESET}\n")
        sys.exit(0)
    print()
    box([("Your private topic is ready. Do this once:", f"{BOLD}Your private topic is ready. Do this once:{RESET}"),
         ("", ""),
         ("1. Open the ntfy app and tap +", f"{VIOLET}1.{RESET} Open the {BOLD}ntfy{RESET} app and tap {BOLD}+{RESET}"),
         ("2. Subscribe to this topic:", f"{VIOLET}2.{RESET} Subscribe to this topic:"),
         ("", ""),
         ("     " + topic, "     " + BOLD + gradient(topic)),
         ("", ""),
         ("3. Come back here and press Enter", f"{VIOLET}3.{RESET} Come back here and press {BOLD}Enter{RESET}")])
    print()
    input(f"  {VIOLET}❯{RESET} Press Enter when you have subscribed  ")
    try:
        notify("Qwen4 listener connected", "It works. You will get the release alert here.", priority="default")
        print(f"  {GREEN}● Test message sent.{RESET} {DIM}It should be on your phone now.{RESET}\n")
        save_private_topic(topic, True)
    except Exception as e:
        print(f"  {RED}Could not send the test message: {e}{RESET}\n")


def ask_topic():
    """The ntfy topic the phone subscribes to. Enter = this person's own private topic."""
    global TOPIC
    mine, confirmed = private_topic()
    while True:
        text = input(f"  {VIOLET}❯{RESET} ntfy topic to notify {DIM}(Enter = your private topic {RESET}{BLUE}{mine}{RESET}{DIM}){RESET}  ").strip().lstrip("/")
        if not text or text == mine:
            TOPIC = mine
            if not confirmed:
                setup_guide(mine)
            return mine
        if re.fullmatch(r"[-_A-Za-z0-9]{1,64}", text):
            return text
        print(f"  {RED}Use only letters, numbers, - and _ (64 at most).{RESET}")


def already_announced():
    """True if someone already posted the release message to this topic, so a shared topic gets it once, not once per person."""
    try:
        for line in fetch(f"{NTFY}/{TOPIC}/json?poll=1&since=12h").splitlines():
            if RELEASE_TITLE in (json.loads(line).get("title") or ""):
                return True
    except Exception:
        pass
    return False


def read_key():
    """One key press: 'up', 'down', 'enter', or '' for anything else."""
    if os.name == "nt":
        import msvcrt
        c = msvcrt.getwch()
        if c in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
    else:
        import termios, tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            c = sys.stdin.read(1)
            if c == "\x1b" and sys.stdin.read(1) == "[":
                return {"A": "up", "B": "down"}.get(sys.stdin.read(1), "")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if c == "\x03":
        raise KeyboardInterrupt
    return "enter" if c in ("\r", "\n") else ""


def select(title, options):
    """Arrow-key menu. options = list of (label, can_choose). Returns the chosen index."""
    pos = 0
    print(f"  {VIOLET}❯{RESET} {title}  {DIM}(arrows to move, Enter to choose){RESET}")
    if not sys.stdin.isatty():
        return 0
    sys.stdout.write("\x1b[?25l")         # hide the cursor while the menu is open
    drawn = False
    try:
        while True:
            if drawn:
                sys.stdout.write(f"\x1b[{len(options)}A")
            for i, (label, can) in enumerate(options):
                if i == pos and can:
                    line = f"    {BOLD}{gradient('● ' + label)}"
                elif can:
                    line = f"    {DIM}○ {label}{RESET}"
                else:
                    line = f"    {DIM}✕ {label}{RESET}"
                sys.stdout.write("\r\x1b[2K" + line + "\n")
            sys.stdout.flush()
            drawn = True
            key = read_key()
            if key == "enter":
                return pos
            if key in ("up", "down"):
                step = -1 if key == "up" else 1
                p = pos + step
                while 0 <= p < len(options) and not options[p][1]:
                    p += step
                if 0 <= p < len(options):
                    pos = p
    finally:
        sys.stdout.write("\x1b[?25h"); sys.stdout.flush()


def ask_mode(every, shared):
    """True = a phone message after every check, False = only when Qwen4 is released."""
    second = f"Every {every} seconds, after each check"
    if shared:
        second += f"  (needs your own topic {private_topic()[0]})"
    return select("Phone messages", [("Only when Qwen4 is released", True), (second, not shared)]) == 1


def messages_remaining():
    """How many messages ntfy.sh still allows from this PC today (shared with the render notifications)."""
    try:
        return json.loads(fetch("https://ntfy.sh/v1/account"))["stats"]["messages_remaining"]
    except Exception:
        return None


class Pings:
    """Every-check messages. They stop while ntfy's daily allowance is low, so the release message always gets through."""
    def send(self, checks):
        left = messages_remaining()
        if left is not None and left <= PING_RESERVE:
            return "paused"
        try:
            notify("Qwen4: not yet", f"Check {checks} at {time.strftime('%H:%M:%S')}: no Qwen4 on Hugging Face.", priority="low")
            return "sent"
        except Exception:
            return "failed"


def clear_line():
    sys.stdout.write("\r\x1b[2K"); sys.stdout.flush()


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def find_qwen4():
    """Everything named Qwen4 on the Qwen organisation's models and collections. Raises if every source failed."""
    found, ok = set(), 0
    for url in (MODELS_URL, SEARCH_URL):
        try:
            for m in json.loads(fetch(url)):
                short = m["id"].split("/", 1)[-1]
                if NAME.search(short):
                    found.add(m["id"])
            ok += 1
        except Exception as e:
            print(time.strftime("%H:%M:%S"), "could not read models:", e, flush=True)
    try:
        html = fetch(COLLECTIONS_URL)
        for match in NAME.finditer(html):
            found.add("collection: " + match.group(0))
        ok += 1
    except Exception as e:
        print(time.strftime("%H:%M:%S"), "could not read collections:", e, flush=True)
    if not ok:
        raise RuntimeError("no source could be read")
    return found


def notify(title, message, click="https://huggingface.co/Qwen", priority="urgent"):
    req = urllib.request.Request(f"{NTFY}/{TOPIC}", data=message.encode("utf-8"), method="POST",
                                 headers={"Title": title, "Priority": priority, "Click": click, "Tags": "rocket", **UA})
    urllib.request.urlopen(req, timeout=30).read()


def seen():
    try:
        return set(json.load(open(SEEN_FILE, encoding="utf-8")))
    except Exception:
        return set()


def check():
    new = find_qwen4() - seen()
    if new:
        names = sorted(new)
        if not already_announced():
            notify(RELEASE_TITLE, "Found on Hugging Face:\n" + "\n".join(names[:10]))
        json.dump(sorted(seen() | new), open(SEEN_FILE, "w", encoding="utf-8"), indent=1)
        clear_line()
        try:                            # the phone was already told: a display problem must never stop the listener
            celebrate(new)
        except Exception:
            sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        print()
        box([("QWEN4 IS RELEASED!  Your phone was notified.", f"{GREEN}{BOLD}QWEN4 IS RELEASED!{RESET}  Your phone was notified.")] +
            [(n[:WIDTH - 4], f"{BLUE}{n[:WIDTH - 4]}{RESET}") for n in names[:10]], GREEN)
        print(flush=True)
    return new


def ask_interval():
    """Seconds between checks, typed at start. Enter = the default. Under 10 s is raised to 10 to stay polite to Hugging Face."""
    while True:
        text = input(f"  {VIOLET}❯{RESET} Check every how many seconds? {DIM}(Enter = {DEFAULT_SECONDS}){RESET}  ").strip()
        if not text:
            return DEFAULT_SECONDS
        if text.isdigit() and int(text) > 0:
            return max(10, int(text))
        print(f"  {RED}Please type a whole number of seconds, or just press Enter.{RESET}")


def reset():
    """Back to first use: forgets the private topic and what was already notified."""
    setup_console()
    banner()
    mine = None
    try:
        mine = json.load(open(TOPIC_FILE, encoding="utf-8")).get("topic")
    except Exception:
        pass
    if mine:
        print(f"  Your current topic {BLUE}{mine}{RESET} will be forgotten. You will get a new one to subscribe to.\n")
    if select("Reset to first use?", [("Cancel, keep everything", True), ("Yes, reset", True)]) != 1:
        print(f"\n  {DIM}Nothing was changed.{RESET}\n")
        return
    for f in (TOPIC_FILE, SEEN_FILE):
        if os.path.exists(f):
            os.remove(f)
    print(f"\n  {GREEN}● Reset done.{RESET} {DIM}The next start is like the first time.{RESET}\n")


def default_install_dir():
    if os.name == "nt":
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ntfy")
    return os.path.join(os.path.expanduser("~"), ".local", "bin")


def ntfy_on_pc():
    """Path of the ntfy program on this computer, or None."""
    if DEV:
        return None
    exe = "ntfy.exe" if os.name == "nt" else "ntfy"
    found = shutil.which("ntfy")
    if found:
        return found
    p = os.path.join(default_install_dir(), exe)
    return p if os.path.isfile(p) else None


def release_asset_suffix():
    arch = platform.machine().lower()
    if os.name == "nt":
        return "windows_amd64.zip"
    if sys.platform == "darwin":
        return "darwin_all.tar.gz"
    return ("linux_arm64" if arch in ("aarch64", "arm64") else "linux_amd64") + ".tar.gz"


def download(url):
    """Downloads with a live percent line."""
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)
    total, data = int(r.headers.get("Content-Length") or 0), bytearray()
    while True:
        chunk = r.read(262144)
        if not chunk:
            break
        data += chunk
        if total:
            clear_line(); sys.stdout.write(f"  {BLUE}Downloading{RESET} {len(data) * 100 // total}%"); sys.stdout.flush()
    clear_line()
    return bytes(data)


def add_to_user_path(folder):
    """Adds the folder to the user's PATH (Windows registry, or a note on Mac and Linux). New windows will see it."""
    if os.name != "nt":
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
        try:
            cur, kind = winreg.QueryValueEx(k, "Path")
        except FileNotFoundError:
            cur, kind = "", winreg.REG_EXPAND_SZ
        if folder.lower() not in [p.strip().lower() for p in cur.split(";")]:
            winreg.SetValueEx(k, "Path", 0, kind, (cur.rstrip(";") + ";" + folder).lstrip(";"))


def install_ntfy(dest=None, change_path=True):
    """Installs the official ntfy release from GitHub after checking its SHA-256. Returns the program's path."""
    dest = dest or default_install_dir()
    rel = json.loads(fetch("https://api.github.com/repos/binwiederhier/ntfy/releases/latest"))
    suffix = release_asset_suffix()
    assets = {a["name"]: a["browser_download_url"] for a in rel["assets"]}
    name = next(n for n in assets if n.endswith(suffix))
    want = next(l.split()[0] for l in fetch(assets["checksums.txt"]).splitlines() if l.split()[-1].lstrip("*") == name)
    data = download(assets[name])
    if hashlib.sha256(data).hexdigest() != want.lower():
        raise RuntimeError("the download failed its checksum, nothing was installed")
    exe = "ntfy.exe" if os.name == "nt" else "ntfy"
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            blob = z.read(next(n for n in z.namelist() if n.rsplit("/", 1)[-1] == exe))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
            blob = t.extractfile(next(m for m in t.getmembers() if m.name.rsplit("/", 1)[-1] == exe)).read()
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, exe)
    with open(path, "wb") as f:
        f.write(blob)
    if os.name != "nt":
        os.chmod(path, 0o755)
    if change_path:
        add_to_user_path(dest)
    return path


def ensure_ntfy():
    """Checks for ntfy on this PC. If missing: install it automatically, or skip and close."""
    found = ntfy_on_pc()
    if found:
        print(f"  {GREEN}●{RESET} {DIM}ntfy is installed:{RESET} {BLUE}{found}{RESET}\n")
        return
    box([("ntfy is not installed on this PC.", f"{RED}{BOLD}ntfy is not installed on this PC.{RESET}"),
         ("", ""),
         ("It can be installed for you, from its official release.", f"{DIM}It can be installed for you, from its official release.{RESET}")])
    print()
    while True:
        if select("Install ntfy now?", [("Yes, install it automatically", True), ("Skip and close", True)]) == 1:
            print(f"\n  {DIM}Closed. Nothing was installed.{RESET}\n")
            sys.exit(0)
        print()
        if DEV:
            print(f"  {DIM}[DEV] install skipped, nothing was downloaded.{RESET}\n")
            return
        try:
            path = install_ntfy()
            print(f"  {GREEN}● ntfy installed:{RESET} {BLUE}{path}{RESET}\n")
            return
        except Exception as e:
            print(f"  {RED}Could not install ntfy: {e}{RESET}\n")


def dev_mode():
    """Preview of the first use: temporary files, no real phone messages, and a fake release on the second check."""
    global TOPIC_FILE, SEEN_FILE, notify, find_qwen4, DEV
    import tempfile
    d = tempfile.mkdtemp(prefix="qwen4-dev-")
    TOPIC_FILE, SEEN_FILE, DEV = os.path.join(d, "my_topic.json"), os.path.join(d, "already_notified.json"), True
    checks = {"n": 0}

    def fake_find():
        checks["n"] += 1
        return {"Qwen/Qwen4-DEV-PREVIEW"} if checks["n"] >= 2 else set()

    def fake_notify(title, message, **kw):
        clear_line()
        print(f"  {DIM}[DEV] phone message NOT sent:{RESET} {VIOLET}{title}{RESET}", flush=True)
    find_qwen4, notify = fake_find, fake_notify


def released_at_start():
    """Opened after the release: play the show and stop, there is nothing left to listen for.
    Needs a real model on Hugging Face; a mention on the collections page alone is not enough to stop listening."""
    global TOPIC
    try:
        found = find_qwen4()
    except Exception:
        return False
    models = sorted(n for n in found if not n.startswith("collection:"))
    if not models:
        return False
    mine, confirmed = private_topic()
    new = set(models) - seen()
    if new and confirmed:               # first time this PC sees it, and the phone is set up
        TOPIC = mine
        try:
            if not already_announced():
                notify(RELEASE_TITLE, "Found on Hugging Face:\n" + "\n".join(sorted(new)[:10]))
        except Exception:
            pass
    json.dump(sorted(seen() | set(models)), open(SEEN_FILE, "w", encoding="utf-8"), indent=1)
    try:
        celebrate(models)
    except Exception:
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
    print()
    box([("QWEN4 IS RELEASED!", f"{GREEN}{BOLD}QWEN4 IS RELEASED!{RESET}")] +
        [(n[:WIDTH - 4], f"{BLUE}{n[:WIDTH - 4]}{RESET}") for n in models[:10]] +
        [("", ""), ("You don't need the listener anymore. Enjoy!", f"{DIM}You don't need the listener anymore. Enjoy!{RESET}")], GREEN)
    print(flush=True)
    return True


def main():
    global TOPIC
    if "--celebrate" in sys.argv:       # just watch the release animation
        setup_console()
        celebrate({"Qwen/Qwen4-27B"})
        return
    if "--dev" in sys.argv:
        dev_mode()
    if "--reset" in sys.argv:
        reset()
        return
    if "--test" in sys.argv or "--once" in sys.argv:     # these never post to the shared topic
        TOPIC = private_topic()[0]
    if "--test" in sys.argv:
        yes = ["Qwen4", "Qwen4-27B", "Qwen-4", "Qwen 4", "Qwen4.5-Flash", "qwen4_72b", "Qwen/Qwen4-VL"]
        no = ["Qwen3.8-27B", "Qwen-4B", "Qwen3.4", "Qwen40", "Qwen-Drive-1.0-4B", "qwen_4b_ace15", "Qwen-Image-2.1", "Qwen3-VL-4B"]
        bad = [n for n in yes if not NAME.search(n)] + [n for n in no if NAME.search(n)]
        print("name matching:", "OK" if not bad else f"WRONG for {bad}")
        print("found right now:", sorted(find_qwen4()))
        notify("Qwen4 listener test", "If you see this, your phone will get the Qwen4 message.", priority="default")
        print("test message sent")
        return
    if "--once" in sys.argv:
        print("new:", sorted(check()))
        return
    setup_console()
    if not DEV and released_at_start():
        return
    banner()
    if DEV:
        print(f"  {BOLD}{gradient('DEV PREVIEW')}{RESET}  {DIM}first use, nothing saved, no phone messages. A fake release appears on the second check.{RESET}\n")
    ensure_ntfy()
    TOPIC = ask_topic()
    every = ask_interval()
    # a shared topic must never get one message per person, per minute: that option is shown but locked
    every_check = ask_mode(every, TOPIC == DEFAULT_TOPIC)
    print()
    box([(f"Subscribe  ntfy app, topic {TOPIC}", f"{DIM}Subscribe{RESET}  ntfy app, topic {BLUE}{BOLD}{TOPIC}{RESET}"),
         (f"Or open    {NTFY}/{TOPIC}", f"{DIM}Or open{RESET}    {BLUE}{NTFY}/{TOPIC}{RESET}")], BLUE)
    print()
    checks, last, problem, phone = 0, "--:--:--", "", "every check" if every_check else "only on release"
    pings = Pings()
    while True:
        try:
            new = check()
            checks += 1; last = time.strftime("%H:%M:%S"); problem = ""
            if every_check and not new:
                r = pings.send(checks)
                phone = {"sent": "every check", "paused": "paused, saving ntfy limit", "failed": "ping failed"}[r]
        except Exception as e:
            problem = str(e)[:40]
        for left in range(every, 0, -1):
            dot = (GREEN if left % 2 else DIM + GREEN) + "●" + RESET
            state = f"{RED}check failed: {problem}{RESET}" if problem else f"{BOLD}Listening{RESET}"
            clear_line()
            sys.stdout.write(f"  {dot} {state}  {DIM}last check{RESET} {last}  {DIM}next in{RESET} {left}s  {DIM}checks{RESET} {checks}  {DIM}phone{RESET} {phone}")
            sys.stdout.flush()
            time.sleep(1)


if __name__ == "__main__":
    main()
