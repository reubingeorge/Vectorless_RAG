"""
Utility functions for PageIndex tree generation.
Adapted from: https://github.com/VectifyAI/PageIndex
"""

import tiktoken
import json
import logging
import asyncio
import pypdf
import copy
import pymupdf
from io import BytesIO
from typing import Optional, List, Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4o-2024-11-20") -> int:
    """Count tokens in text using tiktoken."""
    if not text:
        return 0
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return len(tokens)


async def ChatGPT_API_async(model: str, prompt: str, api_key: str, max_retries: int = 3) -> str:
    """Call OpenAI Chat API asynchronously with retries."""
    messages = [{"role": "user", "content": prompt}]

    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0,
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"ChatGPT API error (attempt {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                await asyncio.sleep(1)
            else:
                logger.error(f'Max retries reached for prompt: {prompt[:100]}...')
                return "Error"


def get_json_content(response: str) -> str:
    """Extract JSON content from markdown code blocks."""
    start_idx = response.find("```json")
    if start_idx != -1:
        start_idx += 7
        response = response[start_idx:]

    end_idx = response.rfind("```")
    if end_idx != -1:
        response = response[:end_idx]

    json_content = response.strip()
    return json_content


def extract_json(content: str) -> Dict[str, Any]:
    """Extract and parse JSON from response string."""
    try:
        start_idx = content.find("```json")
        if start_idx != -1:
            start_idx += 7
            end_idx = content.rfind("```")
            json_content = content[start_idx:end_idx].strip()
        else:
            json_content = content.strip()

        json_content = json_content.replace('None', 'null')
        json_content = json_content.replace('\n', ' ').replace('\r', ' ')
        json_content = ' '.join(json_content.split())

        return json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to extract JSON: {e}")
        try:
            json_content = json_content.replace(',]', ']').replace(',}', '}')
            return json.loads(json_content)
        except:
            logger.error("Failed to parse JSON even after cleanup")
            return {}
    except Exception as e:
        logger.error(f"Unexpected error while extracting JSON: {e}")
        return {}


def write_node_id(data: Any, node_id: int = 0) -> int:
    """Add sequential node IDs to tree structure."""
    if isinstance(data, dict):
        data['node_id'] = str(node_id).zfill(4)
        node_id += 1
        for key in list(data.keys()):
            if 'nodes' in key:
                node_id = write_node_id(data[key], node_id)
    elif isinstance(data, list):
        for index in range(len(data)):
            node_id = write_node_id(data[index], node_id)
    return node_id


def get_nodes(structure: Any) -> List[Dict]:
    """Get all nodes from tree structure (flatten)."""
    if isinstance(structure, dict):
        structure_node = copy.deepcopy(structure)
        structure_node.pop('nodes', None)
        nodes = [structure_node]
        for key in list(structure.keys()):
            if 'nodes' in key:
                nodes.extend(get_nodes(structure[key]))
        return nodes
    elif isinstance(structure, list):
        nodes = []
        for item in structure:
            nodes.extend(get_nodes(item))
        return nodes
    return []


def structure_to_list(structure: Any) -> List[Dict]:
    """Convert nested tree structure to flat list."""
    if isinstance(structure, dict):
        nodes = []
        nodes.append(structure)
        if 'nodes' in structure:
            nodes.extend(structure_to_list(structure['nodes']))
        return nodes
    elif isinstance(structure, list):
        nodes = []
        for item in structure:
            nodes.extend(structure_to_list(item))
        return nodes
    return []


def get_leaf_nodes(structure: Any) -> List[Dict]:
    """Get only leaf nodes from tree structure."""
    if isinstance(structure, dict):
        if not structure.get('nodes'):
            structure_node = copy.deepcopy(structure)
            structure_node.pop('nodes', None)
            return [structure_node]
        else:
            leaf_nodes = []
            for key in list(structure.keys()):
                if 'nodes' in key:
                    leaf_nodes.extend(get_leaf_nodes(structure[key]))
            return leaf_nodes
    elif isinstance(structure, list):
        leaf_nodes = []
        for item in structure:
            leaf_nodes.extend(get_leaf_nodes(item))
        return leaf_nodes
    return []


def get_page_tokens(pdf_path: Any, model: str = "gpt-4o-2024-11-20", pdf_parser: str = "PyPDF2") -> List[Tuple[str, int]]:
    """Extract text and token counts from each page of PDF."""
    enc = tiktoken.encoding_for_model(model)

    if pdf_parser == "PyPDF2":
        if isinstance(pdf_path, BytesIO):
            pdf_reader = pypdf.PdfReader(pdf_path)
        else:
            pdf_reader = pypdf.PdfReader(pdf_path)

        page_list = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            token_length = len(enc.encode(page_text))
            page_list.append((page_text, token_length))
        return page_list

    elif pdf_parser == "PyMuPDF":
        if isinstance(pdf_path, BytesIO):
            pdf_stream = pdf_path
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
        elif isinstance(pdf_path, str):
            doc = pymupdf.open(pdf_path)

        page_list = []
        for page in doc:
            page_text = page.get_text()
            token_length = len(enc.encode(page_text))
            page_list.append((page_text, token_length))
        return page_list
    else:
        raise ValueError(f"Unsupported PDF parser: {pdf_parser}")


def get_text_of_pdf_pages(pdf_pages: List[Tuple[str, int]], start_page: int, end_page: int) -> str:
    """Get concatenated text from page range."""
    text = ""
    for page_num in range(start_page-1, end_page):
        text += pdf_pages[page_num][0]
    return text


def get_text_of_pdf_pages_with_labels(pdf_pages: List[Tuple[str, int]], start_page: int, end_page: int) -> str:
    """Get text from page range with physical index labels."""
    text = ""
    for page_num in range(start_page-1, end_page):
        text += f"<physical_index_{page_num+1}>\n{pdf_pages[page_num][0]}\n</physical_index_{page_num+1}>\n"
    return text


