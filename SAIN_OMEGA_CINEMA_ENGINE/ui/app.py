from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from SAIN_OMEGA_CINEMA_ENGINE.engine.pipeline import SAINOmegaPipeline
from SAIN_OMEGA_CINEMA_ENGINE.storage.paths import SAINPaths


class SAINOmegaUI:
    def __init__(self, paths: SAINPaths):
        self.paths = paths
        self.pipeline = SAINOmegaPipeline(paths)
        self.root = tk.Tk()
        self.root.title('S.A.I.N OMEGA CINEMA ENGINE')
        self.root.geometry('980x620')
        self.root.configure(bg='#0a0d12')

        self.storyboard_path: Path | None = None
        self._build_layout()

    def _build_layout(self) -> None:
        title = tk.Label(
            self.root,
            text='S.A.I.N OMEGA CINEMA ENGINE',
            fg='#c7d9ff',
            bg='#0a0d12',
            font=('Helvetica', 22, 'bold'),
        )
        title.pack(pady=18)

        self.story_input = tk.Text(self.root, height=8, bg='#101622', fg='#d8e6ff', insertbackground='white')
        self.story_input.insert('1.0', 'Enter story intent, emotion, and cinematic direction...')
        self.story_input.pack(fill='x', padx=24)

        controls = tk.Frame(self.root, bg='#0a0d12')
        controls.pack(fill='x', padx=24, pady=14)

        tk.Button(controls, text='Upload Storyboard Sheet', command=self._pick_storyboard, bg='#24324d', fg='white').pack(side='left', padx=6)
        tk.Button(controls, text='Run Cinematic Workflow', command=self._run_pipeline, bg='#2d5cff', fg='white').pack(side='left', padx=6)

        self.log = tk.Text(self.root, bg='#090c14', fg='#8ed9c7', height=22)
        self.log.pack(fill='both', expand=True, padx=24, pady=8)

    def _pick_storyboard(self) -> None:
        selected = filedialog.askopenfilename(
            title='Select Storyboard Sheet',
            filetypes=[('Images', '*.png *.jpg *.jpeg *.webp')],
        )
        if selected:
            self.storyboard_path = Path(selected)
            self._append_log(f'Loaded storyboard sheet: {self.storyboard_path}')

    def _run_pipeline(self) -> None:
        if not self.storyboard_path:
            messagebox.showwarning('Missing Storyboard', 'Please upload a storyboard sheet first.')
            return

        story = self.story_input.get('1.0', 'end').strip()
        result = self.pipeline.run(self.storyboard_path, story)
        self._append_log('Workflow complete ✅')
        self._append_log(f"Panels extracted: {len(result['panels'])}")
        self._append_log(f"Shot packets: {len(result['shot_packets'])}")
        if result['shot_packets']:
            self._append_log(f"First packet: {result['shot_packets'][0]}")
        self._append_log(f"Frame candidates: {len(result['candidates'])}")
        self._append_log(f"Sequence frames: {len(result['sequence'])}")
        self._append_log(f"Video assembled: {result['video']}")
        self._append_log(f"Continuity saved: {result['continuity']}")

    def _append_log(self, msg: str) -> None:
        self.log.insert('end', msg + '\n')
        self.log.see('end')

    def launch(self) -> None:
        self.root.mainloop()
