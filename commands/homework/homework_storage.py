

import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from dateutil import tz

logger = logging.getLogger(__name__)


def get_academic_week_number(target_date: date) -> int:
    if target_date.month >= 9:
        semester_start = date(target_date.year, 9, 1)
    else:
        semester_start = date(target_date.year - 1, 9, 1)
    
    if target_date < semester_start:
        semester_start = date(target_date.year - 1, 9, 1)
    
    return (target_date - semester_start).days // 7 + 1


class HomeworkStorage:
    
    def __init__(self, storage_file: str = "data/homework_data.json"):
        self.storage_file = os.path.abspath(storage_file)
        self.moscow_tz = tz.gettz("Europe/Moscow")
        self.data = self._load_data()
        logger.info(f"HomeworkStorage инициализирован: {self.storage_file}")
    
    def _load_data(self) -> Dict:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "homework" not in data:
                        data["homework"] = {}
                    if "control_measures" not in data:
                        data["control_measures"] = {}
                    if "last_sent_homework" not in data:
                        data["last_sent_homework"] = None
                    if "last_sent_control" not in data:
                        data["last_sent_control"] = None
                    return data
            except Exception as e:
                logger.error(f"Ошибка загрузки данных: {e}", exc_info=True)
        
        return {
            "homework": {},
            "control_measures": {},
            "last_sent_homework": None,
            "last_sent_control": None
        }
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("Данные успешно сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}", exc_info=True)
    
    def reload_data(self):
        self.data = self._load_data()
    
    def _get_week_number(self, target_date: date) -> int:
        return get_academic_week_number(target_date)
    
    def _date_to_str(self, d: date) -> str:
        return d.strftime("%Y-%m-%d")
    
    def _str_to_date(self, s: str) -> date:
        return datetime.strptime(s, "%Y-%m-%d").date()
    
    
    def add_homework(self, target_date: date, subject: str, task: str) -> bool:
        try:
            week_num = str(self._get_week_number(target_date))
            date_str = self._date_to_str(target_date)
            
            if week_num not in self.data["homework"]:
                self.data["homework"][week_num] = {}
            
            if date_str not in self.data["homework"][week_num]:
                self.data["homework"][week_num][date_str] = {}
            
            if subject not in self.data["homework"][week_num][date_str]:
                self.data["homework"][week_num][date_str][subject] = []
            
            self.data["homework"][week_num][date_str][subject].append(task)
            self._save_data()
            
            logger.info(f"Добавлено ДЗ: {subject} -> {task} к {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления ДЗ: {e}", exc_info=True)
            return False
    
    def get_homework_for_week(self, week_num: Optional[int] = None) -> Dict[str, Dict[str, List[str]]]:
        if week_num is None:
            week_num = self._get_week_number(datetime.now(self.moscow_tz).date())
        
        return self.data["homework"].get(str(week_num), {})
    
    def get_homework_for_date(self, target_date: date) -> Dict[str, List[str]]:
        week_num = str(self._get_week_number(target_date))
        date_str = self._date_to_str(target_date)
        
        return self.data["homework"].get(week_num, {}).get(date_str, {})
    
    def get_all_upcoming_homework(self) -> List[Tuple[date, str, List[str]]]:
        today = datetime.now(self.moscow_tz).date()
        result = []
        
        for week_num, week_data in self.data["homework"].items():
            for date_str, subjects in week_data.items():
                hw_date = self._str_to_date(date_str)
                if hw_date >= today:
                    for subject, tasks in subjects.items():
                        if tasks:
                            result.append((hw_date, subject, tasks))
        
        result.sort(key=lambda x: x[0])
        return result
    
    def remove_homework(self, target_date: date, subject: str, task_index: int = -1) -> bool:
        try:
            week_num = str(self._get_week_number(target_date))
            date_str = self._date_to_str(target_date)
            
            if week_num not in self.data["homework"]:
                return False
            if date_str not in self.data["homework"][week_num]:
                return False
            if subject not in self.data["homework"][week_num][date_str]:
                return False
            
            if task_index == -1:
                del self.data["homework"][week_num][date_str][subject]
            else:
                if 0 <= task_index < len(self.data["homework"][week_num][date_str][subject]):
                    self.data["homework"][week_num][date_str][subject].pop(task_index)
                else:
                    return False
            
            # Очистка пустых структур
            if not self.data["homework"][week_num][date_str]:
                del self.data["homework"][week_num][date_str]
            if not self.data["homework"][week_num]:
                del self.data["homework"][week_num]
            
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления ДЗ: {e}", exc_info=True)
            return False
    



    def add_control_measure(self, target_date: date, subject: str, description: str) -> bool:
        try:
            week_num = str(self._get_week_number(target_date))
            date_str = self._date_to_str(target_date)
            
            if week_num not in self.data["control_measures"]:
                self.data["control_measures"][week_num] = {}
            
            if date_str not in self.data["control_measures"][week_num]:
                self.data["control_measures"][week_num][date_str] = {}
            
            if subject not in self.data["control_measures"][week_num][date_str]:
                self.data["control_measures"][week_num][date_str][subject] = []
            
            self.data["control_measures"][week_num][date_str][subject].append(description)
            self._save_data()
            
            logger.info(f"Добавлено КМ: {subject} -> {description} на {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления КМ: {e}", exc_info=True)
            return False
    
    def get_control_measures_for_week(self, week_num: Optional[int] = None) -> Dict[str, Dict[str, List[str]]]:
        if week_num is None:
            week_num = self._get_week_number(datetime.now(self.moscow_tz).date())
        
        return self.data["control_measures"].get(str(week_num), {})
    
    def get_control_measures_for_date(self, target_date: date) -> Dict[str, List[str]]:
        week_num = str(self._get_week_number(target_date))
        date_str = self._date_to_str(target_date)
        
        return self.data["control_measures"].get(week_num, {}).get(date_str, {})
    
    def get_all_upcoming_control_measures(self) -> List[Tuple[date, str, List[str]]]:
        today = datetime.now(self.moscow_tz).date()
        result = []
        
        for week_num, week_data in self.data["control_measures"].items():
            for date_str, subjects in week_data.items():
                km_date = self._str_to_date(date_str)
                if km_date >= today:
                    for subject, descriptions in subjects.items():
                        if descriptions:
                            result.append((km_date, subject, descriptions))
        
        result.sort(key=lambda x: x[0])
        return result
    
    def remove_control_measure(self, target_date: date, subject: str, index: int = -1) -> bool:
        try:
            week_num = str(self._get_week_number(target_date))
            date_str = self._date_to_str(target_date)
            
            if week_num not in self.data["control_measures"]:
                return False
            if date_str not in self.data["control_measures"][week_num]:
                return False
            if subject not in self.data["control_measures"][week_num][date_str]:
                return False
            
            if index == -1:
                del self.data["control_measures"][week_num][date_str][subject]
            else:
                if 0 <= index < len(self.data["control_measures"][week_num][date_str][subject]):
                    self.data["control_measures"][week_num][date_str][subject].pop(index)
                else:
                    return False
            
            if not self.data["control_measures"][week_num][date_str]:
                del self.data["control_measures"][week_num][date_str]
            if not self.data["control_measures"][week_num]:
                del self.data["control_measures"][week_num]
            
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления КМ: {e}", exc_info=True)
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        today = datetime.now(self.moscow_tz).date()
        cutoff = today - timedelta(days=days_to_keep)
        
        for week_num in list(self.data["homework"].keys()):
            for date_str in list(self.data["homework"][week_num].keys()):
                if self._str_to_date(date_str) < cutoff:
                    del self.data["homework"][week_num][date_str]
            if not self.data["homework"][week_num]:
                del self.data["homework"][week_num]
        
        for week_num in list(self.data["control_measures"].keys()):
            for date_str in list(self.data["control_measures"][week_num].keys()):
                if self._str_to_date(date_str) < cutoff:
                    del self.data["control_measures"][week_num][date_str]
            if not self.data["control_measures"][week_num]:
                del self.data["control_measures"][week_num]
        
        self._save_data()
        logger.info(f"Очищены данные старше {cutoff}")
    
    def cleanup_old_weeks(self) -> dict:
        
        today = datetime.now(self.moscow_tz).date()
        current_week = self._get_week_number(today)
        
        removed_homework_weeks = []
        removed_control_weeks = []
        
        for week_num in list(self.data["homework"].keys()):
            try:
                week_int = int(week_num)
                if week_int < current_week:
                    removed_homework_weeks.append(week_int)
                    del self.data["homework"][week_num]
                    logger.info(f"Очищена неделя ДЗ: {week_num}")
            except ValueError:
                continue
        
        for week_num in list(self.data["control_measures"].keys()):
            try:
                week_int = int(week_num)
                if week_int < current_week:
                    removed_control_weeks.append(week_int)
                    del self.data["control_measures"][week_num]
                    logger.info(f"Очищена неделя КМ: {week_num}")
            except ValueError:
                continue
        
        if removed_homework_weeks or removed_control_weeks:
            self._save_data()
            logger.info(
                f"Очистка завершена. Текущая неделя: {current_week}. "
                f"Удалено ДЗ недель: {removed_homework_weeks}, КМ недель: {removed_control_weeks}"
            )
        
        return {
            "current_week": current_week,
            "removed_homework_weeks": removed_homework_weeks,
            "removed_control_weeks": removed_control_weeks
        }


homework_storage = HomeworkStorage()
