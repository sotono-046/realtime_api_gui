import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from utils.logger import get_logger

logger = get_logger()

class PerformerSettingsWindow:
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback  # 設定変更時に呼び出すコールバック
        
        # 設定ファイルのパス
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'prompts.json'
        )
        
        # 演者設定データ
        self.performers = {}
        self.current_performer = None
        
        # ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("演者設定")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.init_ui()
        self.load_performers()
        
    def init_ui(self):
        """UIを初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左右分割フレーム
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左側フレーム：演者リスト
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # 演者リストラベル
        ttk.Label(left_frame, text="演者一覧:").pack(anchor=tk.W, pady=(0, 5))
        
        # 演者リスト
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.performer_listbox = tk.Listbox(list_frame)
        self.performer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.performer_listbox.bind('<<ListboxSelect>>', self.on_performer_selected)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.performer_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.performer_listbox.yview)
        
        # 演者追加・削除ボタン
        list_button_frame = ttk.Frame(left_frame)
        list_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.add_btn = ttk.Button(list_button_frame, text="追加", command=self.add_performer)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(list_button_frame, text="削除", command=self.delete_performer)
        self.delete_btn.pack(side=tk.LEFT)
        
        # 右側フレーム：演者詳細設定
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)
        
        # 演者名
        ttk.Label(right_frame, text="演者名:").pack(anchor=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(right_frame, textvariable=self.name_var)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        self.name_var.trace('w', self.on_setting_changed)
        
        # システムプロンプト
        ttk.Label(right_frame, text="システムプロンプト:").pack(anchor=tk.W, pady=(0, 5))
        self.prompt_text = scrolledtext.ScrolledText(right_frame, height=8, wrap=tk.WORD)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.prompt_text.bind('<KeyRelease>', self.on_setting_changed)
        
        # 音声設定フレーム
        voice_frame = ttk.Frame(right_frame)
        voice_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 音声タイプ
        ttk.Label(voice_frame, text="音声タイプ:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, state="readonly")
        self.voice_combo['values'] = ("alloy", "echo", "fable", "onyx", "nova", "shimmer", "ballad", "sage")
        self.voice_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.voice_var.trace('w', self.on_setting_changed)
        
        # 速度
        ttk.Label(voice_frame, text="速度:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.speed_var = tk.DoubleVar()
        self.speed_spin = ttk.Spinbox(voice_frame, from_=0.5, to=2.0, increment=0.1, 
                                      textvariable=self.speed_var, width=10)
        self.speed_spin.grid(row=0, column=3, sticky=tk.W)
        self.speed_var.trace('w', self.on_setting_changed)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.save_btn = ttk.Button(button_frame, text="保存", command=self.save_settings)
        self.save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.cancel_btn = ttk.Button(button_frame, text="キャンセル", command=self.window.destroy)
        self.cancel_btn.pack(side=tk.RIGHT)
        
        # 初期状態では詳細設定を無効化
        self.set_detail_enabled(False)
        
    def set_detail_enabled(self, enabled):
        """詳細設定の有効/無効を切り替え"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.name_entry.config(state=state)
        self.prompt_text.config(state=state)
        self.voice_combo.config(state="readonly" if enabled else tk.DISABLED)
        self.speed_spin.config(state=state)
        
    def load_performers(self):
        """演者設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.performers = json.load(f)
                    logger.info("演者設定を読み込みました")
            else:
                self.performers = {}
                logger.warning("設定ファイルが見つかりません")
                
            self.update_performer_list()
            
        except Exception as e:
            logger.error(f"演者設定の読み込みに失敗: {e}")
            messagebox.showerror("エラー", f"設定ファイルの読み込みに失敗しました:\n{e}")
            
    def update_performer_list(self):
        """演者リストを更新"""
        self.performer_listbox.delete(0, tk.END)
        for name in self.performers.keys():
            self.performer_listbox.insert(tk.END, name)
            
    def on_performer_selected(self, event):
        """演者が選択された時の処理"""
        selection = self.performer_listbox.curselection()
        if not selection:
            self.current_performer = None
            self.set_detail_enabled(False)
            return
            
        performer_name = self.performer_listbox.get(selection[0])
        self.current_performer = performer_name
        
        if performer_name in self.performers:
            performer_data = self.performers[performer_name]
            
            # 詳細設定を有効化
            self.set_detail_enabled(True)
            
            # フィールドを更新（イベントを一時的に無効化）
            self.name_var.set(performer_name)
            
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, performer_data.get('system_prompt', ''))
            
            self.voice_var.set(performer_data.get('voice', 'alloy'))
            self.speed_var.set(performer_data.get('speed', 1.0))
            
    def on_setting_changed(self, *args):
        """設定が変更された時の処理"""
        if self.current_performer is None:
            return
            
        # 現在の設定を更新
        old_name = self.current_performer
        new_name = self.name_var.get().strip()
        
        if not new_name:
            return
            
        # 演者名が変更された場合
        if old_name != new_name:
            if new_name in self.performers and new_name != old_name:
                messagebox.showwarning("警告", "同じ名前の演者が既に存在します。")
                self.name_var.set(old_name)
                return
                
            # 古い名前のデータを削除し、新しい名前で追加
            performer_data = self.performers.pop(old_name)
            self.performers[new_name] = performer_data
            self.current_performer = new_name
            
            # リストを更新
            self.update_performer_list()
            
            # 新しい名前のアイテムを選択
            performers = list(self.performers.keys())
            if new_name in performers:
                index = performers.index(new_name)
                self.performer_listbox.selection_set(index)
        
        # 設定を更新
        if self.current_performer in self.performers:
            self.performers[self.current_performer].update({
                'system_prompt': self.prompt_text.get(1.0, tk.END).strip(),
                'voice': self.voice_var.get(),
                'speed': self.speed_var.get()
            })
            
    def add_performer(self):
        """新しい演者を追加"""
        name = f"新しい演者{len(self.performers) + 1}"
        counter = 1
        while name in self.performers:
            counter += 1
            name = f"新しい演者{counter}"
            
        # デフォルト設定で新しい演者を追加
        self.performers[name] = {
            'system_prompt': 'あなたは声優です。かぎ括弧で囲まれた文章を自然に読み上げてください。',
            'voice': 'alloy',
            'speed': 1.0
        }
        
        self.update_performer_list()
        
        # 新しく追加された演者を選択
        performers = list(self.performers.keys())
        if name in performers:
            index = performers.index(name)
            self.performer_listbox.selection_set(index)
            self.on_performer_selected(None)
                
    def delete_performer(self):
        """選択された演者を削除"""
        if self.current_performer is None:
            return
            
        result = messagebox.askyesno("確認", f"演者「{self.current_performer}」を削除しますか？")
        
        if result:
            del self.performers[self.current_performer]
            self.update_performer_list()
            self.current_performer = None
            self.set_detail_enabled(False)
            
    def save_settings(self):
        """設定を保存"""
        try:
            # 設定ファイルのディレクトリが存在しない場合は作成
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            # JSONファイルに保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.performers, f, ensure_ascii=False, indent=4)
                
            logger.info("演者設定を保存しました")
            messagebox.showinfo("保存完了", "演者設定を保存しました。")
            
            # コールバックを呼び出し
            if self.callback:
                self.callback()
                
            self.window.destroy()
            
        except Exception as e:
            logger.error(f"設定の保存に失敗: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{e}")