from tag_system import TagSystem
from typing import List, Dict


class TagRepository:
    def __init__(self, data_path: str):
        self._tag_system = TagSystem(data_path=data_path)

    @property
    def tag_system(self) -> TagSystem:
        return self._tag_system

    def add_tag(self, record_id: str, tag: str) -> bool:
        return self._tag_system.add_tag(record_id, tag)

    def remove_tag(self, record_id: str, tag: str) -> bool:
        return self._tag_system.remove_tag(record_id, tag)

    def batch_add_tag(self, record_ids: List[str], tag: str) -> Dict[str, bool]:
        return self._tag_system.batch_add_tag(record_ids, tag)

    def get_tags(self, record_id: str) -> List[str]:
        return self._tag_system.get_tags(record_id)

    def get_tag_tree(self) -> Dict:
        return self._tag_system.get_tag_tree()

    def get_all_tags(self) -> List[str]:
        return self._tag_system.get_all_tags()

    def search_with_operators(self, query: str) -> List[str]:
        return self._tag_system.search_with_operators(query)

    def initialize_from_data(self, data_dir: str):
        import os
        import json
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    record_id = data.get('id')
                    tags = data.get('tags', [])
                    if record_id:
                        for tag in tags:
                            self._tag_system.add_tag(record_id, tag)
