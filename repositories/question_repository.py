import json
import os
from typing import List, Dict, Any, Optional


class QuestionRepository:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def list_all(self, reverse: bool = True) -> List[Dict[str, Any]]:
        questions = []
        if not os.path.exists(self.data_dir):
            return questions
        for filename in sorted(os.listdir(self.data_dir), reverse=reverse):
            if filename.endswith('.json'):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        questions.append(data)
                except (json.JSONDecodeError, IOError):
                    continue
        return questions

    def get_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        filepath = os.path.join(self.data_dir, f"{question_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, question_data: Dict[str, Any]) -> str:
        question_id = question_data.get('id')
        filepath = os.path.join(self.data_dir, f"{question_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        return question_id

    def delete(self, question_id: str) -> bool:
        filepath = os.path.join(self.data_dir, f"{question_id}.json")
        if not os.path.exists(filepath):
            return False
        os.remove(filepath)
        return True

    def exists(self, question_id: str) -> bool:
        filepath = os.path.join(self.data_dir, f"{question_id}.json")
        return os.path.exists(filepath)

    def count(self) -> int:
        if not os.path.exists(self.data_dir):
            return 0
        return len([f for f in os.listdir(self.data_dir) if f.endswith('.json')])
