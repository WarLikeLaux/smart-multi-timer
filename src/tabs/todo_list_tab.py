import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk


class TodoListTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tasks = []
        self.current_filter = "all"
        self.setup_styles()
        self.setup_ui()
        self.regular_font = tkFont.Font(family="Segoe UI", size=11)
        self.completed_font = tkFont.Font(
            family="Segoe UI", size=11, slant="italic", overstrike=1
        )

    def setup_styles(self):
        style = ttk.Style()

        style.configure("Todo.TFrame", background="#ffffff")

        style.configure("TaskItem.TFrame", background="#ffffff", padding=5)
        style.configure("TaskItemHover.TFrame", background="#f2f2f2", padding=5)

        style.configure("TodoEntry.TEntry", padding=10, fieldbackground="#f5f5f5")

        style.configure("Todo.TCheckbutton", background="#ffffff")

        style.configure("Accent.TButton", padding=5, font=("Segoe UI", 10, "bold"))
        style.configure("Filter.TButton", font=("Segoe UI", 10))
        style.configure("Todo.TButton", relief="flat", background="#ffffff")
        style.configure("Arrow.TButton", width=2, relief="flat", background="#ffffff")

    def setup_ui(self):
        self.configure(style="Todo.TFrame")
        main_container = ttk.Frame(self, style="Todo.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_container, style="Todo.TFrame")
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(
            header,
            text="Задачи",
            font=("Segoe UI", 20),
            foreground="#2c2c2c",
            background="#ffffff",
        ).pack(side=tk.LEFT)

        filter_frame = ttk.Frame(main_container, style="Todo.TFrame")
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        ttk.Button(
            filter_frame,
            text="Все",
            style="Filter.TButton",
            command=lambda: self.apply_filter("all"),
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Активные",
            style="Filter.TButton",
            command=lambda: self.apply_filter("active"),
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Выполненные",
            style="Filter.TButton",
            command=lambda: self.apply_filter("completed"),
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Очистить выполненные",
            style="Filter.TButton",
            command=self.clear_completed,
            takefocus=0,
        ).pack(side=tk.RIGHT, padx=5)

        search_frame = ttk.Frame(main_container, style="Todo.TFrame")
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        ttk.Label(
            search_frame,
            text="Поиск:",
            font=("Segoe UI", 10),
            background="#ffffff",
        ).pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(
            search_frame, font=("Segoe UI", 11), style="TodoEntry.TEntry"
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        input_frame = ttk.Frame(main_container, style="Todo.TFrame")
        input_frame.pack(fill=tk.X, padx=20, pady=5)
        self.task_entry = ttk.Entry(
            input_frame, font=("Segoe UI", 11), style="TodoEntry.TEntry"
        )
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.task_entry.bind("<FocusIn>", self.on_entry_click)
        self.task_entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        self.placeholder_text = "+ Добавить задачу"
        self.task_entry.insert(0, self.placeholder_text)
        self.task_entry.config(foreground="#9e9e9e")
        ttk.Button(
            input_frame, text="Добавить", style="Accent.TButton", command=self.add_task
        ).pack(side=tk.LEFT, padx=5)

        self.tasks_container = ttk.Frame(main_container, style="Todo.TFrame")
        self.tasks_container.pack(fill=tk.BOTH, expand=True, padx=20)
        self.canvas = tk.Canvas(
            self.tasks_container, background="#ffffff", bd=0, highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.tasks_container, orient="vertical", command=self.canvas.yview
        )
        self.tasks_frame = ttk.Frame(self.canvas, style="Todo.TFrame")
        self.tasks_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.tasks_frame, anchor="nw"
        )
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_entry_click(self, event):
        if self.task_entry.get() == self.placeholder_text:
            self.task_entry.delete(0, tk.END)
            self.task_entry.config(foreground="#2c2c2c")

    def on_entry_focus_out(self, event):
        if not self.task_entry.get().strip():
            self.task_entry.insert(0, self.placeholder_text)
            self.task_entry.config(foreground="#9e9e9e")

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text and task_text != self.placeholder_text:
            task_frame = ttk.Frame(self.tasks_frame, style="TaskItem.TFrame")
            task_frame.pack(fill=tk.X, pady=3)
            var = tk.BooleanVar()
            task_frame.var = var

            def update_task_style():
                if var.get():
                    label.configure(font=self.completed_font, foreground="#9e9e9e")
                else:
                    label.configure(font=self.regular_font, foreground="#2c2c2c")
                self.apply_filter(self.current_filter)

            check = ttk.Checkbutton(
                task_frame,
                variable=var,
                command=update_task_style,
                style="Todo.TCheckbutton",
                takefocus=0,
            )
            check.pack(side=tk.LEFT, padx=(5, 10))

            label = ttk.Label(
                task_frame, text=task_text, style="Task.TLabel", background="#ffffff"
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            label.bind("<Double-Button-1>", lambda e: self.edit_task(label))

            controls_frame = ttk.Frame(task_frame, style="Todo.TFrame")
            controls_frame.pack(side=tk.RIGHT, padx=5)

            up_btn = ttk.Button(
                controls_frame,
                text="↑",
                style="Arrow.TButton",
                takefocus=0,
                command=lambda: self.move_task_up(task_frame),
            )
            up_btn.pack(side=tk.LEFT, padx=2)

            down_btn = ttk.Button(
                controls_frame,
                text="↓",
                style="Arrow.TButton",
                takefocus=0,
                command=lambda: self.move_task_down(task_frame),
            )
            down_btn.pack(side=tk.LEFT, padx=2)

            delete_btn = ttk.Button(
                controls_frame,
                text="✕",
                command=lambda: self.delete_task(task_frame),
                takefocus=0,
                style="Todo.TButton",
            )
            delete_btn.pack(side=tk.LEFT, padx=2)

            def on_enter(e):
                task_frame.configure(style="TaskItemHover.TFrame")
                controls_frame.pack(side=tk.RIGHT, padx=5)

            def on_leave(e):
                task_frame.configure(style="TaskItem.TFrame")
                if not delete_btn.winfo_containing(e.x_root, e.y_root):
                    controls_frame.pack_forget()

            task_frame.bind("<Enter>", on_enter)
            task_frame.bind("<Leave>", on_leave)

            self.tasks.append(task_frame)
            self.task_entry.delete(0, tk.END)
            self.on_entry_focus_out(None)
            self.canvas.yview_moveto(1.0)
            self.apply_filter(self.current_filter)

    def delete_task(self, task_frame):
        if task_frame in self.tasks:
            self.tasks.remove(task_frame)
        task_frame.destroy()

    def edit_task(self, label):
        task_frame = label.master
        old_text = label.cget("text")
        edit_entry = ttk.Entry(
            task_frame, font=("Segoe UI", 11), style="TodoEntry.TEntry"
        )
        edit_entry.insert(0, old_text)
        edit_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        label.pack_forget()
        edit_entry.focus_set()

        def save_edit(event=None):
            new_text = edit_entry.get().strip()
            if new_text:
                label.config(text=new_text)
            edit_entry.destroy()
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: save_edit())

    def move_task_up(self, task_frame):
        index = self.tasks.index(task_frame)
        if index > 0:
            self.tasks[index], self.tasks[index - 1] = (
                self.tasks[index - 1],
                self.tasks[index],
            )
            for task in self.tasks:
                task.pack_forget()
                task.pack(fill=tk.X, pady=3)

    def move_task_down(self, task_frame):
        index = self.tasks.index(task_frame)
        if index < len(self.tasks) - 1:
            self.tasks[index], self.tasks[index + 1] = (
                self.tasks[index + 1],
                self.tasks[index],
            )
            for task in self.tasks:
                task.pack_forget()
                task.pack(fill=tk.X, pady=3)

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        for task in self.tasks:
            var = task.var

            task_label = None
            for child in task.winfo_children():
                if isinstance(child, ttk.Label):
                    task_label = child
                    break
            task_text = task_label.cget("text") if task_label else ""
            search_query = self.search_entry.get().strip().lower()
            matches_search = search_query in task_text.lower() if search_query else True

            if filter_type == "all":
                if matches_search:
                    task.pack(fill=tk.X, pady=3)
                else:
                    task.pack_forget()
            elif filter_type == "active":
                if not var.get() and matches_search:
                    task.pack(fill=tk.X, pady=3)
                else:
                    task.pack_forget()
            elif filter_type == "completed":
                if var.get() and matches_search:
                    task.pack(fill=tk.X, pady=3)
                else:
                    task.pack_forget()

    def on_search(self, event):
        self.apply_filter(self.current_filter)

    def clear_completed(self):
        for task in self.tasks[:]:
            if task.var.get():
                self.delete_task(task)
