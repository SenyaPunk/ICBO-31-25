import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ScheduleStorage:
    
    def __init__(self, storage_file="data/schedule_data.json"):
        self.storage_file = storage_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка при загрузке данных: {e}")
        
        return {
            "notified_lessons": {},  # lesson_id: timestamp
            "lesson_files": {},       # lesson_name: [file_paths]
            "attendance_messages": {},  # lesson_id: {message_id, lesson_name}
            "attendance_requests": {}   # lesson_id: [user_data]
        }
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
    
    def was_notified(self, lesson_id: str) -> bool:
        self._cleanup_old_notifications()
        
        return lesson_id in self.data["notified_lessons"]
    
    def mark_as_notified(self, lesson_id: str):
        self.data["notified_lessons"][lesson_id] = datetime.now().isoformat()
        self._save_data()
    
    def _cleanup_old_notifications(self):
        now = datetime.now()
        to_delete = []
        
        for lesson_id, timestamp_str in self.data["notified_lessons"].items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if (now - timestamp).days > 1:
                    to_delete.append(lesson_id)
            except Exception:
                to_delete.append(lesson_id)
        
        for lesson_id in to_delete:
            del self.data["notified_lessons"][lesson_id]
        
        if to_delete:
            self._save_data()
    
    def add_lesson_files(self, lesson_name: str, file_paths: List[str]):
        if lesson_name not in self.data["lesson_files"]:
            self.data["lesson_files"][lesson_name] = []
        
        for path in file_paths:
            if path not in self.data["lesson_files"][lesson_name]:
                self.data["lesson_files"][lesson_name].append(path)
        
        self._save_data()
        logger.info(f"Добавлены файлы для пары '{lesson_name}': {file_paths}")
    
    def get_lesson_files(self, lesson_id: str, lesson_name: str) -> List[str]:
        import re
        for stored_name, files in self.data["lesson_files"].items():
            if stored_name.lower() in lesson_name.lower() or lesson_name.lower() in stored_name.lower():
                return files
        
        return []
    
    def remove_lesson_files(self, lesson_name: str):
        if lesson_name in self.data["lesson_files"]:
            del self.data["lesson_files"][lesson_name]
            self._save_data()
            logger.info(f"Удалены файлы для пары '{lesson_name}'")
    
    def get_all_lesson_files(self) -> Dict[str, List[str]]:
        return self.data["lesson_files"]
    
    def save_attendance_message(self, lesson_id: str, message_id: int, lesson_name: str = ""):
        self.data["attendance_messages"][lesson_id] = {
            "message_id": message_id,
            "lesson_name": lesson_name
        }
        self._save_data()
    
    def add_attendance_request(self, lesson_id: str, user_data: Dict):
        if lesson_id not in self.data["attendance_requests"]:
            self.data["attendance_requests"][lesson_id] = []
        
        user_id = user_data["user_id"]
        if not any(req["user_id"] == user_id for req in self.data["attendance_requests"][lesson_id]):
            self.data["attendance_requests"][lesson_id].append(user_data)
            self._save_data()
            return True
        
        return False
    
    def get_attendance_list(self, lesson_id: str) -> List[Dict]:
        return self.data["attendance_requests"].get(lesson_id, [])
    
    def clear_attendance_list(self, lesson_id: str):
        if lesson_id in self.data["attendance_requests"]:
            del self.data["attendance_requests"][lesson_id]
            self._save_data()
