"""
Text-to-Speech API Backend
FastAPIを使用した音声生成バックエンドサービス
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 音声生成クラスをインポート
from tts_generator import TTSGenerator

# FastAPIアプリケーションを初期化
app = FastAPI(
    title="Text-to-Speech API",
    description="Gemini APIを使用した音声生成サービス",
    version="1.0.0"
)

# CORS設定（フロントエンドとの通信を許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なドメインを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストボディのモデル定義
class TTSRequest(BaseModel):
    text: str
    voice: str = "Zephyr"  # デフォルト音声
    
    class Config:
        schema_extra = {
            "example": {
                "text": "こんにちは。私はAIアシスタントです。",
                "voice": "Zephyr"
            }
        }

# レスポンスモデル定義
class TTSResponse(BaseModel):
    message: str
    file_id: str
    voice_used: str
    text_length: int

# TTS生成器のインスタンスを作成
tts_generator = TTSGenerator()

# 出力フォルダの確認・作成
OUTPUT_DIR = "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/")
async def root():
    """
    APIのルートエンドポイント - ヘルスチェック用
    """
    return {
        "message": "Text-to-Speech API is running",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    try:
        # Gemini APIキーの存在確認
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {
                "status": "unhealthy",
                "error": "GEMINI_API_KEY is not set"
            }
        
        return {
            "status": "healthy",
            "gemini_api": "configured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/voices")
async def get_available_voices():
    """
    利用可能な音声リストを取得（35種類すべて）
    """
    voices = [
        {"name": "Zephyr", "description": "穏やかな声"},
        {"name": "Puck", "description": "活発な声"},
        {"name": "Charon", "description": "深い声"},
        {"name": "Kore", "description": "明るい声"},
        {"name": "Fenrir", "description": "力強い声"},
        {"name": "Leda", "description": "優雅な声"},
        {"name": "Orus", "description": "知的な声"},
        {"name": "Aoede", "description": "歌うような声"},
        {"name": "Callirrhoe", "description": "流れるような声"},
        {"name": "Autonoe", "description": "自然な声"},
        {"name": "Enceladus", "description": "雄大な声"},
        {"name": "Iapetus", "description": "落ち着いた声"},
        {"name": "Umbriel", "description": "神秘的な声"},
        {"name": "Algieba", "description": "華やかな声"},
        {"name": "Despina", "description": "軽やかな声"},
        {"name": "Erinome", "description": "エレガントな声"},
        {"name": "Algenib", "description": "クリアな声"},
        {"name": "Rasalgethi", "description": "威厳のある声"},
        {"name": "Laomedeia", "description": "やわらかな声"},
        {"name": "Achernar", "description": "輝く声"},
        {"name": "Alnilam", "description": "透明感のある声"},
        {"name": "Schedar", "description": "温かい声"},
        {"name": "Gacrux", "description": "力強く美しい声"},
        {"name": "Pulcherrima", "description": "最も美しい声"},
        {"name": "Achird", "description": "鋭い声"},
        {"name": "Zubenelgenubi", "description": "バランスの取れた声"},
        {"name": "Vindemiatrix", "description": "収穫の声"},
        {"name": "Sadachbia", "description": "幸運の声"},
        {"name": "Sadaltager", "description": "商人の声"},
        {"name": "Sulafat", "description": "亀の声"},
        {"name": "Albireo", "description": "二重星の声"},
        {"name": "Mintaka", "description": "ベルトの声"},
        {"name": "Rigel", "description": "巨星の声"},
        {"name": "Bellatrix", "description": "戦士の声"},
        {"name": "Sirius", "description": "最も明るい声"}
    ]
    
    return {
        "voices": voices,
        "default": "Zephyr"
    }


@app.post("/generate-speech", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """
    テキストから音声を生成するメインエンドポイント
    
    Args:
        request: TTSRequest (text, voice)
    
    Returns:
        TTSResponse: 生成結果の情報
    """
    try:
        # 入力検証
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="テキストが空です")
        
        if len(request.text) > 1000:
            raise HTTPException(status_code=400, detail="テキストが長すぎます（最大1000文字）")
        
        logger.info(f"Generating speech for text: {request.text[:50]}...")
        logger.info(f"Using voice: {request.voice}")
        
        # 一意のファイルIDを生成
        file_id = str(uuid.uuid4())
        output_path = os.path.join(OUTPUT_DIR, f"{file_id}.wav")
        
        # 音声生成を実行
        success = tts_generator.generate_speech(
            text=request.text,
            voice=request.voice,
            output_path=output_path
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="音声生成に失敗しました")
        
        # ファイルの存在確認
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="音声ファイルの生成に失敗しました")
        
        logger.info(f"Speech generated successfully: {output_path}")
        
        return TTSResponse(
            message="音声生成が完了しました",
            file_id=file_id,
            voice_used=request.voice,
            text_length=len(request.text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音声生成中にエラーが発生しました: {str(e)}")


@app.get("/download/{file_id}")
async def download_audio(file_id: str):
    """
    生成された音声ファイルをダウンロード
    
    Args:
        file_id: 音声ファイルのID
    
    Returns:
        FileResponse: 音声ファイル
    """
    try:
        # ファイルパスの構築
        file_path = os.path.join(OUTPUT_DIR, f"{file_id}.wav")
        
        # ファイルの存在確認
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="音声ファイルが見つかりません")
        
        logger.info(f"Serving audio file: {file_path}")
        
        # ファイルを返す
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=f"speech_{file_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ファイル配信中にエラーが発生しました: {str(e)}")


@app.delete("/cleanup")
async def cleanup_old_files():
    """
    古い音声ファイルを削除（管理用エンドポイント）
    """
    try:
        if not os.path.exists(OUTPUT_DIR):
            return {"message": "出力フォルダが存在しません", "deleted_count": 0}
        
        deleted_count = 0
        current_time = datetime.now().timestamp()
        
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.wav'):
                file_path = os.path.join(OUTPUT_DIR, filename)
                file_time = os.path.getmtime(file_path)
                
                # 1時間以上古いファイルを削除
                if current_time - file_time > 3600:
                    os.remove(file_path)
                    deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old audio files")
        
        return {
            "message": f"{deleted_count}個の古いファイルを削除しました",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"クリーンアップ中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # 環境変数チェック
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY environment variable is not set!")
    
    # 開発サーバーを起動
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開発時の自動リロード
        log_level="info"
    )