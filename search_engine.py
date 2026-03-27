from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Any, Optional
import os
import json
import re


class TokenType(Enum):
    TAG = auto()
    TEXT = auto()
    PHRASE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass
class Token:
    type: TokenType
    value: str = ""
    negative: bool = False


class ASTNode:
    pass


@dataclass
class TagNode(ASTNode):
    value: str
    negative: bool = False


@dataclass
class TextNode(ASTNode):
    value: str
    negative: bool = False


@dataclass
class PhraseNode(ASTNode):
    value: str
    negative: bool = False


@dataclass
class AndNode(ASTNode):
    left: ASTNode
    right: ASTNode


@dataclass
class OrNode(ASTNode):
    left: ASTNode
    right: ASTNode


@dataclass
class NotNode(ASTNode):
    operand: ASTNode


@dataclass
class EmptyNode(ASTNode):
    pass


class SearchEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._questions_cache: Optional[List[Dict[str, Any]]] = None
    
    def _load_questions(self) -> List[Dict[str, Any]]:
        if self._questions_cache is not None:
            return self._questions_cache
        
        questions = []
        if not os.path.exists(self.data_dir):
            return questions
        
        for filename in sorted(os.listdir(self.data_dir), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        questions.append(data)
                except (json.JSONDecodeError, IOError):
                    continue
        
        self._questions_cache = questions
        return questions
    
    def _invalidate_cache(self):
        self._questions_cache = None
    
    def _tokenize(self, query: str) -> List[Token]:
        tokens = []
        i = 0
        query_len = len(query)
        
        while i < query_len:
            char = query[i]
            
            if char == '(':
                tokens.append(Token(TokenType.LPAREN))
                i += 1
            elif char == ')':
                tokens.append(Token(TokenType.RPAREN))
                i += 1
            elif char == '-':
                if i + 1 < query_len:
                    next_char = query[i + 1]
                    if next_char == 't' and query[i:i + 5].lower() == '-tag:':
                        rest = query[i + 5:]
                        tag_end = self._find_token_end(rest)
                        tag_value = rest[:tag_end]
                        tokens.append(Token(TokenType.TAG, tag_value, negative=True))
                        i += 5 + tag_end
                    elif next_char == '(' or next_char == '"':
                        tokens.append(Token(TokenType.NOT))
                        i += 1
                    else:
                        text = self._parse_text_token(query, i + 1)
                        tokens.append(Token(TokenType.TEXT, text, negative=True))
                        i += 1 + len(text)
                else:
                    text = self._parse_text_token(query, i + 1)
                    tokens.append(Token(TokenType.TEXT, text, negative=True))
                    i += 1 + len(text)
            elif query[i:i + 3].upper() == 'AND':
                tokens.append(Token(TokenType.AND))
                i += 3
            elif query[i:i + 2].upper() == 'OR':
                tokens.append(Token(TokenType.OR))
                i += 2
            elif query[i:i + 3].upper() == 'NOT':
                tokens.append(Token(TokenType.NOT))
                i += 3
            elif char == '"':
                end = query.find('"', i + 1)
                if end == -1:
                    text = query[i + 1:]
                    tokens.append(Token(TokenType.PHRASE, text))
                    break
                else:
                    text = query[i + 1:end]
                    tokens.append(Token(TokenType.PHRASE, text))
                    i = end + 1
            elif char in ' \t':
                i += 1
            else:
                text = self._parse_text_token(query, i)
                if text.lower().startswith('tag:'):
                    tag_value = text[4:]
                    negative = tag_value.startswith('-')
                    actual_tag = tag_value[1:] if negative else tag_value
                    tokens.append(Token(TokenType.TAG, actual_tag, negative))
                else:
                    tokens.append(Token(TokenType.TEXT, text, negative=False))
                i += len(text)
        
        return tokens
    
    def _parse_text_token(self, query: str, start: int) -> str:
        end = start
        query_len = len(query)
        while end < query_len:
            char = query[end]
            if char in ' \t()\"':
                break
            end += 1
        return query[start:end]
    
    def _find_token_end(self, s: str) -> int:
        end = 0
        s_len = len(s)
        while end < s_len:
            char = s[end]
            if char in ' \t()\"':
                break
            end += 1
        return end
    
    def _parse(self, tokens: List[Token]) -> ASTNode:
        self._parse_pos = 0
        self._parse_tokens = tokens
        
        result = self._parse_expression()
        return result
    
    def _parse_expression(self) -> ASTNode:
        return self._parse_or()
    
    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        
        while (self._parse_pos < len(self._parse_tokens) and 
               self._parse_tokens[self._parse_pos].type == TokenType.OR):
            self._parse_pos += 1
            right = self._parse_and()
            left = OrNode(left, right)
        
        return left
    
    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        
        while self._parse_pos < len(self._parse_tokens):
            token = self._parse_tokens[self._parse_pos]
            
            if token.type == TokenType.AND:
                self._parse_pos += 1
                right = self._parse_not()
                left = AndNode(left, right)
            elif token.type in (TokenType.TEXT, TokenType.PHRASE, TokenType.TAG, TokenType.LPAREN):
                right = self._parse_not()
                left = AndNode(left, right)
            else:
                break
        
        return left
    
    def _parse_not(self) -> ASTNode:
        if (self._parse_pos < len(self._parse_tokens) and 
            self._parse_tokens[self._parse_pos].type == TokenType.NOT):
            self._parse_pos += 1
            operand = self._parse_atom()
            return NotNode(operand)
        
        return self._parse_atom()
    
    def _parse_atom(self) -> ASTNode:
        if self._parse_pos >= len(self._parse_tokens):
            return EmptyNode()
        
        token = self._parse_tokens[self._parse_pos]
        self._parse_pos += 1
        
        if token.type == TokenType.LPAREN:
            expr = self._parse_expression()
            if (self._parse_pos < len(self._parse_tokens) and 
                self._parse_tokens[self._parse_pos].type == TokenType.RPAREN):
                self._parse_pos += 1
            return expr
        
        if token.type == TokenType.TAG:
            return TagNode(token.value, token.negative)
        
        if token.type == TokenType.PHRASE:
            return PhraseNode(token.value, token.negative)
        
        if token.type == TokenType.TEXT:
            return TextNode(token.value, token.negative)
        
        return EmptyNode()
    
    def _create_regex(self, pattern: str) -> re.Pattern:
        escaped = re.escape(pattern)
        escaped = escaped.replace(r'\*', '.*')
        escaped = escaped.replace('_', '.')
        return re.compile(f'^{escaped}$', re.IGNORECASE)
    
    def _match_tag(self, tag: str, tags: List[str]) -> bool:
        tag_lower = tag.lower()
        tags_lower = [t.lower() for t in tags]
        
        if '*' in tag or '_' in tag:
            try:
                regex = self._create_regex(tag)
                return any(regex.fullmatch(t) for t in tags_lower)
            except re.error:
                pass
        
        if tag_lower in tags_lower:
            return True
        
        prefix = tag_lower + '::'
        if any(t.startswith(prefix) for t in tags_lower):
            return True
        
        return False
    
    def _match_text(self, text: str, question_str: str, answer_str: str) -> bool:
        try:
            regex = self._create_regex(text)
            return bool(regex.search(question_str)) or bool(regex.search(answer_str))
        except re.error:
            text_lower = text.lower()
            return text_lower in question_str or text_lower in answer_str
    
    def _match_phrase(self, phrase: str, question_str: str, answer_str: str) -> bool:
        phrase_lower = phrase.lower()
        return phrase_lower in question_str or phrase_lower in answer_str
    
    def _get_effective_tags(self, question: Dict[str, Any]) -> List[str]:
        own_tags = question.get('tags', [])
        sub_question_tags = []
        for sq in question.get('sub_questions', []):
            sub_question_tags.extend(sq.get('tags', []))
        return list(set(own_tags + sub_question_tags))
    
    def _evaluate(self, node: ASTNode, question: Dict[str, Any]) -> bool:
        question_content = question.get('question', {})
        answer_content = question.get('answer', {})
        
        question_str = json.dumps(question_content, ensure_ascii=False).lower()
        answer_str = json.dumps(answer_content, ensure_ascii=False).lower()
        tags = self._get_effective_tags(question)
        
        if isinstance(node, TagNode):
            result = self._match_tag(node.value, tags)
            return not result if node.negative else result
        
        if isinstance(node, TextNode):
            result = self._match_text(node.value, question_str, answer_str)
            return not result if node.negative else result
        
        if isinstance(node, PhraseNode):
            result = self._match_phrase(node.value, question_str, answer_str)
            return not result if node.negative else result
        
        if isinstance(node, AndNode):
            return self._evaluate(node.left, question) and self._evaluate(node.right, question)
        
        if isinstance(node, OrNode):
            return self._evaluate(node.left, question) or self._evaluate(node.right, question)
        
        if isinstance(node, NotNode):
            return not self._evaluate(node.operand, question)
        
        if isinstance(node, EmptyNode):
            return True
        
        return True
    
    def search(self, query: str, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        questions = self._load_questions()
        
        if not query or not query.strip():
            total = len(questions)
            start = (page - 1) * page_size
            end = start + page_size
            paginated = questions[start:end]
            
            return {
                "questions": paginated,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
                "search_query": query
            }
        
        tokens = self._tokenize(query)
        ast = self._parse(tokens)
        
        filtered = [q for q in questions if self._evaluate(ast, q)]
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]
        
        return {
            "questions": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "search_query": query
        }
    
    def get_all_tags(self) -> List[str]:
        questions = self._load_questions()
        tag_set = set()
        
        for q in questions:
            tags = self._get_effective_tags(q)
            tag_set.update(tags)
        
        return sorted(tag_set)
    
    def refresh(self):
        self._invalidate_cache()
