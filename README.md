# 🎤文章読み上げアプリ SpeakAI

Google Gemini 2.5 Flash Preview TTSを活用した、高品質な音声合成システムです。

![FireShot Capture 049 - SpeakAI - AIテキスト読み上げ -  localhost](https://github.com/user-attachments/assets/e67678e4-6058-45f4-b703-02d2628c6d40)


## ✨特徴

🤖 AI音声合成: Google Gemini 2.5 Flash Preview TTSによる自然な音声生成

🌐 Webベース: ブラウザで簡単にアクセス可能

📝 テキスト入力: 任意のテキストを音声に変換

🎵 高品質音声: クリアで聞き取りやすい音声出力

## 🚀 クイックスタート
### 1. リポジトリのクローン

```
git clone https://github.com/YumaShinoki47/Text-To-Speech-App.git
cd Text-To-Speech-App
```

### 2. 依存関係のインストール

```
pip install -r requirements.txt
```

### 3. APIキーの設定

GEMINI_API_KEY環境変数にあなたのAPIキーを設定してください。

### 4. アプリケーションの起動
#### バックエンドサーバー起動
```
cd Text-To-Speech-App/backend
python app.py
```

#### フロントエンドサーバー起動
```
cd Text-To-Speech-App/frontend
python -m http.server 3000
```

### 5. アクセス
ブラウザで http://localhost:3000/ にアクセスしてください。

## 🛠️使用技術

- 音声合成エンジン: Gemini 2.5 Flash Preview TTS
- バックエンド: Python
- フロントエンド: HTML/JavaScript
- API: Google Gemini API

## 📋システム要件
- Python 3.7以上
- インターネット接続（API通信のため）
- Google Gemini APIキー