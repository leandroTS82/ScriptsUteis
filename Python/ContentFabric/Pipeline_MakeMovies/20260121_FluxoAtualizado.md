Task Scheduler (1h)
  ↓
CreateRightNowAuto.bat
  ↓
GetReadyToBeCreated.py
  ├─ verifica lock
  ├─ verifica jsons válidos
  ├─ unifica
  ├─ marca processing_
  ├─ preenche CreateLater.json
  └─ retorna EXIT 2
  ↓
pipeline_MakeVideoGemin_MoveFiles.bat
  ├─ cria lock
  ├─ executa pipeline
  ├─ sucesso → success_
  └─ erro → error_
