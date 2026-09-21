import os

class RecentFilesManager:
    """
    [MS17-B6] 最近使ったファイルの履歴管理ロジックを集約するクラス。
    """
    def __init__(self, ui_state, max_history: int = 5):
        self.ui_state = ui_state
        self.max_history = max_history

    def get_valid_audio_files(self) -> list[str]:
        """
        存在する音声ファイルパスのみを返す。
        """
        valid_files = []
        for p in self.ui_state.recent_audio_files:
            if os.path.exists(p):
                valid_files.append(p)
                
        # 履歴が拡張されたばかりで recent_audio_files が空なら、互換のために recent_wav_files を確認
        if not valid_files and getattr(self.ui_state, 'recent_wav_files', []):
            for p in self.ui_state.recent_wav_files:
                if os.path.exists(p):
                    valid_files.append(p)
        
        self.ui_state.recent_audio_files = valid_files[:self.max_history]
        return self.ui_state.recent_audio_files

    def get_valid_text_files(self) -> list[str]:
        """
        存在するテキストファイルパスのみを返す。
        """
        valid_files = []
        for p in self.ui_state.recent_text_files:
            if os.path.exists(p):
                valid_files.append(p)
                
        self.ui_state.recent_text_files = valid_files[:self.max_history]
        return self.ui_state.recent_text_files
