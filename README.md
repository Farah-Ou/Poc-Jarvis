# Jarvis_2_0_2 repo git 

### To run the project:
venv\Scripts\activate 
cd .\node-start-all-servers\
$env:PYTHONIOENCODING="utf-8"     ## To enable print of utf characters in terminal
npm run start:all                 # To start all servers 
npm run start:core-only          # To start essential servers (Frontend & Backend)
npm run start:graphs-only        # To start only graph servers

#### Separate Servers start :
npm run start:BackendAuto
npm run start:BackendTCGen
npm run start:Backend
npm run start:Frontend


### Activate backend venv : 
venv\Scripts\activate


### To start servers separately : 
run_main = "uvicorn src.app:app --port 8000 --reload"

run_tcgen = "uvicorn Backend_TC_Gen.main:app --port 8003 --reload"

run_auto = "uvicorn Backend_Auto.main:app --port 8004 --reload" 

run_eval = "uvicorn Backend_Eval.main:app --port 8002 --reload"

 
### To start graph visuals servers : 
cd "Created_Graphs\US-Graph-Visual\graphrag-visualizer"
cd "Created_Graphs\Context-Graph-Visual\graphrag-visualizer"
cd "Created_Graphs\Guidelines-Graph-Visual\graphrag-visualizer"
cd "Created_Graphs\Test-Cases-History-Graph-Visual\graphrag-visualizer"
"# Jarvis_2_0_to_Clean" 
