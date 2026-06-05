from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from SAIN_OMEGA_CINEMA_ENGINE.engine.pipeline import SAINOmegaPipeline
from SAIN_OMEGA_CINEMA_ENGINE.storage.paths import SAINPaths


class SAINOmegaUI:
    """Four-screen director-first desktop MVP."""

    COMMANDS = ('Generate Start Frame', 'Generate End Frame', 'Continue', 'Regenerate', 'Send To Video')

    def __init__(self, paths: SAINPaths):
        self.paths = paths
        self.pipeline = SAINOmegaPipeline(paths)
        self.root = tk.Tk()
        self.root.title('OMEGA Film Studio V2 — Desktop MVP')
        self.root.geometry('1180x760')
        self.root.configure(bg='#07090f')

        self.storyboard_path: Path | None = None
        self.selected_shot_index = 0
        self.preview_images: list[tk.PhotoImage] = []
        self._build_layout()

    def _build_layout(self) -> None:
        shell = tk.Frame(self.root, bg='#07090f')
        shell.pack(fill='both', expand=True, padx=18, pady=18)

        self._build_project_dashboard(shell)
        body = tk.Frame(shell, bg='#07090f')
        body.pack(fill='both', expand=True, pady=(14, 0))
        self._build_director_chat(body)
        self._build_shot_workspace(body)
        self._build_export_screen(shell)

    def _build_project_dashboard(self, parent: tk.Widget) -> None:
        dashboard = tk.Frame(parent, bg='#0d1320', highlightbackground='#1f2d44', highlightthickness=1)
        dashboard.pack(fill='x')
        tk.Label(
            dashboard,
            text='OMEGA Film Studio V2',
            fg='#f4f7ff',
            bg='#0d1320',
            font=('Helvetica', 24, 'bold'),
        ).pack(side='left', padx=16, pady=16)
        tk.Button(
            dashboard,
            text='Upload Storyboard PDF / Images',
            command=self._pick_storyboard,
            bg='#2d5cff',
            fg='white',
            relief='flat',
            padx=14,
            pady=8,
        ).pack(side='right', padx=12)
        self.status = tk.Label(dashboard, text='Upload a storyboard to begin.', fg='#9eb3d9', bg='#0d1320')
        self.status.pack(side='right', padx=10)

    def _build_director_chat(self, parent: tk.Widget) -> None:
        chat = tk.Frame(parent, bg='#0b101a', highlightbackground='#1f2d44', highlightthickness=1, width=330)
        chat.pack(side='left', fill='y', padx=(0, 14))
        chat.pack_propagate(False)
        tk.Label(chat, text='Director Chat', fg='#f4f7ff', bg='#0b101a', font=('Helvetica', 16, 'bold')).pack(anchor='w', padx=14, pady=(14, 6))
        self.chat_log = tk.Text(chat, bg='#07090f', fg='#d8e6ff', height=15, relief='flat', wrap='word')
        self.chat_log.pack(fill='both', expand=True, padx=14, pady=6)
        self._chat('OMEGA', 'Upload storyboard. I will extract shots automatically.')
        for command in self.COMMANDS:
            tk.Button(
                chat,
                text=command,
                command=lambda cmd=command: self._director_command(cmd),
                bg='#182238',
                fg='white',
                activebackground='#2d5cff',
                relief='flat',
                pady=7,
            ).pack(fill='x', padx=14, pady=4)

    def _build_shot_workspace(self, parent: tk.Widget) -> None:
        workspace = tk.Frame(parent, bg='#0b101a', highlightbackground='#1f2d44', highlightthickness=1)
        workspace.pack(side='left', fill='both', expand=True)
        top = tk.Frame(workspace, bg='#0b101a')
        top.pack(fill='x', padx=14, pady=12)
        tk.Label(top, text='Shot Workspace', fg='#f4f7ff', bg='#0b101a', font=('Helvetica', 16, 'bold')).pack(side='left')
        self.shot_list = tk.Listbox(top, bg='#07090f', fg='#d8e6ff', height=5, exportselection=False, relief='flat')
        self.shot_list.pack(side='right', fill='x', expand=True, padx=(18, 0))
        self.shot_list.bind('<<ListboxSelect>>', self._select_shot)

        strip = tk.Frame(workspace, bg='#0b101a')
        strip.pack(fill='both', expand=True, padx=14, pady=(0, 14))
        self.preview_labels: dict[str, tk.Label] = {}
        for title in ('Storyboard Reference', 'Start Frame', 'End Frame'):
            cell = tk.Frame(strip, bg='#111827', highlightbackground='#263854', highlightthickness=1)
            cell.pack(side='left', fill='both', expand=True, padx=6)
            tk.Label(cell, text=title, fg='#9eb3d9', bg='#111827', font=('Helvetica', 11, 'bold')).pack(pady=(10, 4))
            label = tk.Label(cell, text='Not generated', fg='#52647f', bg='#111827')
            label.pack(fill='both', expand=True, padx=10, pady=10)
            self.preview_labels[title] = label

    def _build_export_screen(self, parent: tk.Widget) -> None:
        export = tk.Frame(parent, bg='#0d1320', highlightbackground='#1f2d44', highlightthickness=1)
        export.pack(fill='x', pady=(14, 0))
        tk.Label(export, text='Export Screen', fg='#f4f7ff', bg='#0d1320', font=('Helvetica', 15, 'bold')).pack(side='left', padx=14, pady=12)
        tk.Button(export, text='Export Film', command=self._export_film, bg='#13a36f', fg='white', relief='flat', padx=18, pady=8).pack(side='right', padx=12)
        self.export_status = tk.Label(export, text='Final film will export to project/Final_Film.mp4', fg='#9eb3d9', bg='#0d1320')
        self.export_status.pack(side='right', padx=10)

    def _pick_storyboard(self) -> None:
        selected = filedialog.askopenfilenames(
            title='Select Storyboard PDF or Images',
            filetypes=[('Storyboards', '*.pdf *.png *.jpg *.jpeg'), ('PDF', '*.pdf'), ('Images', '*.png *.jpg *.jpeg')],
        )
        if not selected:
            return
        try:
            paths = [Path(p) for p in selected]
            self.storyboard_path = paths[0]
            source = paths if len(paths) > 1 else paths[0]
            result = self.pipeline.intake_storyboard(source)
            self._populate_shot_list(result['shots'])
            self.status.configure(text=f"{len(result['shots'])} shots extracted automatically.")
            self._chat('OMEGA', f"Storyboard analyzed. {len(result['shots'])} shots are ready.")
            self._refresh_workspace()
        except Exception as exc:
            messagebox.showerror('Storyboard Intake Failed', str(exc))

    def _director_command(self, command: str) -> None:
        if not self.pipeline.shot_payloads:
            messagebox.showwarning('Missing Storyboard', 'Upload a storyboard first.')
            return
        try:
            self._chat('Director', command)
            if command in {'Generate Start Frame', 'Generate End Frame'}:
                self.pipeline.generate_frames(self.selected_shot_index)
                self._chat('OMEGA', 'Generated start and end frames for the selected shot.')
            elif command == 'Regenerate':
                self.pipeline.generate_frames(self.selected_shot_index)
                self._chat('OMEGA', 'Regenerated selected shot frames.')
            elif command == 'Send To Video':
                self.pipeline.send_to_video(self.selected_shot_index)
                self._chat('OMEGA', 'Selected shot sent to the video provider.')
            elif command == 'Continue':
                self._chat('OMEGA', self.pipeline.continue_workflow())
            self._refresh_workspace()
        except Exception as exc:
            messagebox.showerror('OMEGA Workflow Failed', str(exc))

    def _export_film(self) -> None:
        if not self.pipeline.shot_payloads:
            messagebox.showwarning('Missing Storyboard', 'Upload a storyboard first.')
            return
        try:
            final_path = self.pipeline.export_film()
            self.export_status.configure(text=f'Exported: {final_path}')
            self._chat('OMEGA', f'Final MP4 ready: {final_path}')
        except Exception as exc:
            messagebox.showerror('Export Failed', str(exc))

    def _populate_shot_list(self, shots: list[dict[str, object]]) -> None:
        self.shot_list.delete(0, 'end')
        for shot in shots:
            label = str(shot['shot_id']).replace('shot', 'Shot ')
            self.shot_list.insert('end', label)
        if shots:
            self.shot_list.selection_set(0)
            self.selected_shot_index = 0

    def _select_shot(self, _event: tk.Event) -> None:
        selection = self.shot_list.curselection()
        if selection:
            self.selected_shot_index = int(selection[0])
            self._refresh_workspace()

    def _refresh_workspace(self) -> None:
        if not self.pipeline.shot_payloads:
            return
        shot = self.pipeline.shot_payloads[self.selected_shot_index]
        self.preview_images.clear()
        mapping = {
            'Storyboard Reference': Path(str(shot['storyboard_panel'])),
            'Start Frame': Path(str(shot['start_frame'])),
            'End Frame': Path(str(shot['end_frame'])),
        }
        for title, path in mapping.items():
            self._set_preview(title, path)

    def _set_preview(self, title: str, path: Path) -> None:
        label = self.preview_labels[title]
        if not path.exists():
            label.configure(text='Not generated', image='')
            return
        try:
            image = tk.PhotoImage(file=str(path))
            self.preview_images.append(image)
            label.configure(image=image, text='')
        except tk.TclError:
            label.configure(text=str(path), image='')

    def _chat(self, speaker: str, message: str) -> None:
        self.chat_log.insert('end', f'{speaker}: {message}\n')
        self.chat_log.see('end')

    def launch(self) -> None:
        self.root.mainloop()
