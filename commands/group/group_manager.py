"""
Менеджер для работы с данными группы
"""
import json
import os
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class Role(str, Enum):
    STAROSTA = "Староста"
    ZAM_STAROSTA = "Зам старосты"
    PROFORG = "Профорг"
    PARTICIPANT = "Участник"
    GUEST = "Гость"


class GroupManager:
    
    def __init__(self, data_file: str = "data/group_data.json"):
        self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self._save_data({"members": {}})
    
    def _load_data(self) -> dict:
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"members": {}}
    
    def _save_data(self, data: dict):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_member(self, user_id: int) -> Optional[dict]:
        data = self._load_data()
        return data["members"].get(str(user_id))
    
    def is_member_registered(self, user_id: int) -> bool:
        return self.get_member(user_id) is not None
    
    def add_member(self, user_id: int, telegram_username: Optional[str], 
                   full_name: str, birth_date: str, notifications: dict,
                   is_guest: bool = False):
        data = self._load_data()
        
        role = Role.GUEST.value if is_guest else Role.PARTICIPANT.value
        
        data["members"][str(user_id)] = {
            "user_id": user_id,
            "telegram_username": telegram_username,
            "full_name": full_name,
            "birth_date": birth_date,
            "notifications": notifications,  
            "role": role,
            "registered_at": datetime.now().isoformat()
        }
        self._save_data(data)
    
    def update_member(self, user_id: int, full_name: Optional[str] = None, 
                     birth_date: Optional[str] = None, 
                     notifications: Optional[dict] = None,
                     role: Optional[Role] = None):
        data = self._load_data()
        if str(user_id) not in data["members"]:
            return False
        
        member = data["members"][str(user_id)]
        
        if full_name is not None:
            member["full_name"] = full_name
        if birth_date is not None:
            member["birth_date"] = birth_date
        if notifications is not None:
            member["notifications"] = notifications
        if role is not None:
            if role in [Role.STAROSTA, Role.ZAM_STAROSTA, Role.PROFORG]:
                for member_id, member_data in data["members"].items():
                    if member_data["role"] == role.value:
                        member_data["role"] = Role.PARTICIPANT.value
            member["role"] = role.value
        
        self._save_data(data)
        return True
    
    def get_all_members(self) -> Dict[str, dict]:
        data = self._load_data()
        return data["members"]
    
    def get_members_by_role(self, role: Role) -> List[dict]:
        data = self._load_data()
        return [member for member in data["members"].values() 
                if member["role"] == role.value]
    
    def get_headman(self) -> Optional[dict]:
        headmen = self.get_members_by_role(Role.STAROSTA)
        return headmen[0] if headmen else None


group_manager = GroupManager()
