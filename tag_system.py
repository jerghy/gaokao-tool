import copy
import json
import os
import re
from typing import List, Dict


class MatchType:
    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    CONTAINS = "contains"
    REGEX = "regex"


class TagSystem:
    def __init__(self, data_path: str = "tags_data.json"):
        self.data_path = data_path
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            data = {"records": {}, "tag_tree": {}}
            self._save_data(data)
            return data

    def _save_data(self, data: dict = None) -> None:
        if data is None:
            data = self.data
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _update_tag_tree(self, tag: str) -> None:
        parts = tag.split("::")
        current = self.data["tag_tree"]
        for part in parts[:-1]:
            if part not in current:
                current[part] = {"children": {}}
            elif "children" not in current[part]:
                current[part]["children"] = {}
            current = current[part]["children"]
        if parts[-1] not in current:
            current[parts[-1]] = {}

    def _ensure_parent_tags(self, tag: str) -> None:
        parts = tag.split("::")
        if len(parts) <= 1:
            return
        current = self.data["tag_tree"]
        for part in parts[:-1]:
            if part not in current:
                current[part] = {"children": {}}
            elif "children" not in current[part]:
                current[part]["children"] = {}
            current = current[part]["children"]

    def add_tag(self, record_id: str, tag: str) -> bool:
        if record_id not in self.data["records"]:
            self.data["records"][record_id] = []
        if tag not in self.data["records"][record_id]:
            self.data["records"][record_id].append(tag)
        self._update_tag_tree(tag)
        self._save_data()
        return True

    def remove_tag(self, record_id: str, tag: str) -> bool:
        if record_id not in self.data["records"]:
            return False
        if tag not in self.data["records"][record_id]:
            return False
        self.data["records"][record_id].remove(tag)
        self._save_data()
        return True

    def batch_add_tag(self, record_ids: List[str], tag: str) -> Dict[str, bool]:
        results = {}
        for record_id in record_ids:
            results[record_id] = self.add_tag(record_id, tag)
        return results

    def batch_remove_tag(self, record_ids: List[str], tag: str) -> Dict[str, bool]:
        results = {}
        for record_id in record_ids:
            results[record_id] = self.remove_tag(record_id, tag)
        return results

    def update_tag(self, record_id: str, old_tag: str, new_tag: str) -> bool:
        if record_id not in self.data["records"]:
            return False
        if old_tag not in self.data["records"][record_id]:
            return False
        self.data["records"][record_id].remove(old_tag)
        self.data["records"][record_id].append(new_tag)
        self._update_tag_tree(old_tag)
        self._update_tag_tree(new_tag)
        self._save_data()
        return True

    def get_tags(self, record_id: str) -> List[str]:
        if record_id not in self.data["records"]:
            return []
        return self.data["records"][record_id]

    def search(self, query: str, match_type: str = "exact") -> List[str]:
        matching_records = set()
        for record_id, tags in self.data["records"].items():
            for tag in tags:
                if match_type == MatchType.EXACT:
                    if tag == query:
                        matching_records.add(record_id)
                        break
                elif match_type == MatchType.PREFIX:
                    if tag.startswith(query):
                        matching_records.add(record_id)
                        break
                elif match_type == MatchType.SUFFIX:
                    if tag.endswith(query):
                        matching_records.add(record_id)
                        break
                elif match_type == MatchType.CONTAINS:
                    if query in tag:
                        matching_records.add(record_id)
                        break
                elif match_type == MatchType.REGEX:
                    if re.search(query, tag):
                        matching_records.add(record_id)
                        break
        return list(matching_records)

    def search_by_regex(self, regex_pattern: str) -> List[str]:
        return self.search(regex_pattern, MatchType.REGEX)

    def get_records_with_tag(self, tag: str) -> List[str]:
        return self.search(tag, MatchType.EXACT)

    def _tokenize(self, query: str) -> List[tuple]:
        tokens = []
        i = 0
        while i < len(query):
            if query[i] == '(':
                tokens.append(('LPAREN', '('))
                i += 1
            elif query[i] == ')':
                tokens.append(('RPAREN', ')'))
                i += 1
            elif query[i:].startswith('AND') and (i + 3 >= len(query) or not query[i+3].isalnum()):
                tokens.append(('AND', 'AND'))
                i += 3
            elif query[i] == '|':
                tokens.append(('OR', '|'))
                i += 1
            elif query[i:].startswith('OR') and (i + 2 >= len(query) or not query[i+2].isalnum()):
                tokens.append(('OR', 'OR'))
                i += 2
            elif query[i] == '-' and (not tokens or tokens[-1][0] in ('AND', 'OR', 'LPAREN', 'NOT', 'TAG')):
                tokens.append(('NOT', '-'))
                i += 1
            elif query[i:].startswith('NOT') and (i + 3 >= len(query) or not query[i+3].isalnum()):
                tokens.append(('NOT', 'NOT'))
                i += 3
            elif query[i] == ' ':
                i += 1
            elif query[i:i+2] == '::':
                if tokens and tokens[-1][0] == 'TAG':
                    tokens[-1] = ('TAG', tokens[-1][1] + '::')
                else:
                    tokens.append(('TAG', '::'))
                i += 2
            else:
                match = re.match(r'([^\s()\-:|]+)', query[i:])
                if match:
                    tokens.append(('TAG', match.group(1)))
                    i += len(match.group(1))
                else:
                    i += 1
        return tokens

    def _get_all_records(self) -> set:
        return set(self.data["records"].keys())

    def _parse_and_evaluate(self, tokens: List[tuple], pos: int) -> tuple:
        result, pos = self._parse_or(tokens, pos)
        return result, pos

    def _parse_or(self, tokens: List[tuple], pos: int) -> tuple:
        left, pos = self._parse_and(tokens, pos)
        while pos < len(tokens) and tokens[pos][0] == 'OR':
            pos += 1
            right, pos = self._parse_and(tokens, pos)
            left = left | right
        return left, pos

    def _parse_and(self, tokens: List[tuple], pos: int) -> tuple:
        left, pos = self._parse_not(tokens, pos)
        while pos < len(tokens):
            token_type = tokens[pos][0]
            if token_type == 'AND':
                pos += 1
                right, pos = self._parse_not(tokens, pos)
                left = left & right
            elif token_type == 'TAG':
                right, pos = self._parse_not(tokens, pos)
                left = left & right
            elif token_type == 'LPAREN':
                right, pos = self._parse_not(tokens, pos)
                left = left & right
            elif token_type == 'NOT':
                pos += 1
                right, pos = self._parse_atom(tokens, pos)
                left = left - right
            else:
                break
        return left, pos

    def _parse_not(self, tokens: List[tuple], pos: int) -> tuple:
        if pos < len(tokens) and tokens[pos][0] == 'NOT':
            pos += 1
            result, pos = self._parse_atom(tokens, pos)
            return self._get_all_records() - result, pos
        return self._parse_atom(tokens, pos)

    def _parse_atom(self, tokens: List[tuple], pos: int) -> tuple:
        if pos < len(tokens):
            token_type, token_val = tokens[pos]
            if token_type == 'TAG':
                if token_val.endswith('::'):
                    records = set(self.search(token_val, MatchType.PREFIX))
                else:
                    records = set(self.get_records_with_tag(token_val))
                return records, pos + 1
            elif token_type == 'LPAREN':
                pos += 1
                result, pos = self._parse_or(tokens, pos)
                if pos < len(tokens) and tokens[pos][0] == 'RPAREN':
                    pos += 1
                return result, pos
        return set(), pos

    def search_with_operators(self, query: str) -> List[str]:
        tokens = self._tokenize(query)
        result, _ = self._parse_and_evaluate(tokens, 0)
        return list(result)

    def get_tag_tree(self) -> Dict:
        return copy.deepcopy(self.data["tag_tree"])

    def get_all_tags(self) -> List[str]:
        all_tags = []
        self._collect_tags(self.data["tag_tree"], "", all_tags)
        return sorted(all_tags)

    def _collect_tags(self, tree: Dict, prefix: str, result: List[str]) -> None:
        for tag, value in tree.items():
            full_tag = f"{prefix}{tag}" if prefix else tag
            result.append(full_tag)
            if value:
                children = value.get("children", {})
                if children:
                    self._collect_tags(children, f"{full_tag}::", result)

    def delete_tag_from_system(self, tag: str) -> bool:
        found = False
        for record_id in list(self.data["records"].keys()):
            if tag in self.data["records"][record_id]:
                self.data["records"][record_id].remove(tag)
                found = True

        if self._remove_from_tree(self.data["tag_tree"], tag):
            found = True

        if found:
            self._save_data()
        return found

    def _remove_from_tree(self, tree: Dict, tag: str) -> bool:
        parts = tag.split("::")
        if len(parts) == 1:
            if parts[0] in tree:
                del tree[parts[0]]
                return True
            return False

        current = tree
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                return False
            next_level = current[part].get("children", {})
            if i == len(parts) - 2:
                if parts[-1] in next_level:
                    del next_level[parts[-1]]
                    self._cleanup_empty_parents(current, parts, 0)
                    return True
                return False
            current = next_level
        return False

    def _cleanup_empty_parents(self, tree: Dict, parts: List[str], index: int) -> None:
        for i in range(len(parts) - 1):
            part = parts[i]
            if part in tree:
                children = tree[part].get("children", {})
                if not children:
                    del tree[part]
                    break
                tree = children