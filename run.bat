@echo off

python -m pip install -r requirements.txt
python -m coverage run -m pytest tests
python -m coverage report -m
pause
