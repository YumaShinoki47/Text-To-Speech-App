"""
TTS Generator Class
Gemini APIを使用したテキスト音声変換クラス
"""

import base64
import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types
import logging

# ログ設定
logger = logging.getLogger(__name__)


class TTSGenerator:
    """
    Gemini APIを使用してテキストから音声を生成するクラス
    """
    
    def __init__(self, api_key: str = None):
        """
        TTSGeneratorを初期化
        
        Args:
            api_key: Gemini APIキー（Noneの場合は環境変数から取得）
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Gemini APIクライアントを初期化
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-preview-tts"
        
        # 利用可能な音声リスト
        self.available_voices = [
            "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", 
            "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", 
            "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome",
            "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam",
            "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
            "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
        ]
        
        logger.info("TTSGenerator initialized successfully")
    
    def save_binary_file(self, file_name: str, data: bytes) -> bool:
        """
        バイナリデータをファイルに保存する
        
        Args:
            file_name: 保存するファイル名
            data: 保存するバイナリデータ
            
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            with open(file_name, "wb") as f:
                f.write(data)
            logger.info(f"音声ファイルを保存しました：{file_name}")
            return True
        except Exception as e:
            logger.error(f"ファイル保存エラー: {str(e)}")
            return False
    
    def generate_speech(self, text: str, voice: str = "Zephyr", output_path: str = None) -> bool:
        """
        テキストから音声を生成するメイン関数
        
        Args:
            text: 読み上げるテキスト
            voice: 使用する音声名
            output_path: 出力ファイルパス（Noneの場合は自動生成）
            
        Returns:
            bool: 生成が成功したかどうか
        """
        try:
            # 入力検証
            if not text.strip():
                logger.error("テキストが空です")
                return False
            
            if voice not in self.available_voices:
                logger.warning(f"未知の音声: {voice}. デフォルトのZephyrを使用します")
                voice = "Zephyr"
            
            # 出力パスが指定されていない場合は自動生成
            if output_path is None:
                import uuid
                file_id = str(uuid.uuid4())
                output_path = f"speech_{file_id}.wav"
            
            logger.info(f"音声生成開始 - テキスト: {text[:50]}...")
            logger.info(f"使用音声: {voice}")
            logger.info(f"出力先: {output_path}")
            
            # リクエストの内容を設定
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=text),
                    ],
                ),
            ]
            
            # 音声生成の設定
            generate_content_config = types.GenerateContentConfig(
                temperature=1,  # 生成の多様性（0-1の範囲、1が最も多様）
                response_modalities=["audio"],  # レスポンスの形式として音声を指定
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            )
            
            # ストリーミングで音声生成を実行
            audio_data_chunks = []
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                # レスポンスデータの存在確認
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                # 音声データが含まれている場合の処理
                if chunk.candidates[0].content.parts[0].inline_data:
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    
                    # MIMEタイプから適切な拡張子を推測
                    file_extension = mimetypes.guess_extension(inline_data.mime_type)
                    if file_extension is None:
                        # 拡張子が推測できない場合はWAVとして処理
                        data_buffer = self.convert_to_wav(inline_data.data, inline_data.mime_type)
                    
                    # 音声ファイルを保存
                    return self.save_binary_file(output_path, data_buffer)
                else:
                    # テキストレスポンスがある場合は表示
                    if hasattr(chunk, 'text') and chunk.text:
                        logger.info(f"API Response: {chunk.text}")
            
            logger.error("音声データが生成されませんでした")
            return False
            
        except Exception as e:
            logger.error(f"音声生成エラー: {str(e)}")
            return False
    
    def convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """
        生の音声データをWAVファイル形式に変換する関数
        
        Args:
            audio_data: 生の音声データ（バイト形式）
            mime_type: 音声データのMIMEタイプ
            
        Returns:
            WAVファイル形式のバイトデータ
        """
        try:
            # MIMEタイプから音声パラメータを解析
            parameters = self.parse_audio_mime_type(mime_type)
            bits_per_sample = parameters["bits_per_sample"]
            sample_rate = parameters["rate"]
            num_channels = 1  # モノラル
            data_size = len(audio_data)
            bytes_per_sample = bits_per_sample // 8
            block_align = num_channels * bytes_per_sample
            byte_rate = sample_rate * block_align
            chunk_size = 36 + data_size  # ヘッダー36バイト + データサイズ
            
            # WAVファイルのヘッダーを構築
            # 参考: http://soundfile.sapp.org/doc/WaveFormat/
            header = struct.pack(
                "<4sI4s4sIHHIIHH4sI",
                b"RIFF",          # ChunkID（RIFFヘッダー）
                chunk_size,       # ChunkSize（ファイル全体のサイズ - 8バイト）
                b"WAVE",          # Format（WAVEフォーマット）
                b"fmt ",          # Subchunk1ID（フォーマットチャンク）
                16,               # Subchunk1Size（PCMの場合は16）
                1,                # AudioFormat（PCMの場合は1）
                num_channels,     # NumChannels（チャンネル数）
                sample_rate,      # SampleRate（サンプリングレート）
                byte_rate,        # ByteRate（バイトレート）
                block_align,      # BlockAlign（ブロックアライメント）
                bits_per_sample,  # BitsPerSample（サンプルあたりのビット数）
                b"data",          # Subchunk2ID（データチャンク）
                data_size         # Subchunk2Size（音声データのサイズ）
            )
            
            return header + audio_data
            
        except Exception as e:
            logger.error(f"WAV変換エラー: {str(e)}")
            return audio_data  # 変換に失敗した場合は元のデータを返す
    
    def parse_audio_mime_type(self, mime_type: str) -> dict:
        """
        音声MIMEタイプ文字列からビット数とサンプリングレートを解析する関数
        
        Args:
            mime_type: 音声MIMEタイプ文字列（例: "audio/L16;rate=24000"）
            
        Returns:
            dict: "bits_per_sample"と"rate"キーを持つ辞書
        """
        # デフォルト値を設定
        bits_per_sample = 16   # デフォルトのビット数
        rate = 24000          # デフォルトのサンプリングレート
        
        try:
            # MIMEタイプをセミコロンで分割してパラメータを解析
            parts = mime_type.split(";")
            for param in parts:
                param = param.strip()
                
                # レートパラメータの解析
                if param.lower().startswith("rate="):
                    try:
                        rate_str = param.split("=", 1)[1]
                        rate = int(rate_str)
                    except (ValueError, IndexError):
                        pass  # デフォルト値を維持
                
                # ビット数パラメータの解析（audio/L16のような形式）
                elif param.startswith("audio/L"):
                    try:
                        bits_per_sample = int(param.split("L", 1)[1])
                    except (ValueError, IndexError):
                        pass  # デフォルト値を維持
        
        except Exception as e:
            logger.warning(f"MIMEタイプ解析エラー: {str(e)} - デフォルト値を使用")
        
        return {"bits_per_sample": bits_per_sample, "rate": rate}
    
    def get_available_voices(self) -> list:
        """
        利用可能な音声リストを取得
        
        Returns:
            list: 利用可能な音声名のリスト
        """
        return self.available_voices.copy()
    
    def is_voice_available(self, voice: str) -> bool:
        """
        指定された音声が利用可能かチェック
        
        Args:
            voice: チェックする音声名
            
        Returns:
            bool: 利用可能かどうか
        """
        return voice in self.available_voices


# デバッグ用のメイン関数
if __name__ == "__main__":
    # テスト実行
    try:
        generator = TTSGenerator()
        
        test_text = "こんにちは。私はAIアシスタントです。"
        test_voice = "Zephyr"
        output_file = "test_speech.wav"
        
        print(f"テスト実行: {test_text}")
        print(f"音声: {test_voice}")
        
        success = generator.generate_speech(
            text=test_text,
            voice=test_voice,
            output_path=output_file
        )
        
        if success:
            print(f"音声生成成功: {output_file}")
        else:
            print("音声生成失敗")
            
    except Exception as e:
        print(f"エラー: {str(e)}")
        print("GEMINI_API_KEY環境変数が設定されているか確認してください")