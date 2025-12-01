import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dateutil import tz

logger = logging.getLogger(__name__)

ALL_SUBJECTS = [
    "ЛК Информатика",
    "ЛК Физика",
    "ПР Физическая культура и спорт",
    "ПР Иностранный язык",
    "ЛК История России",
    "ЛК Линейная алгебра и аналитическая геометрия",
    "ПР Математический анализ",
    "ПР История России",
    "ПР Линейная алгебра и аналитическая геометрия",
    "ПР Информатика",
    "ПР Физика",
    "ПР Математическая логика и теория алгоритмов",
    "ЛК Математический анализ",
    "ЛК Математическая логика и теория алгоритмов",
    "ЛК Введение в профессиональную деятельность",
    "ЛАБ Физика (1 п/г)",
    "ЛАБ Физика (2 п/г)",
]


class ScheduleStorage:
    
    def __init__(self, storage_file="data/schedule_data.json"):
        self.storage_file = os.path.abspath(storage_file)  
        logger.info(f"ScheduleStorage инициализирован с фай лом: {self.storage_file}")
        self.data = self._load_data()
        self.moscow_tz = tz.gettz("Europe/Moscow")
    
    def reload_data(self):
        self.data = self._load_data()
        logger.info(f"Данные перезагружены. Файлы для пар: {list(self.data.get('lesson_files', {}).keys())}")
    
    def _load_data(self) -> Dict:
        logger.info(f"Загрузка данных из файла: {self.storage_file}")
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Данные загружены успешно. Ключи: {list(data.keys())}")
                    lesson_files = data.get('lesson_files', {})
                    logger.info(f"Загружено файлов для пар: {list(lesson_files.keys())}")
                    return data
            except Exception as e:
                logger.error(f"Ошибка при загрузке данных: {e}", exc_info=True)
        else:
            logger.info(f"Файл не существует: {self.storage_file}")
        
        return {
            "notified_lessons": {},
            "lesson_files": {},
            "attendance_messages": {},
            "attendance_requests": {}
        }
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Данные сохранены в {self.storage_file}")
            logger.info(f"Сохранено файлов для пар: {list(self.data.get('lesson_files', {}).keys())}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}", exc_info=True)
    
    def was_notified(self, lesson_id: str) -> bool:
        self._cleanup_old_notifications()
        return lesson_id in self.data["notified_lessons"]
    
    def mark_as_notified(self, lesson_id: str):
        self.data["notified_lessons"][lesson_id] = datetime.now(self.moscow_tz).isoformat()
        self._save_data()
    
    def _cleanup_old_notifications(self):
        now = datetime.now(self.moscow_tz)
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
        self.reload_data()
        
        if "lesson_files" not in self.data:
            self.data["lesson_files"] = {}
        
        if lesson_name not in self.data["lesson_files"]:
            self.data["lesson_files"][lesson_name] = []
        
        for path in file_paths:
            if path not in self.data["lesson_files"][lesson_name]:
                self.data["lesson_files"][lesson_name].append(path)
        
        self._save_data()
        logger.info(f"Добавлены файлы для пары '{lesson_name}': {file_paths}")
        logger.info(f"Текущие файлы в хранилище: {self.data['lesson_files']}")
    
    def _normalize_name(self, name: str) -> str:
        return " ".join(name.strip().split()).lower()
    
    def _parse_lesson_name(self, name: str) -> Tuple[str, str]:
        name = name.strip()
        
        match = re.match(r'^(ЛК|ПР|ЛАБ)\s+(.+)$', name, re.IGNORECASE)
        
        if match:
            lesson_type = match.group(1).upper()
            discipline = self._normalize_name(match.group(2))
            return (lesson_type, discipline)
        
        return ("", self._normalize_name(name))
    
    def get_lesson_files(self, lesson_id: str, lesson_title: str) -> List[str]:
        try:
            self.data = self._load_data()
            
            stored_files = self.data.get("lesson_files", {})
            
            logger.info(f"=== ПОИСК ФАЙЛОВ ===")
            logger.info(f"Искомая пара: '{lesson_title}'")
            logger.info(f"Файл хранилища: {self.storage_file}")
            logger.info(f"Доступные предметы ({len(stored_files)}): {list(stored_files.keys())}")
            
            if not stored_files:
                logger.info(f"Хранилище пустое!")
                return []
            
            search_type, search_discipline = self._parse_lesson_name(lesson_title)
            logger.info(f"Разбор искомой пары: тип='{search_type}', дисциплина='{search_discipline}'")
            
            for stored_name, files in stored_files.items():
                stored_type, stored_discipline = self._parse_lesson_name(stored_name)
                logger.info(f"Сравниваем с '{stored_name}': тип='{stored_type}', дисциплина='{stored_discipline}'")
                
                if search_type == stored_type and search_discipline == stored_discipline:
                    logger.info(f"СОВПАДЕНИЕ! '{stored_name}' -> {len(files)} файлов: {files}")
                    return files
                else:
                    logger.info(f"Нет совпадения: type_match={search_type == stored_type}, disc_match={search_discipline == stored_discipline}")
            
            logger.info(f"Файлы для '{lesson_title}' не найдены")
            return []
            
        except Exception as e:
            logger.error(f"Ошибка при получении файлов: {e}", exc_info=True)
            return []
    
    def remove_lesson_files(self, lesson_name: str):
        if lesson_name in self.data["lesson_files"]:
            del self.data["lesson_files"][lesson_name]
            self._save_data()
            logger.info(f"Удалены файлы для пары '{lesson_name}'")
    
    def get_all_lesson_files(self) -> Dict[str, List[str]]:
        self.reload_data()
        return self.data.get("lesson_files", {})
    
    def save_attendance_message(self, lesson_id: str, message_id: int, lesson_name: str = "", full_subject: str = "", 
                                 lesson_start: str = "", break_minutes: int = 10):
        
        self.data["attendance_messages"][lesson_id] = {
            "message_id": message_id,
            "lesson_name": lesson_name,
            "full_subject": full_subject or lesson_name,
            "lesson_start": lesson_start,
            "break_minutes": break_minutes
        }
        self._save_data()
    
    def get_attendance_message_info(self, lesson_id: str) -> Optional[Dict]:
        return self.data.get("attendance_messages", {}).get(lesson_id)
    
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
    
    def clear_notified_lessons(self):
        self.reload_data()
        self.data["notified_lessons"] = {}
        self._save_data()
        logger.info("Список уведомленных пар очищен")
