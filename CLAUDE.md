# CLAUDE.md - Smart Multi-Timer Codebase Guide

> Comprehensive guide for AI assistants working with the Smart Multi-Timer codebase

**Last Updated**: 2025-11-15
**Codebase Size**: ~6,100 lines of Python code
**Tech Stack**: Python 3.x, Tkinter, PyGame, Telethon

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Structure](#codebase-structure)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Key Components](#key-components)
5. [Development Workflow](#development-workflow)
6. [Code Conventions](#code-conventions)
7. [Data Persistence](#data-persistence)
8. [Build & Distribution](#build--distribution)
9. [Known Issues & Technical Debt](#known-issues--technical-debt)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Project Overview

**Smart Multi-Timer** is a desktop productivity suite for Windows and Linux that combines multiple time-management and habit-tracking features into a single application.

### Core Features
- **Multi-Timer System**: Run unlimited concurrent timers with custom/preset durations
- **Todo List Management**: Task tracking with priorities, filters, and drag-n-drop
- **Habit Tracking**: Customizable habit reminders with intervals and notifications
- **Medication Tracker**: Schedule-based medication intake tracking
- **Pushup Counter**: Fitness tracking with session history
- **Telegram Integration**: Message management and folder filtering

### Target Platform
- **Primary**: Windows 10/11
- **Secondary**: Linux (with WSL detection)
- **Not Supported**: macOS (though code has platform checks)

### Technology Stack
- **GUI Framework**: Tkinter with ttkthemes for theming
- **Audio**: pygame.mixer for sound playback
- **System Tray**: pystray for tray icon integration
- **Telegram API**: telethon for Telegram integration
- **Packaging**: PyInstaller for executable creation

---

## Codebase Structure

```
smart-multi-timer/
├── src/                          # Main source directory
│   ├── components/               # Reusable UI components
│   │   └── timer.py             # Timer widget (350+ lines)
│   ├── tabs/                     # Application tab modules
│   │   ├── __init__.py
│   │   ├── habits_tab.py        # Habit tracking (1400+ lines)
│   │   ├── medication_tab.py    # Medication tracker (900+ lines)
│   │   ├── pushup_tracker_tab.py # Fitness tracker (450+ lines)
│   │   ├── telegram_tab.py      # Telegram integration (350+ lines)
│   │   └── todo_list_tab.py     # Todo list manager (700+ lines)
│   ├── utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── constants.py         # Resource paths and constants
│   │   ├── habit_reminder.py    # Background reminder daemon
│   │   ├── resource_path.py     # PyInstaller resource handling
│   │   ├── sound_utils.py       # Sound playback utilities
│   │   └── timer_notification.py # Timer completion notifications
│   ├── windows/                  # Window management
│   │   ├── __init__.py
│   │   ├── main_timer_window.py # Fullscreen timer display
│   │   └── main_window.py       # Main application window
│   ├── resources/                # Application resources
│   │   ├── images/              # Icons and images
│   │   │   ├── 1.jpeg
│   │   │   ├── 2.jpeg
│   │   │   └── tray_icon.ico
│   │   └── sounds/              # Sound files
│   │       └── habit.mp3
│   └── main.py                   # Application entry point
├── app.spec                      # PyInstaller build configuration
├── app.ico                       # Application icon
├── Makefile                      # Build automation
├── collect.sh                    # Source code collection script
├── fast-collect                  # Quick collection script
├── .gitignore                    # Git ignore patterns
└── README.md                     # User-facing documentation
```

### File Counts by Type
- **Tab modules**: 5 files (3,800+ lines)
- **Components**: 1 file (350+ lines)
- **Windows**: 2 files (800+ lines)
- **Utils**: 5 files (400+ lines)
- **Entry point**: 1 file (13 lines)

---

## Architecture & Design Patterns

### Overall Architecture
The application follows a **tab-based modular architecture** with centralized window management:

```
MainWindow (ThemedTk)
    ├── TabControl (ttk.Notebook)
    │   ├── TimerTab (embedded in main frame)
    │   ├── TodoListTab (ttk.Frame)
    │   ├── HabitsTab (ttk.Frame)
    │   ├── MedicationTab (ttk.Frame)
    │   ├── PushupTrackerTab (ttk.Frame)
    │   └── TelegramTab (ttk.Frame)
    └── SystemTray (pystray)
```

### Design Patterns Used

#### 1. **Component Pattern**
- **Location**: `components/timer.py`
- **Purpose**: Reusable timer widget with self-contained state
- **Pattern**: Each `Timer` instance manages its own:
  - State (running, paused, remaining_time)
  - UI elements (labels, buttons, spinboxes)
  - Callbacks (on_delete, sound_player)

#### 2. **Tab Module Pattern**
- **Location**: All files in `tabs/`
- **Pattern**: Each tab extends `ttk.Frame` and follows:
  ```python
  class SomeTab(ttk.Frame):
      def __init__(self, parent):
          super().__init__(parent)
          self.setup_ui()
          self.load_data()

      def setup_ui(self):
          # Build UI components

      def load_data(self):
          # Load from JSON

      def save_data(self):
          # Save to JSON
  ```

#### 3. **Resource Path Abstraction**
- **Location**: `utils/resource_path.py`
- **Purpose**: Handle both development and PyInstaller-packaged environments
- **Pattern**:
  ```python
  def get_resource_path(relative_path):
      try:
          base_path = sys._MEIPASS  # PyInstaller temp folder
      except:
          base_path = "src/"  # Development
      return os.path.join(base_path, "resources", relative_path)
  ```

#### 4. **Daemon Thread for Background Tasks**
- **Location**: `utils/habit_reminder.py`
- **Purpose**: Non-blocking periodic notifications
- **Pattern**:
  ```python
  class HabitReminder:
      def __init__(self, habits_tab):
          self.daemon_thread = threading.Thread(target=self.check_reminders, daemon=True)
          self.daemon_thread.start()
  ```

#### 5. **Platform-Specific Code Branching**
- **Pattern**: Extensive use of `platform.system()` checks:
  ```python
  if platform.system() == "Windows":
      import winsound
      # Windows-specific code
  elif platform.system() == "Linux":
      # Linux-specific code
  ```

#### 6. **State Persistence via JSON**
- **Pattern**: Each module independently manages its own JSON file
- **Files Created**:
  - `habits.json` - Habit data with intervals and reminders
  - `medications.json` - Medication schedules and intake records
  - `pushups.json` - Workout history
  - `timers.json` - Active timer configurations
  - `theme_settings.json` - UI theme preference
  - `telegram_config.json` - API credentials (security concern)

---

## Key Components

### 1. Timer Component (`components/timer.py`)

**Purpose**: Individual countdown timer with controls and progress display

**Key Features**:
- Preset durations (Pomodoro: 25+5, Focus: 52+17, custom)
- Emoji picker for descriptions
- Custom sound file selection
- Fullscreen mode with circular progress indicator
- Snooze functionality
- Thread-safe state management

**Important Methods**:
- `start_timer()` - Begins countdown in background thread
- `show_main_screen()` - Opens fullscreen timer window
- `play_notification_sound()` - Handles completion alerts
- `safe_update_main_window()` - Thread-safe UI updates

**State Variables**:
```python
self.remaining_time: int          # Seconds remaining
self.is_running: bool             # Timer active state
self.custom_sound: str            # Path to custom sound file
self.paused_time: int             # Paused duration for snooze
self.initial_time: int            # Original timer duration
```

### 2. Main Window (`windows/main_window.py`)

**Purpose**: Root application window with tab navigation and theme management

**Key Features**:
- Dynamic theme switching (20+ themes via ttkthemes)
- System tray integration (Windows/Linux)
- WSL detection and conditional tray icon
- Timer management (add/remove/persist)
- Graceful window hiding on close

**Important Methods**:
- `setup_ui()` - Builds tab notebook and timer section
- `create_tray_icon()` - Initializes system tray
- `change_theme()` - Applies new theme and saves preference
- `save_timers()` / `load_timers()` - Persist timer state
- `hide_window()` / `show_window()` - Minimize to tray

**Theming**:
- Inherits from `ThemedTk` (not standard `tk.Tk`)
- Saved preference in `theme_settings.json`
- Default theme: "ubuntu"

### 3. Habits Tab (`tabs/habits_tab.py`)

**Purpose**: Flexible habit tracking with custom intervals and reminders

**Key Features**:
- Time-period organization (Morning, Day, Evening, Night, Custom)
- Interval-based habits (daily, every N days)
- Active hours restriction (e.g., only 9am-6pm)
- Notification sounds and system tray alerts
- Habit groups for organization
- Statistics tracking with history
- Compact mode toggle

**Data Structure**:
```python
{
    "time_period": [
        {
            "name": "Drink water",
            "use_interval": True,
            "interval_minutes": 60,
            "reminder_enabled": True,
            "active_hours": {"start": "09:00", "end": "18:00"},
            "notify_sound": True,
            "history": {"2025-11-15": True},
            "group": "Health"
        }
    ]
}
```

**Background Process**:
- `HabitReminder` runs in daemon thread
- Checks every 10 seconds for due reminders
- Plays sound and shows toast notification
- Marks reminders as shown to prevent duplicates

### 4. Todo List Tab (`tabs/todo_list_tab.py`)

**Purpose**: Simple task management with filtering

**Key Features**:
- Inline task creation with Enter key
- Drag-n-drop reordering
- Status filters (All, Active, Completed)
- Task search functionality
- Checkboxes for completion
- Delete button per task

**Data Structure**:
```python
{
    "tasks": [
        {
            "text": "Complete project",
            "completed": False,
            "priority": "high"
        }
    ]
}
```

**Note**: Todo list does NOT persist to JSON - state is session-only

### 5. Medication Tab (`tabs/medication_tab.py`)

**Purpose**: Medication schedule tracking with intake logging

**Key Features**:
- Visual grid layout (medications × time slots)
- Checkboxes for intake confirmation
- "Mark All" / "Reset All" bulk operations
- Quick timer creation for medication reminders
- Toast notifications for schedule adherence

**Data Structure**:
```python
{
    "medications": ["Aspirin", "Vitamin D"],
    "times": ["Morning", "Evening"],
    "data": {
        "Aspirin": {
            "Morning": {"taken": True, "time": "08:30"}
        }
    }
}
```

### 6. Pushup Tracker Tab (`tabs/pushup_tracker_tab.py`)

**Purpose**: Daily pushup count tracking with presets

**Key Features**:
- Quick-add buttons (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
- Custom amount entry
- Daily total display
- History view with dates
- Reset daily count

**Data Structure**:
```python
{
    "2025-11-15": [
        {"count": 20, "time": "08:30:15"},
        {"count": 30, "time": "14:22:10"}
    ]
}
```

**Optimization**: `PushupStorage` class uses `_modified` flag to avoid unnecessary file writes

### 7. Telegram Tab (`tabs/telegram_tab.py`)

**Purpose**: Telegram client integration for message management

**Key Features**:
- API credentials configuration (api_id, api_hash)
- Phone number authentication
- Mark all messages as read
- Folder filtering (e.g., "Archive")
- Session persistence via `.session` file

**Security Concerns**:
- Credentials stored in plain text `telegram_config.json`
- Session files contain authentication tokens
- Both are in `.gitignore` but no encryption

---

## Development Workflow

### Running the Application

**Development Mode**:
```bash
cd smart-multi-timer
python src/main.py
```

**Dependencies** (inferred from imports):
```
tkinter (built-in)
ttkthemes
pygame
pillow (PIL)
pystray
telethon
```

**Note**: No `requirements.txt` exists in the repository despite `.gitignore` exception

### Building Executable

**Using PyInstaller**:
```bash
pyinstaller app.spec
```

**Output**: `dist/SmartMultiTimer.exe` (Windows) or `dist/SmartMultiTimer` (Linux)

**Build Configuration** (`app.spec`):
- Entry point: `src/main.py`
- Bundled data: `resources/images/*.ico`, `resources/images/*.jpeg`, `resources/sounds/*.mp3`
- Hidden imports: `pygame.mixer`
- Excludes: `numpy` (optimization)
- Console: False (GUI only)
- Icon: `app.ico`

**Using Makefile**:
```bash
make collect  # Runs collect.sh to generate project_source.txt
```

### Code Collection Script

**Purpose**: `collect.sh` aggregates all source files into `project_source.txt` for documentation

**Usage**:
```bash
bash collect.sh $(find src -type f -name "*.py")
# Or use the shortcut:
./fast-collect
```

**Output Format**:
```
Project Structure:
src/
    main.py
    ...

--------------------------------

File src/main.py

<file contents>

--------------------------------
```

---

## Code Conventions

### Python Style

**Formatting**:
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Generally <100 characters, but not strictly enforced
- **Imports**: Grouped (standard library, third-party, local)
- **Encoding**: UTF-8 with Russian language strings

**Naming Conventions**:
- **Classes**: PascalCase (`MainWindow`, `HabitsTab`)
- **Functions/Methods**: snake_case (`setup_ui`, `load_habits`)
- **Constants**: UPPER_SNAKE_CASE (`IMAGES_DIR`, `SOUNDS`)
- **Private Methods**: Leading underscore (`_modified`, `_update_display`)

**Docstrings**:
- **Minimal usage** - Most functions lack docstrings
- When present, uses Russian language
- Example:
  ```python
  def normalize_path(path):
      """Нормализует путь в зависимости от операционной системы"""
  ```

### UI Text Language

**All UI strings are in Russian**:
- Button labels: "Добавить", "Удалить", "Сохранить"
- Tab names: "Привычки", "Задачи", "Таймер"
- Messages: Error dialogs, notifications, tooltips

**When modifying UI**: Maintain Russian language consistency

### Import Organization

**Standard Pattern**:
```python
# Standard library
import json
import platform
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# Third-party
from pygame import mixer
from PIL import Image, ImageTk
from ttkthemes import ThemedTk

# Local imports
from components.timer import Timer
from utils.constants import IMAGES
```

### Error Handling Patterns

**Pattern 1: Silent Fallback** (Common in load operations)
```python
try:
    with open("settings.json", "r") as f:
        settings = json.load(f)
except:
    settings = {}  # Default
```

**Pattern 2: User Notification** (Common in save operations)
```python
try:
    with open("data.json", "w") as f:
        json.dump(data, f)
except Exception as e:
    messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")
```

**Pattern 3: TclError Protection** (Common in UI updates)
```python
try:
    self.label.configure(text=new_text)
except tk.TclError:
    pass  # Widget destroyed
```

### Threading Patterns

**Background Timers**:
```python
def start_timer(self):
    self.is_running = True
    threading.Thread(target=self.countdown, daemon=False).start()

def countdown(self):
    while self.remaining_time > 0 and self.is_running:
        time.sleep(1)
        self.remaining_time -= 1
        self.update_display()
```

**Daemon Threads** (for background services):
```python
self.daemon_thread = threading.Thread(target=self.worker, daemon=True)
self.daemon_thread.start()
```

### File I/O Patterns

**JSON Writing** (Standard pattern):
```python
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**JSON Reading** (Standard pattern):
```python
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
```

---

## Data Persistence

### Persistence Strategy

**Approach**: File-based JSON storage in application root directory
**Timing**: Save on every state change (no batching)
**Thread Safety**: ⚠️ NOT thread-safe (see Known Issues)

### Data Files

| File | Owner Module | Purpose | Frequency | Size Estimate |
|------|--------------|---------|-----------|---------------|
| `habits.json` | `habits_tab.py` | Habit definitions and history | High (15+/session) | 5-50 KB |
| `medications.json` | `medication_tab.py` | Medication grid data | Medium (6/session) | 2-10 KB |
| `pushups.json` | `pushup_tracker_tab.py` | Daily workout logs | Low (2/session) | 1-5 KB |
| `timers.json` | `main_window.py` | Active timer configs | Medium (3+/session) | 1-3 KB |
| `theme_settings.json` | `main_window.py` | UI theme preference | Very Low (1/change) | <1 KB |
| `telegram_config.json` | `telegram_tab.py` | API credentials | Very Low (1/setup) | <1 KB |

### Data Schemas

**habits.json**:
```json
{
    "time_periods": ["Утро", "День", "Вечер", "Ночь"],
    "custom_times": ["Workout"],
    "habits": {
        "Утро": [
            {
                "name": "Медитация",
                "use_interval": true,
                "interval_minutes": 1440,
                "last_check": "2025-11-15 08:30:00",
                "reminder_enabled": true,
                "active_hours_enabled": true,
                "active_hours": {"start": "06:00", "end": "10:00"},
                "notify_sound": true,
                "history": {
                    "2025-11-15": true,
                    "2025-11-14": false
                },
                "group": "Здоровье"
            }
        ]
    },
    "time_settings": {
        "Утро": {
            "quick_timer_minutes": 25
        }
    }
}
```

**timers.json**:
```json
[
    {
        "hours": 0,
        "minutes": 25,
        "seconds": 0,
        "description": "Pomodoro Session 🍅"
    }
]
```

**theme_settings.json**:
```json
{
    "theme": "ubuntu"
}
```

### Persistence Implementation

**Save Pattern** (habits_tab.py:1272):
```python
def save_habits(self):
    try:
        data = {
            "time_periods": self.all_times,
            "custom_times": self.custom_times,
            "habits": self.habits,
            "time_settings": self.time_settings
        }
        with open("habits.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")
```

**Load Pattern** (habits_tab.py:1229):
```python
def load_habits(self):
    try:
        with open("habits.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.all_times = data.get("time_periods", self.default_times)
            self.custom_times = data.get("custom_times", [])
            self.habits = data.get("habits", {})
            # ... restore state
    except FileNotFoundError:
        pass  # Use defaults
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить: {str(e)}")
```

**Optimized Pattern** (pushup_tracker_tab.py:32):
```python
class PushupStorage:
    def __init__(self):
        self._modified = False

    def save(self):
        if not self._modified:
            return  # Skip if no changes
        with open("pushups.json", "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        self._modified = False
```

### Backup Strategy

**Current State**: ❌ No backups, no recovery mechanism

**Recommendations**:
- Implement `.bak` file rotation before writes
- Add timestamp-based snapshots
- Validate JSON before overwriting

---

## Build & Distribution

### PyInstaller Configuration

**Spec File**: `app.spec`

**Key Settings**:
```python
datas=[
    ('src/resources/images/*.ico', 'resources/images'),
    ('src/resources/images/*.jpeg', 'resources/images'),
    ('src/resources/sounds/*.mp3', 'resources/sounds'),
]
hiddenimports=['pygame.mixer']
excludes=['numpy']
console=False  # No console window
icon='app.ico'
```

### Resource Handling

**Development vs Production**:

In development, resources are in `src/resources/`
In PyInstaller build, resources are in `sys._MEIPASS/resources/`

**Solution** (`utils/resource_path.py`):
```python
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp extraction dir
    except AttributeError:
        base_path = os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base_path, "resources", relative_path)
```

### Platform-Specific Build Notes

**Windows**:
- Icon: Uses `.ico` format
- System tray: Full support
- Sound: Can use `winsound` as fallback

**Linux**:
- Icon: Requires conversion from `.ico`
- WSL Detection: Disables tray icon if WSL detected
- Sound: Relies on pygame.mixer

---

## Known Issues & Technical Debt

### Critical Issues

#### 1. **Thread Safety in Data Persistence** 🔴
- **Location**: `habits_tab.py`, `HabitReminder`
- **Problem**: Daemon thread calls `save_habits()` while UI thread may also save
- **Risk**: Race condition → data corruption
- **Solution**: Add threading lock:
  ```python
  self._save_lock = threading.Lock()

  def save_habits(self):
      with self._save_lock:
          # ... save logic
  ```

#### 2. **Incomplete Code - Undefined Methods** 🔴
- **Location**: `habits_tab.py:519, 530, 535`
- **Problem**: Calls to `load_json()` and `save_json()` that don't exist
- **Impact**: Feature incomplete or broken
- **Solution**: Implement missing methods or remove dead code

#### 3. **Security: Plain Text Credentials** 🟡
- **Location**: `telegram_config.json`
- **Problem**: API credentials stored unencrypted
- **Risk**: Credential theft if file is accessed
- **Solution**: Use system keyring or at minimum base64 encoding

#### 4. **No Atomic File Writes** 🟡
- **Location**: All JSON save operations
- **Problem**: Process kill during write → corrupted files
- **Solution**: Write to temp file, then rename:
  ```python
  with open("data.json.tmp", "w") as f:
      json.dump(data, f)
  os.replace("data.json.tmp", "data.json")
  ```

### Design Issues

#### 5. **No Requirements File** 🟡
- **Problem**: No `requirements.txt` despite `.gitignore` exception
- **Impact**: Difficult for new developers to set up environment
- **Solution**: Create from imports:
  ```
  ttkthemes>=3.2.0
  pygame>=2.0.0
  Pillow>=9.0.0
  pystray>=0.19.0
  telethon>=1.24.0
  pyinstaller>=5.0.0
  ```

#### 6. **Todo List Doesn't Persist** 🟡
- **Location**: `todo_list_tab.py`
- **Problem**: Tasks lost on app close
- **Impact**: Poor user experience
- **Solution**: Add `save_tasks()` / `load_tasks()` like other tabs

#### 7. **Excessive File I/O** 🟢
- **Problem**: Save on every state change (15+ writes/session for habits)
- **Impact**: Disk wear, potential performance issues
- **Solution**: Debounce saves (e.g., 5-second delay) or save on app close

#### 8. **No Logging System** 🟢
- **Problem**: Errors silently caught or shown in messageboxes
- **Impact**: Difficult to debug user-reported issues
- **Solution**: Add `logging` module with file output

### Code Quality Issues

#### 9. **Minimal Documentation** 🟢
- **Problem**: Most functions lack docstrings
- **Impact**: Hard for new contributors to understand code
- **Solution**: Add docstrings to public methods

#### 10. **Global State in Tabs** 🟢
- **Problem**: Each tab directly writes to filesystem
- **Impact**: Tight coupling, hard to test
- **Solution**: Add data layer abstraction

---

## AI Assistant Guidelines

### When Working on This Codebase

#### Do:
1. **Maintain Russian UI text** - All user-facing strings must be in Russian
2. **Use UTF-8 encoding** - Always specify `encoding="utf-8"` in file operations
3. **Follow tab module pattern** - New features should extend `ttk.Frame`
4. **Test on both Windows and Linux** - Use `platform.system()` checks
5. **Update `app.spec`** - When adding resources, add to PyInstaller config
6. **Preserve threading patterns** - Match existing daemon thread usage
7. **Handle TclError** - UI updates in threads must catch `tk.TclError`
8. **Use resource_path helper** - Never hardcode paths to resources

#### Don't:
1. **Don't add English text** - Keep language consistency
2. **Don't remove platform checks** - They're necessary for cross-platform support
3. **Don't use `print()`** - Use `messagebox` or add logging
4. **Don't break PyInstaller** - Test that bundled app still works
5. **Don't ignore thread safety** - Add locks if modifying shared state
6. **Don't remove error handling** - Existing try/except blocks are intentional

### Common Tasks

#### Adding a New Tab
1. Create `src/tabs/my_feature_tab.py`:
   ```python
   import tkinter as tk
   from tkinter import ttk

   class MyFeatureTab(ttk.Frame):
       def __init__(self, parent):
           super().__init__(parent)
           self.setup_ui()
           self.load_data()

       def setup_ui(self):
           # Build UI
           pass

       def load_data(self):
           try:
               with open("my_feature.json", "r", encoding="utf-8") as f:
                   self.data = json.load(f)
           except FileNotFoundError:
               self.data = {}

       def save_data(self):
           with open("my_feature.json", "w", encoding="utf-8") as f:
               json.dump(self.data, f, ensure_ascii=False, indent=2)
   ```

2. Register in `main_window.py`:
   ```python
   from tabs.my_feature_tab import MyFeatureTab

   # In setup_ui():
   my_tab = MyFeatureTab(self.notebook)
   self.notebook.add(my_tab, text="Моя Функция")
   ```

3. Add to `.gitignore` if needed:
   ```
   my_feature.json
   ```

#### Adding a New Resource
1. Place file in `src/resources/images/` or `src/resources/sounds/`
2. Update `utils/constants.py`:
   ```python
   IMAGES = {
       "MY_IMAGE": os.path.join(IMAGES_DIR, "my_image.png"),
   }
   ```
3. Update `app.spec`:
   ```python
   datas=[
       ('src/resources/images/*.png', 'resources/images'),
   ]
   ```
4. Use in code:
   ```python
   from utils.constants import IMAGES
   img = Image.open(IMAGES["MY_IMAGE"])
   ```

#### Debugging PyInstaller Issues
1. Check resource paths:
   ```python
   print(get_resource_path("images/icon.ico"))
   ```
2. Run with console enabled:
   ```python
   # In app.spec:
   console=True
   ```
3. Check `sys._MEIPASS` contents:
   ```python
   import os
   print(os.listdir(sys._MEIPASS))
   ```

#### Adding Threading
1. For short tasks, use non-daemon threads:
   ```python
   threading.Thread(target=self.task, daemon=False).start()
   ```
2. For background services, use daemon threads:
   ```python
   threading.Thread(target=self.worker, daemon=True).start()
   ```
3. Always protect UI updates:
   ```python
   try:
       self.label.configure(text="Updated")
   except tk.TclError:
       pass  # Widget destroyed
   ```

### Testing Recommendations

**Manual Testing Checklist**:
- [ ] Theme switching works without errors
- [ ] System tray icon appears (Windows/Linux non-WSL)
- [ ] Timers persist across app restarts
- [ ] Habit reminders trigger at correct times
- [ ] Sounds play correctly
- [ ] Fullscreen timer displays properly
- [ ] PyInstaller build launches and all resources load

**Edge Cases to Test**:
- [ ] File corrupted/invalid JSON
- [ ] File deleted while app running
- [ ] Rapid theme switching
- [ ] Multiple timers completing simultaneously
- [ ] Long-running app (memory leaks?)

### Git Workflow

**Commit Message Format**:
- Use lowercase, descriptive messages
- Start with action verb: "added", "refactored", "fixed", "updated"
- Examples from history:
  ```
  added habit group functionality and improved ui
  refactored: standardized code formatting and improved readability
  fixed timer notification sound toggle
  ```

**Branch Strategy**:
- Development on `claude/` prefixed branches
- Main branch for stable releases
- Feature branches for major additions

---

## Appendix

### Frequently Modified Files

Based on commit history analysis:

1. **habits_tab.py** - Most active development
2. **timer.py** - Frequent enhancements (snooze, emoji, sounds)
3. **main_window.py** - Theme and tray icon changes
4. **medication_tab.py** - Recent additions
5. **pushup_tracker_tab.py** - Recent refactoring

### Performance Characteristics

- **Startup Time**: <2 seconds (depends on JSON load)
- **Memory Usage**: ~50-100 MB (Tkinter + pygame)
- **CPU Usage**: Minimal when idle, spikes during:
  - Timer countdown (1 update/second)
  - Habit reminder checks (every 10 seconds)
  - Theme switching (rebuilds UI)

### External Dependencies

**Required at Runtime**:
- Python 3.x (tested on 3.8+)
- X11/Wayland (Linux GUI)
- Windows API (for tray icon on Windows)

**Optional**:
- Internet connection (only for Telegram tab)
- Sound card (graceful degradation if missing)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-15 | 1.0 | Initial CLAUDE.md creation |

---

**End of CLAUDE.md**

For questions or updates, contact: [@teagamesen](https://t.me/teagamesen)
