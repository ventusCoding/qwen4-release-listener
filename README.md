<div align="center">

# 🚀 Qwen4 Release Listener

**Get a phone alert the moment Qwen4 lands on Hugging Face.**

No account. No API key. Just run it and go back to your day.

![Python](https://img.shields.io/badge/Python-3.9%2B-3b82f6?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-a855f7?style=for-the-badge)
![Notifications](https://img.shields.io/badge/Alerts-ntfy-ec4899?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)

</div>

```
 ██████╗  ██╗    ██╗ ███████╗ ███╗   ██╗ ██╗  ██╗
██╔═══██╗ ██║    ██║ ██╔════╝ ████╗  ██║ ██║  ██║
██║   ██║ ██║ █╗ ██║ █████╗   ██╔██╗ ██║ ███████║
██║▄▄ ██║ ██║███╗██║ ██╔══╝   ██║╚██╗██║ ╚════██║
╚██████╔╝ ╚███╔███╔╝ ███████╗ ██║ ╚████║      ██║
 ╚══▀▀═╝   ╚══╝╚══╝  ╚══════╝ ╚═╝  ╚═══╝      ╚═╝

R E L E A S E   L I S T E N E R

● Listening  last check 14:12:52  next in 42s  checks 18  phone only on release
```

---

## ✨ What it does

It watches the [Qwen page on Hugging Face](https://huggingface.co/Qwen). As soon as a model or collection named Qwen4 appears, your phone gets an alert. Tap it to open the page.

- 📱 **Instant phone alerts** through the free [ntfy](https://ntfy.sh) app
- 🔒 **Your own private topic**, created for you on first run
- ⏱️ **You choose the timer**, every 60 seconds by default
- 🎆 **A fireworks show in your terminal** the moment it drops
- 🎮 **Simple menus** you control with the arrow keys
- 🧰 **Guided setup**: it tells you exactly what to do, then sends a test message

---

## 🚀 Quick start

### 1. Install Python

You need **Python 3.9 or newer**. Get it from [python.org/downloads](https://www.python.org/downloads/).

| System | Notes |
|---|---|
| **Windows** | Tick **Add Python to PATH** in the installer |
| **Ubuntu / Linux** | Usually already installed. If not: `sudo apt install python3` |
| **macOS** | After installing from python.org, open **Applications › Python 3.x** and run **Install Certificates.command** once, or it can't reach the internet |

### 2. Download this project

Click the green **Code** button above, then **Download ZIP**, and unzip it.

Or use git:

```bash
git clone https://github.com/ventusCoding/qwen4-release-listener.git
cd qwen4-release-listener
```

### 3. Start it

| System | What to do |
|---|---|
| **Windows** | Double-click `Start Qwen4 Listener.bat` |
| **macOS / Linux** | Run `python3 qwen4_listener.py` in a terminal |

### 4. Follow the screen

The first time, it walks you through everything:

1. **ntfy check.** If the ntfy program is missing on your computer, choose to install it automatically, or skip and close.
2. **Your topic.** Press **Enter** to use the private topic it created for you.
3. **The phone app.** If you don't have ntfy on your phone, choose **No, show me how to install it**.
4. **Subscribe.** In the ntfy app, tap **+** and type the topic shown on screen. Then press **Enter**.
5. **Test message.** Your phone should get a message right away. That means it works.
6. **Timer.** Type how many seconds between checks, or press **Enter** for 60.
7. **Phone messages.** Pick one with the arrow keys:
   - **Only when Qwen4 is released** (recommended)
   - **After every check**

That's it. Leave the window open and you're done. 🎉

---

## ⚙️ Options

Press **Enter** at any question to accept the default.

| Question | Default | Notes |
|---|---|---|
| ntfy topic | Your private topic | You can type another name |
| Check every how many seconds | `60` | Minimum is `10` |
| Phone messages | Only when released | Use the arrow keys, then Enter |

### Commands

| Command | What it does |
|---|---|
| `python qwen4_listener.py` | Start listening |
| `python qwen4_listener.py --once` | Do one check, then exit |
| `python qwen4_listener.py --test` | Check everything works and send one test message |
| `python qwen4_listener.py --reset` | Start over like the first time |
| `python qwen4_listener.py --celebrate` | Watch the release fireworks right now 🎆 |

### 🎆 Preview the fireworks

Want to see what happens the moment Qwen4 drops?

| System | What to do |
|---|---|
| **Windows** | Double-click `Preview Release Animation.bat` |
| **macOS / Linux** | Run `bash preview-release-animation.sh` in a terminal |
| `python qwen4_listener.py --dev` | Preview the first run with a fake release. Saves nothing and sends nothing |

> On macOS and Linux, use `python3`.

---

## ❓ Questions

<details>
<summary><b>Does my computer need to stay on?</b></summary>
<br>
Yes. It only checks while the window is open and your computer is awake.
</details>

<details>
<summary><b>What if I open it after Qwen4 is already out?</b></summary>
<br>
It plays the fireworks, shows the models it found, and stops. There is nothing left to listen for.
</details>

<details>
<summary><b>How do I stop it?</b></summary>
<br>
Just close the window.
</details>

<details>
<summary><b>I didn't get the test message. What should I check?</b></summary>
<br>
Make sure the topic in the ntfy app is exactly the one on screen, and that notifications are allowed for ntfy on your phone.
</details>

<details>
<summary><b>Is my topic private?</b></summary>
<br>
On ntfy, anyone who knows a topic name can read it or post to it. Your topic has a random name, so keep it to yourself. Before you trust any alert, tap it and confirm the model is really on Hugging Face.
</details>

<details>
<summary><b>What is the shared <code>qwen4</code> topic?</b></summary>
<br>
A topic anyone can use. Type <code>qwen4</code> at the first question to use it. To protect its subscribers, it only gets the release message, once. The "after every check" option is locked there.
</details>

<details>
<summary><b>Why did "after every check" messages stop?</b></summary>
<br>
ntfy allows 250 free messages a day from one internet connection. These messages pause when 50 are left, so the release alert can still reach you.
</details>

<details>
<summary><b>Which names does it look for?</b></summary>
<br>
Names like Qwen4, Qwen-4, Qwen4.5 and Qwen4-27B. Size names like Qwen-4B are ignored.
</details>

<details>
<summary><b>How do I remove it?</b></summary>
<br>
Delete the folder. If it installed ntfy for you, also delete <code>%LOCALAPPDATA%\ntfy</code> on Windows, or <code>~/.local/bin/ntfy</code> on macOS and Linux.
</details>

---

<div align="center">

Made for everyone waiting for Qwen4.

Free to use under the [MIT License](LICENSE).

<sub>Not affiliated with Qwen, Alibaba, Hugging Face or ntfy.</sub>

</div>