def list_to_tree(data: List[Dict]) -> List[Dict]:
    """Convert flat list with structure field to nested tree."""
    def get_parent_structure(structure):
        if not structure:
            return None
        parts = str(structure).split('.')
        return '.'.join(parts[:-1]) if len(parts) > 1 else None

    nodes = {}
    root_nodes = []

    for item in data:
        structure = item.get('structure')
        node = {
            'title': item.get('title'),
            'start_index': item.get('start_index'),
            'end_index': item.get('end_index'),
            'nodes': []
        }

        nodes[structure] = node
        parent_structure = get_parent_structure(structure)

        if parent_structure:
            if parent_structure in nodes:
                nodes[parent_structure]['nodes'].append(node)
            else:
                root_nodes.append(node)
        else:
            root_nodes.append(node)

    def clean_node(node):
        if not node['nodes']:
            del node['nodes']
        else:
            for child in node['nodes']:
                clean_node(child)
        return node

    return [clean_node(node) for node in root_nodes]


def add_preface_if_needed(data: List[Dict]) -> List[Dict]:
    """Add preface node if document doesn't start at page 1."""
    if not isinstance(data, list) or not data:
        return data

    if data[0].get('physical_index') is not None and data[0]['physical_index'] > 1:
        preface_node = {
            "structure": "0",
            "title": "Preface",
            "physical_index": 1,
        }
        data.insert(0, preface_node)
    return data


def post_processing(structure: List[Dict], end_physical_index: int) -> List[Dict]:
    """Post-process structure to add start/end indices and convert to tree."""
    for i, item in enumerate(structure):
        item['start_index'] = item.get('physical_index')
        if i < len(structure) - 1:
            if structure[i + 1].get('appear_start') == 'yes':
                item['end_index'] = structure[i + 1]['physical_index'] - 1
            else:
                item['end_index'] = structure[i + 1]['physical_index']
        else:
            item['end_index'] = end_physical_index

    tree = list_to_tree(structure)
    if len(tree) != 0:
        return tree
    else:
        for node in structure:
            node.pop('appear_start', None)
            node.pop('physical_index', None)
        return structure


def add_node_text(node: Any, pdf_pages: List[Tuple[str, int]]) -> None:
    """Recursively add text content to nodes from PDF pages."""
    if isinstance(node, dict):
        start_page = node.get('start_index')
        end_page = node.get('end_index')
        if start_page and end_page:
            node['text'] = get_text_of_pdf_pages(pdf_pages, start_page, end_page)
        if 'nodes' in node:
            add_node_text(node['nodes'], pdf_pages)
    elif isinstance(node, list):
        for index in range(len(node)):
            add_node_text(node[index], pdf_pages)


def add_node_text_with_labels(node: Any, pdf_pages: List[Tuple[str, int]]) -> None:
    """Recursively add labeled text content to nodes."""
    if isinstance(node, dict):
        start_page = node.get('start_index')
        end_page = node.get('end_index')
        if start_page and end_page:
            node['text'] = get_text_of_pdf_pages_with_labels(pdf_pages, start_page, end_page)
        if 'nodes' in node:
            add_node_text_with_labels(node['nodes'], pdf_pages)
    elif isinstance(node, list):
        for index in range(len(node)):
            add_node_text_with_labels(node[index], pdf_pages)


async def generate_node_summary(node: Dict, model: str, api_key: str) -> str:
    """Generate AI summary for a node's content."""
    prompt = f"""You are given a part of a document, your task is to generate a description of the partial document about what are main points covered in the partial document.

Partial Document Text: {node['text']}

Directly return the description, do not include any other text.
"""
    response = await ChatGPT_API_async(model, prompt, api_key)
    return response


async def generate_summaries_for_structure(structure: Any, model: str, api_key: str) -> Any:
    """Generate summaries for all nodes in structure."""
    nodes = structure_to_list(structure)
    tasks = [generate_node_summary(node, model=model, api_key=api_key) for node in nodes]
    summaries = await asyncio.gather(*tasks)

    for node, summary in zip(nodes, summaries):
        node['summary'] = summary
    return structure


def remove_fields(data: Any, fields: List[str] = ['text']) -> Any:
    """Remove specified fields from structure recursively."""
    if isinstance(data, dict):
        return {k: remove_fields(v, fields)
            for k, v in data.items() if k not in fields}
    elif isinstance(data, list):
        return [remove_fields(item, fields) for item in data]
    return data


def convert_physical_index_to_int(data: Any) -> Any:
    """Convert physical_index tags to integers."""
    if isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], dict) and 'physical_index' in data[i]:
                if isinstance(data[i]['physical_index'], str):
                    if data[i]['physical_index'].startswith('<physical_index_'):
                        data[i]['physical_index'] = int(data[i]['physical_index'].split('_')[-1].rstrip('>').strip())
                    elif data[i]['physical_index'].startswith('physical_index_'):
                        data[i]['physical_index'] = int(data[i]['physical_index'].split('_')[-1].strip())
    elif isinstance(data, str):
        if data.startswith('<physical_index_'):
            data = int(data.split('_')[-1].rstrip('>').strip())
        elif data.startswith('physical_index_'):
            data = int(data.split('_')[-1].strip())
        if isinstance(data, int):
            return data
        else:
            return None
    return data


def get_number_of_pages(pdf_path: Any) -> int:
    """Get total number of pages in PDF."""
    if isinstance(pdf_path, BytesIO):
        pdf_reader = pypdf.PdfReader(pdf_path)
    else:
        pdf_reader = pypdf.PdfReader(pdf_path)
    return len(pdf_reader.pages)
