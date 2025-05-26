# 🎤文章読み上げアプリ SpeakAI

入力したテキスト文を音声出力するアプリケーションです。

![FireShot Capture 049 - SpeakAI - AIテキスト読み上げ -  localhost](https://github.com/user-attachments/assets/e67678e4-6058-45f4-b703-02d2628c6d40)




## インストール
```
git clone https://github.com/YumaShinoki47/Text-To-Speech-App.git
```
```
cd Text-To-Speech-App
pip install -r requirements.txt
```
"GEMINI_API_KEY"にAPIキーを設定してください。

## 起動方法
バックエンド
```
cd Text-To-Speech-App/backend
python app.py
```

フロントエンド
```
cd Text-To-Speech-App/frontend
python -m http.server 3000
```

http://localhost:3000/ にアクセスしてください。

## 使用技術

Gemini 2.5 Flash Preview TTS

https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja
