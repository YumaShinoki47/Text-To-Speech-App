/**
 * API通信を管理するクラス
 * バックエンドのFastAPIと通信を行う
 */
class TTSApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * APIのヘルスチェックを実行
     * @returns {Promise<Object>} ヘルスチェック結果
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            return {
                success: response.ok,
                data: data
            };
        } catch (error) {
            console.error('Health check failed:', error);
            return {
                success: false,
                error: 'サーバーに接続できません'
            };
        }
    }

    /**
     * 利用可能な音声リストを取得
     * @returns {Promise<Object>} 音声リスト
     */
    async getAvailableVoices() {
        try {
            const response = await fetch(`${this.baseUrl}/voices`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return {
                success: true,
                data: data
            };
        } catch (error) {
            console.error('Failed to fetch voices:', error);
            return {
                success: false,
                error: '音声リストの取得に失敗しました',
                data: {
                    voices: [
                        { name: "Zephyr", description: "穏やかな声" },
                        { name: "Puck", description: "活発な声" },
                        { name: "Charon", description: "深い声" },
                        { name: "Kore", description: "明るい声" }
                    ],
                    default: "Zephyr"
                }
            };
        }
    }

    /**
     * テキストから音声を生成
     * @param {string} text - 読み上げるテキスト
     * @param {string} voice - 使用する音声名
     * @returns {Promise<Object>} 生成結果
     */
    async generateSpeech(text, voice = 'Zephyr') {
        try {
            // 入力検証
            if (!text || typeof text !== 'string') {
                throw new Error('有効なテキストを入力してください');
            }

            if (text.trim().length === 0) {
                throw new Error('テキストが空です');
            }

            if (text.length > 1000) {
                throw new Error('テキストが長すぎます（最大1000文字）');
            }

            // APIリクエストを送信
            const response = await fetch(`${this.baseUrl}/generate-speech`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text.trim(),
                    voice: voice
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            return {
                success: true,
                data: data
            };

        } catch (error) {
            console.error('Speech generation failed:', error);
            return {
                success: false,
                error: error.message || '音声生成に失敗しました'
            };
        }
    }

    /**
     * 生成された音声ファイルをダウンロード
     * @param {string} fileId - ファイルID
     * @returns {Promise<Object>} ダウンロード結果
     */
    async downloadAudio(fileId) {
        try {
            if (!fileId) {
                throw new Error('ファイルIDが指定されていません');
            }

            const response = await fetch(`${this.baseUrl}/download/${fileId}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            // Blobとして音声データを取得
            const audioBlob = await response.blob();
            
            return {
                success: true,
                data: {
                    blob: audioBlob,
                    url: URL.createObjectURL(audioBlob)
                }
            };

        } catch (error) {
            console.error('Audio download failed:', error);
            return {
                success: false,
                error: error.message || '音声ダウンロードに失敗しました'
            };
        }
    }

    /**
     * 古いファイルをクリーンアップ（管理者用）
     * @returns {Promise<Object>} クリーンアップ結果
     */
    async cleanupOldFiles() {
        try {
            const response = await fetch(`${this.baseUrl}/cleanup`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            return {
                success: true,
                data: data
            };

        } catch (error) {
            console.error('Cleanup failed:', error);
            return {
                success: false,
                error: error.message || 'クリーンアップに失敗しました'
            };
        }
    }

    /**
     * ネットワーク接続をテスト
     * @returns {Promise<boolean>} 接続状態
     */
    async testConnection() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒タイムアウト

            const response = await fetch(`${this.baseUrl}/`, {
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response.ok;

        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }

    /**
     * エラーメッセージを日本語に変換
     * @param {string} error - エラーメッセージ
     * @returns {string} 日本語エラーメッセージ
     */
    translateError(error) {
        const errorMap = {
            'Network Error': 'ネットワークエラーが発生しました',
            'Connection refused': 'サーバーに接続できません',
            'Timeout': 'リクエストがタイムアウトしました',
            'Bad Request': '不正なリクエストです',
            'Internal Server Error': 'サーバー内部エラーが発生しました',
            'Service Unavailable': 'サービスが利用できません'
        };

        return errorMap[error] || error;
    }
}

// グローバルなAPIクライアントインスタンスを作成
window.ttsApi = new TTSApiClient();