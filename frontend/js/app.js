/**
 * 音声読み上げアプリケーションのメインクラス
 */
class TTSApp {
    constructor() {
        this.currentFileId = null;
        this.currentAudioUrl = null;
        this.isPlaying = false;
        this.availableVoices = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadVoices();
        this.checkServerConnection();
    }

    /**
     * DOM要素を初期化
     */
    initializeElements() {
        this.form = document.getElementById('ttsForm');
        this.textInput = document.getElementById('textInput');
        this.charCount = document.getElementById('charCount');
        this.voiceSelector = document.getElementById('voiceSelector');
        this.generateBtn = document.getElementById('generateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.audioElement = document.getElementById('audioElement');
        this.playBtn = document.getElementById('playBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.errorMessage = document.getElementById('errorMessage');
    }

    /**
     * イベントリスナーを設定
     */
    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.textInput.addEventListener('input', () => this.updateCharCount());
        this.clearBtn.addEventListener('click', () => this.clearForm());
        this.playBtn.addEventListener('click', () => this.togglePlayback());
        this.downloadBtn.addEventListener('click', () => this.downloadAudio());
        this.audioElement.addEventListener('ended', () => this.onAudioEnded());
        this.audioElement.addEventListener('loadeddata', () => this.onAudioLoaded());
        this.audioElement.addEventListener('error', () => this.onAudioError());
    }

    /**
     * サーバー接続をチェック
     */
    async checkServerConnection() {
        const isConnected = await window.ttsApi.testConnection();
        if (!isConnected) {
            this.showError('サーバーに接続できません。バックエンドサーバーが起動しているか確認してください。');
        }
    }

    /**
     * 利用可能な音声を読み込み
     */
    async loadVoices() {
        try {
            const result = await window.ttsApi.getAvailableVoices();
            
            if (result.success) {
                this.availableVoices = result.data.voices;
                this.renderVoiceSelector(result.data.voices, result.data.default);
            } else {
                console.warn('Failed to load voices, using fallback');
                this.renderVoiceSelector(result.data.voices, result.data.default);
            }
        } catch (error) {
            console.error('Error loading voices:', error);
            this.showError('音声リストの読み込みに失敗しました');
        }
    }

    /**
     * 音声選択UIを描画
     */
    renderVoiceSelector(voices, defaultVoice = 'Zephyr') {
        this.voiceSelector.innerHTML = '';
        
        voices.forEach((voice, index) => {
            const isDefault = voice.name === defaultVoice;
            const voiceOption = document.createElement('div');
            voiceOption.className = 'voice-option';
            
            voiceOption.innerHTML = `
                <input type="radio" 
                       id="voice_${voice.name}" 
                       name="voice" 
                       value="${voice.name}" 
                       ${isDefault ? 'checked' : ''}>
                <label for="voice_${voice.name}" class="voice-label">
                    <div class="voice-name">${voice.name}</div>
                    <div class="voice-desc">${voice.description}</div>
                </label>
            `;
            
            this.voiceSelector.appendChild(voiceOption);
        });
    }

    /**
     * 文字数カウントを更新
     */
    updateCharCount() {
        const count = this.textInput.value.length;
        this.charCount.textContent = count;
        
        // 文字数に応じて色を変更
        if (count > 800) {
            this.charCount.style.color = '#d32f2f';
        } else if (count > 600) {
            this.charCount.style.color = '#f57c00';
        } else {
            this.charCount.style.color = '#888';
        }

        // 生成ボタンの有効/無効を制御
        this.generateBtn.disabled = count === 0 || count > 1000;
    }

    /**
     * フォーム送信を処理
     */
    async handleSubmit(e) {
        e.preventDefault();
        
        const text = this.textInput.value.trim();
        if (!text) {
            this.showError('テキストを入力してください。');
            return;
        }

        const selectedVoice = document.querySelector('input[name="voice"]:checked')?.value || 'Zephyr';

        try {
            this.showLoading(true);
            this.hideError();
            this.hideAudioPlayer();
            
            // 音声生成をリクエスト
            const generateResult = await window.ttsApi.generateSpeech(text, selectedVoice);
            
            if (!generateResult.success) {
                throw new Error(generateResult.error);
            }

            this.currentFileId = generateResult.data.file_id;
            
            // 音声ファイルをダウンロード
            const downloadResult = await window.ttsApi.downloadAudio(this.currentFileId);
            
            if (!downloadResult.success) {
                throw new Error(downloadResult.error);
            }

            // 音声プレーヤーを表示
            this.displayAudioPlayer(downloadResult.data.url, downloadResult.data.blob);
            
        } catch (error) {
            console.error('Error in handleSubmit:', error);
            this.showError(error.message || '音声生成中にエラーが発生しました。');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 音声プレーヤーを表示
     */
    displayAudioPlayer(audioUrl, audioBlob) {
        // 既存のURLをクリーンアップ
        if (this.currentAudioUrl) {
            URL.revokeObjectURL(this.currentAudioUrl);
        }
        
        this.currentAudioUrl = audioUrl;
        this.currentAudioBlob = audioBlob;
        this.audioElement.src = audioUrl;
        this.audioPlayer.classList.add('show');
        this.resetPlayButton();
    }

    /**
     * 音声再生を切り替え
     */
    togglePlayback() {
        if (this.isPlaying) {
            this.audioElement.pause();
        } else {
            this.audioElement.play().catch(error => {
                console.error('Playback failed:', error);
                this.showError('音声の再生に失敗しました。');
            });
        }
    }

    /**
     * 音声再生終了時の処理
     */
    onAudioEnded() {
        this.isPlaying = false;
        this.playBtn.textContent = '▶️';
    }

    /**
     * 音声データ読み込み完了時の処理
     */
    onAudioLoaded() {
        this.playBtn.disabled = false;
        this.downloadBtn.disabled = false;
        
        // 音声再生状態を監視
        this.audioElement.addEventListener('play', () => {
            this.isPlaying = true;
            this.playBtn.textContent = '⏸️';
        });
        
        this.audioElement.addEventListener('pause', () => {
            this.isPlaying = false;
            this.playBtn.textContent = '▶️';
        });
    }

    /**
     * 音声エラー時の処理
     */
    onAudioError() {
        console.error('Audio playback error');
        this.showError('音声ファイルの再生中にエラーが発生しました。');
        this.resetPlayButton();
    }

    /**
     * 音声ファイルをダウンロード
     */
    downloadAudio() {
        if (this.currentAudioBlob) {
            const url = URL.createObjectURL(this.currentAudioBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `speech_${new Date().getTime()}.wav`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }

    /**
     * フォームをクリア
     */
    clearForm() {
        this.textInput.value = '';
        this.updateCharCount();
        this.hideAudioPlayer();
        this.hideError();
        this.textInput.focus();
        
        // デフォルト音声を選択
        const defaultVoice = document.querySelector('input[name="voice"][value="Zephyr"]');
        if (defaultVoice) {
            defaultVoice.checked = true;
        }
    }

    /**
     * 再生ボタンをリセット
     */
    resetPlayButton() {
        this.isPlaying = false;
        this.playBtn.textContent = '▶️';
        this.playBtn.disabled = true;
        this.downloadBtn.disabled = true;
    }

    /**
     * ローディング表示を制御
     */
    showLoading(show) {
        if (show) {
            this.loadingIndicator.classList.add('show');
            this.generateBtn.disabled = true;
        } else {
            this.loadingIndicator.classList.remove('show');
            this.generateBtn.disabled = false;
        }
    }

    /**
     * 音声プレーヤーを非表示
     */
    hideAudioPlayer() {
        this.audioPlayer.classList.remove('show');
        
        // リソースをクリーンアップ
        if (this.currentAudioUrl) {
            URL.revokeObjectURL(this.currentAudioUrl);
            this.currentAudioUrl = null;
        }
        
        if (this.audioElement.src) {
            this.audioElement.src = '';
        }
        
        this.currentAudioBlob = null;
        this.currentFileId = null;
        this.resetPlayButton();
    }

    /**
     * エラーメッセージを表示
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.add('show');
        
        // 5秒後に自動的に非表示
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    /**
     * エラーメッセージを非表示
     */
    hideError() {
        this.errorMessage.classList.remove('show');
    }

    /**
     * アプリケーションの状態をリセット
     */
    reset() {
        this.clearForm();
        this.hideAudioPlayer();
        this.hideError();
        this.showLoading(false);
    }

    /**
     * キーボードショートカットを処理
     */
    handleKeyboardShortcuts(e) {
        // Ctrl+Enter で音声生成
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            if (!this.generateBtn.disabled) {
                this.handleSubmit(new Event('submit'));
            }
        }
        
        // Escapeキーでクリア
        if (e.key === 'Escape') {
            this.clearForm();
        }
        
        // スペースキーで再生/一時停止（テキストエリア以外）
        if (e.key === ' ' && e.target !== this.textInput && this.audioPlayer.classList.contains('show')) {
            e.preventDefault();
            this.togglePlayback();
        }
    }

    /**
     * アプリケーションの初期化完了
     */
    onReady() {
        console.log('TTS App initialized successfully');
        
        // キーボードショートカットを有効化
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // フォーカスをテキストエリアに設定
        this.textInput.focus();
        
        // 初期文字数カウント
        this.updateCharCount();
    }
}

/**
 * ユーティリティ関数
 */
const TTSUtils = {
    /**
     * ファイルサイズを人間が読みやすい形式に変換
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * 時間を mm:ss 形式に変換
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    /**
     * デバウンス関数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * ローカルストレージに設定を保存
     */
    saveSettings(settings) {
        try {
            localStorage.setItem('tts_settings', JSON.stringify(settings));
        } catch (error) {
            console.warn('Failed to save settings:', error);
        }
    },

    /**
     * ローカルストレージから設定を読み込み
     */
    loadSettings() {
        try {
            const settings = localStorage.getItem('tts_settings');
            return settings ? JSON.parse(settings) : {};
        } catch (error) {
            console.warn('Failed to load settings:', error);
            return {};
        }
    }
};

// DOM読み込み完了後にアプリケーションを初期化
document.addEventListener('DOMContentLoaded', () => {
    window.ttsApp = new TTSApp();
    window.ttsApp.onReady();
});