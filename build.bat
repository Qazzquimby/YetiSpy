start venv\scripts\pyinstaller.exe --noconfirm --onefile eternal_collection_guide/generate_overall_value.py
start venv\scripts\pyinstaller.exe --noconfirm --onefile eternal_collection_guide/update_cards.py
start venv\scripts\pyinstaller.exe --noconfirm --onefile eternal_collection_guide/update_decks.py
copy build\chromedriver.exe dist\chromedriver.exe
copy build\run.bat dist\run.bat
copy build\search_urls.csv dist\search_urls.csv
pause