@echo off
echo Installing Gemini AI package...
pip install google-generativeai>=0.3.0
echo.
echo Gemini AI package installed!
echo.
echo Next steps:
echo 1. Get your API keys from: https://aistudio.google.com/app/apikey
echo 2. Add them to your .env file: GEMINI_API_KEYS=key1,key2,key3
echo 3. Run test: python test_gemini_setup.py
echo.
pause