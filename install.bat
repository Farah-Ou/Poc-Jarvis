@echo off
SETLOCAL

echo === Creating virtual environment ===
py -3.11 -m venv venv

echo === Activating virtual environment ===
call venv\Scripts\activate.bat

echo === Installing Python requirements ===
pip install -r Requirements_August.txt --upgrade --no-deps

echo === Installing Frontend dependencies ===
cd Frontend
npm install

echo === Installing Graph Visualizer dependencies ===
cd ..
cd Created_Graphs
cd US-Graph-Visual
cd graphrag-visualizer
npm install

echo === Setup completed successfully ===
timeout /t 2 >nul
exit
