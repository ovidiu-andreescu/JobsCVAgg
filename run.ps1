$port = 5000
python -m uvicorn services.user_management.src.user_management.app:app --host 127.0.0.1 --port $port --reload
