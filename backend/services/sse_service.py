import queue
import threading
import json

class SSENotificationManager:
    def __init__(self):
        self.clients = {}  # teacher_id -> set/list of queue.Queue()
        self.lock = threading.Lock()

    def add_client(self, teacher_id):
        q = queue.Queue()
        t_id_key = str(teacher_id)
        with self.lock:
            if t_id_key not in self.clients:
                self.clients[t_id_key] = []
            self.clients[t_id_key].append(q)
        print(f"[SSENotificationManager] Teacher {teacher_id} connected to SSE. Active queues for teacher: {len(self.clients[t_id_key])}")
        return q

    def remove_client(self, teacher_id, q):
        t_id_key = str(teacher_id)
        with self.lock:
            if t_id_key in self.clients:
                if q in self.clients[t_id_key]:
                    self.clients[t_id_key].remove(q)
                if not self.clients[t_id_key]:
                    del self.clients[t_id_key]
        print(f"[SSENotificationManager] Teacher {teacher_id} disconnected from SSE.")

    def broadcast_to_teacher(self, teacher_id, event_data):
        t_id_key = str(teacher_id)
        with self.lock:
            queues = list(self.clients.get(t_id_key, []))

        if not queues:
            return

        json_str = json.dumps(event_data)
        formatted_message = f"data: {json_str}\n\n"

        for q in queues:
            try:
                q.put_nowait(formatted_message)
            except Exception as e:
                print(f"[SSENotificationManager] Queue put error for teacher {teacher_id}: {e}")

sse_manager = SSENotificationManager()
