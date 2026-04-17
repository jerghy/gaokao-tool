import os
import logging
from datetime import datetime
from PIL import Image
from errors import AppError, ValidationError, NotFoundError

logger = logging.getLogger(__name__)


class QuestionService:
    def __init__(self, question_repo, tag_repo, image_manager, search_engine, img_dir, static_dir):
        self.question_repo = question_repo
        self.tag_repo = tag_repo
        self.image_manager = image_manager
        self.search_engine = search_engine
        self.img_dir = img_dir
        self.static_dir = static_dir

    def process_image_items(self, items, question_id):
        processed_items = []
        for item in items:
            if item.get('type') == 'image':
                if 'config_id' in item:
                    config_id = item['config_id']
                    update_data = {}
                    if 'display' in item:
                        update_data['display'] = item['display']
                    if 'width' in item:
                        update_data['width'] = item['width']
                    if 'height' in item:
                        update_data['height'] = item['height']
                    if 'charBox' in item:
                        update_data['charBox'] = item['charBox']
                    if 'splitLines' in item:
                        update_data['splitLines'] = item['splitLines']
                    if update_data:
                        self.image_manager.update_config(config_id, **update_data)
                    self.image_manager.add_usage(config_id, question_id)
                    processed_items.append({'type': 'image', 'config_id': config_id})
                elif 'image_id' in item or 'src' in item:
                    if 'image_id' in item:
                        image_id = item['image_id']
                    else:
                        filename = os.path.basename(item['src'])
                        existing_image = self.image_manager.get_image_by_filename(filename)
                        if existing_image:
                            image_id = existing_image['id']
                        else:
                            img_width, img_height = None, None
                            try:
                                img_path = os.path.join(self.static_dir, item['src'].lstrip('/'))
                                if os.path.exists(img_path):
                                    with Image.open(img_path) as img:
                                        img_width, img_height = img.size
                            except Exception:
                                pass
                            image_id = self.image_manager.add_image(
                                filename=filename,
                                path=item['src'],
                                width=img_width,
                                height=img_height
                            )
                    config_id = self.image_manager.create_config(
                        image_id=image_id,
                        display=item.get('display', 'center'),
                        width=item.get('width', 300),
                        height=item.get('height', 'auto'),
                        charBox=item.get('charBox'),
                        splitLines=item.get('splitLines')
                    )
                    self.image_manager.add_usage(config_id, question_id)
                    processed_items.append({'type': 'image', 'config_id': config_id})
                else:
                    processed_items.append(item)
            else:
                processed_items.append(item)
        return processed_items

    def expand_image_items(self, items):
        self.image_manager.reload()
        expanded_items = []
        for item in items:
            if item.get('type') == 'image' and 'config_id' in item:
                full_info = self.image_manager.get_full_image_info(item['config_id'])
                if full_info:
                    image_info = full_info['image']
                    natural_width = image_info.get('width')
                    natural_height = image_info.get('height')
                    if natural_width is None or natural_height is None:
                        try:
                            img_path = os.path.join(self.static_dir, image_info['path'].lstrip('/'))
                            if os.path.exists(img_path):
                                with Image.open(img_path) as img:
                                    natural_width, natural_height = img.size
                                    self.image_manager.update_image(image_info['id'], width=natural_width, height=natural_height)
                        except Exception:
                            pass
                    expanded_item = {
                        'type': 'image',
                        'config_id': item['config_id'],
                        'src': image_info['path'],
                        'display': full_info['config']['display'],
                        'width': full_info['config']['width'],
                        'height': full_info['config']['height'],
                        'naturalWidth': natural_width,
                        'naturalHeight': natural_height
                    }
                    if 'charBox' in full_info['config']:
                        expanded_item['charBox'] = full_info['config']['charBox']
                    if 'splitLines' in full_info['config']:
                        expanded_item['splitLines'] = full_info['config']['splitLines']
                    expanded_items.append(expanded_item)
                else:
                    expanded_items.append(item)
            else:
                expanded_items.append(item)
        return expanded_items

    def save_question(self, data):
        if not data:
            raise ValidationError("No data provided")

        question_id = data.get('id', datetime.now().strftime('%Y%m%d%H%M%S'))

        question_items = self.process_image_items(
            data.get('question', {}).get('items', []),
            question_id
        )
        answer_items = self.process_image_items(
            data.get('answer', {}).get('items', []),
            question_id
        )

        sub_questions = data.get('sub_questions', [])
        for sq in sub_questions:
            if 'question_text' in sq and 'items' in sq['question_text']:
                sq['question_text']['items'] = self.process_image_items(
                    sq['question_text']['items'],
                    question_id
                )

        if self.question_repo.exists(question_id):
            question_data = self.question_repo.get_by_id(question_id)

            old_tags = question_data.get('tags', [])
            new_tags = data.get('tags', old_tags)

            if old_tags != new_tags:
                for tag in old_tags:
                    self.tag_repo.remove_tag(question_id, tag)
                for tag in new_tags:
                    self.tag_repo.add_tag(question_id, tag)

            question_data['question'] = {'items': question_items}
            question_data['answer'] = {'items': answer_items}
            question_data['tags'] = new_tags
            question_data['sub_questions'] = sub_questions
        else:
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            question_data = {
                'id': question_id,
                'created_at': created_at,
                'question': {'items': question_items},
                'answer': {'items': answer_items},
                'tags': data.get('tags', []),
                'sub_questions': sub_questions
            }

            for tag in data.get('tags', []):
                self.tag_repo.add_tag(question_id, tag)

        self.question_repo.save(question_data)
        self.search_engine.refresh()

        return {
            'success': True,
            'id': question_id,
            'filename': f"{question_id}.json"
        }

    def update_question(self, question_id, data):
        if not data:
            raise ValidationError("No data provided")

        if not self.question_repo.exists(question_id):
            raise NotFoundError("Question", question_id)

        question_data = self.question_repo.get_by_id(question_id)

        question_items = self.process_image_items(
            data.get('question', {}).get('items', []),
            question_id
        )
        answer_items = self.process_image_items(
            data.get('answer', {}).get('items', []),
            question_id
        )

        sub_questions = data.get('sub_questions', question_data.get('sub_questions', []))
        for sq in sub_questions:
            if 'question_text' in sq and 'items' in sq['question_text']:
                sq['question_text']['items'] = self.process_image_items(
                    sq['question_text']['items'],
                    question_id
                )

        old_tags = question_data.get('tags', [])
        new_tags = data.get('tags', old_tags)

        if old_tags != new_tags:
            for tag in old_tags:
                self.tag_repo.remove_tag(question_id, tag)
            for tag in new_tags:
                self.tag_repo.add_tag(question_id, tag)

        question_data['question'] = {'items': question_items}
        question_data['answer'] = {'items': answer_items}
        question_data['tags'] = new_tags
        question_data['sub_questions'] = sub_questions

        self.question_repo.save(question_data)
        self.search_engine.refresh()

        expanded_question_data = question_data.copy()
        expanded_question_data['question'] = {'items': self.expand_image_items(question_data['question']['items'])}
        expanded_question_data['answer'] = {'items': self.expand_image_items(question_data['answer']['items'])}
        if 'sub_questions' in expanded_question_data:
            for sq in expanded_question_data['sub_questions']:
                if 'question_text' in sq and 'items' in sq['question_text']:
                    sq['question_text']['items'] = self.expand_image_items(sq['question_text']['items'])

        return {
            'success': True,
            'id': question_id,
            'question': expanded_question_data
        }

    def delete_question(self, question_id):
        if not self.question_repo.exists(question_id):
            raise NotFoundError("Question", question_id)

        tags = self.tag_repo.get_tags(question_id)
        for tag in tags:
            self.tag_repo.remove_tag(question_id, tag)

        self.question_repo.delete(question_id)
        self.search_engine.refresh()

        return {'success': True, 'id': question_id}

    def get_questions(self, page, page_size, search):
        if search:
            result = self.search_engine.search(search, page, page_size)
            for q in result['questions']:
                if 'question' in q and 'items' in q['question']:
                    q['question']['items'] = self.expand_image_items(q['question']['items'])
                if 'answer' in q and 'items' in q['answer']:
                    q['answer']['items'] = self.expand_image_items(q['answer']['items'])
                if 'sub_questions' in q:
                    for sq in q['sub_questions']:
                        if 'question_text' in sq and 'items' in sq['question_text']:
                            sq['question_text']['items'] = self.expand_image_items(sq['question_text']['items'])
            return result

        questions = self.question_repo.list_all()
        for data in questions:
            if 'question' in data and 'items' in data['question']:
                data['question']['items'] = self.expand_image_items(data['question']['items'])
            if 'answer' in data and 'items' in data['answer']:
                data['answer']['items'] = self.expand_image_items(data['answer']['items'])
            if 'sub_questions' in data:
                for sq in data['sub_questions']:
                    if 'question_text' in sq and 'items' in sq['question_text']:
                        sq['question_text']['items'] = self.expand_image_items(sq['question_text']['items'])

        total = len(questions)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = questions[start:end]

        return {
            'questions': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'search_query': ''
        }

    def get_training_items(self, page, page_size, search, ability_tag):
        training_items = []

        all_questions = self.question_repo.list_all()
        for data in all_questions:
            items = data.get('chinese_modern_text_training', [])
            question_id = data.get('id', '')

            for idx, item in enumerate(items):
                training_item = {
                    'id': f"{question_id}_{idx}",
                    'question_id': question_id,
                    'material': item.get('material', ''),
                    'question': item.get('question', ''),
                    'abilityPoint': item.get('abilityPoint', ''),
                    'answerAnalysis': item.get('answerAnalysis', '')
                }

                if ability_tag:
                    if not training_item['abilityPoint'].startswith(ability_tag):
                        continue

                if search:
                    search_lower = search.lower()
                    if (search_lower not in training_item['material'].lower() and
                        search_lower not in training_item['question'].lower() and
                        search_lower not in training_item['abilityPoint'].lower()):
                        continue

                training_items.append(training_item)

        total = len(training_items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = training_items[start:end]

        return {
            'success': True,
            'items': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 1
        }

    def get_training_ability_tags(self):
        tag_counts = {}

        all_questions = self.question_repo.list_all()
        for data in all_questions:
            items = data.get('chinese_modern_text_training', [])
            for item in items:
                ability_point = item.get('abilityPoint', '')
                if ability_point:
                    tag_counts[ability_point] = tag_counts.get(ability_point, 0) + 1

        def build_tag_tree(tag_counts):
            tree = {}
            for tag, count in sorted(tag_counts.items()):
                parts = tag.split('::')
                current = tree
                for i, part in enumerate(parts):
                    if part not in current:
                        current[part] = {'children': {}, 'count': 0}
                    current[part]['count'] += count
                    current = current[part]['children']
            return tree

        tag_tree = build_tag_tree(tag_counts)
        total_count = sum(tag_counts.values())

        return {
            'success': True,
            'tag_tree': tag_tree,
            'all_tags': sorted(list(tag_counts.keys())),
            'tag_counts': tag_counts,
            'total_count': total_count
        }

    def get_questions_with_difficulties(self):
        questions = []

        all_questions = self.question_repo.list_all()
        for data in all_questions:
            difficulties = data.get('chemistry_preprocessing', {}).get('Difficulties', [])
            if not difficulties:
                continue

            preview_text = ''
            items = data.get('question', {}).get('items', [])
            for item in items:
                if item.get('type') == 'richtext':
                    content = item.get('content', '')
                    if content:
                        preview_text = content[:100]
                        break
                elif item.get('type') == 'text':
                    text = item.get('text', '')
                    if text:
                        preview_text = text[:100]
                        break

            questions.append({
                'id': data.get('id'),
                'created_at': data.get('created_at'),
                'preview_text': preview_text,
                'tags': data.get('tags', []),
                'difficulty_count': len(difficulties),
                'selected_difficulty_ids': data.get('selected_difficulty_ids', []),
                'chemistry_preprocessing': data.get('chemistry_preprocessing', {})
            })

        questions.sort(key=lambda q: (
            len(q.get('selected_difficulty_ids', [])) == 0,
            q.get('created_at', '')
        ), reverse=True)

        return {
            'success': True,
            'questions': questions,
            'total': len(questions)
        }

    def update_selected_difficulties(self, question_id, selected_difficulty_ids):
        if not self.question_repo.exists(question_id):
            raise NotFoundError("Question", question_id)

        try:
            question_data = self.question_repo.get_by_id(question_id)
            question_data['selected_difficulty_ids'] = selected_difficulty_ids
            self.question_repo.save(question_data)

            return {
                'success': True,
                'id': question_id,
                'selected_difficulty_ids': selected_difficulty_ids
            }
        except Exception as e:
            logger.error(f"Error updating selected difficulties for {question_id}: {str(e)}")
            raise AppError("UPDATE_ERROR", f"Failed to update selected difficulties: {str(e)}", 500)

    def batch_add_tag(self, record_ids, tag):
        if not record_ids or not tag:
            raise ValidationError("record_ids and tag are required")

        results = self.tag_repo.batch_add_tag(record_ids, tag)

        for record_id in record_ids:
            if results[record_id]:
                if self.question_repo.exists(record_id):
                    question_data = self.question_repo.get_by_id(record_id)
                    if tag not in question_data.get('tags', []):
                        question_data['tags'] = question_data.get('tags', []) + [tag]
                        self.question_repo.save(question_data)

        self.search_engine.refresh()

        return {
            'success': True,
            'results': results
        }
