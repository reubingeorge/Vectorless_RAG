"""
PageIndex Tree Generation Algorithm
Adapted from: https://github.com/VectifyAI/PageIndex
Simplified for microservice architecture
"""

import asyncio
import copy
import json
import logging
import math
import random
from typing import List, Dict, Any, Tuple, Optional

from utils import (
    ChatGPT_API_async, count_tokens, extract_json, get_json_content,
    write_node_id, get_page_tokens, add_node_text, add_node_text_with_labels,
    add_preface_if_needed, post_processing, convert_physical_index_to_int,
    list_to_tree, generate_summaries_for_structure, get_number_of_pages
)

logger = logging.getLogger(__name__)


# ============================================================================
# TOC Detection
# ============================================================================

async def toc_detector_single_page(content: str, model: str, api_key: str, max_retries: int = 3) -> str:
    """Detect if a single page contains table of contents."""
    prompt = f"""Your job is to detect if there is a table of content provided in the given text.

Given text: {content}

return the following JSON format:
{{
    "thinking": "<why do you think there is a table of content in the given text>",
    "toc_detected": "<yes or no>"
}}

Directly return the final JSON structure. Do not output anything else.
Please note: abstract, summary, notation list, figure list, table list, etc. are not table of contents."""

    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    json_content = extract_json(response)
    return json_content.get('toc_detected', 'no')


async def find_toc_pages(start_page_index: int, page_list: List[Tuple[str, int]], toc_check_page_num: int, model: str, api_key: str, max_retries: int = 3) -> List[int]:
    """Find all pages that contain table of contents."""
    logger.info('Finding TOC pages...')
    last_page_is_yes = False
    toc_page_list = []
    i = start_page_index

    while i < len(page_list):
        if i >= toc_check_page_num and not last_page_is_yes:
            break

        detected_result = await toc_detector_single_page(page_list[i][0], model, api_key, max_retries)
        if detected_result == 'yes':
            logger.info(f'Page {i} has TOC')
            toc_page_list.append(i)
            last_page_is_yes = True
        elif detected_result == 'no' and last_page_is_yes:
            logger.info(f'Found the last page with TOC: {i-1}')
            break
        i += 1

    if not toc_page_list:
        logger.info('No TOC found')

    return toc_page_list


async def toc_extractor(page_list: List[Tuple[str, int]], toc_page_list: List[int], model: str, api_key: str, max_retries: int = 3) -> Dict[str, Any]:
    """Extract table of contents from detected pages."""
    toc_text = "\n\n".join([page_list[i][0] for i in toc_page_list])

    prompt = f"""Extract the table of contents from the following text.

Text:
{toc_text}

Return JSON:
{{
    "toc_content": "<extracted table of contents>",
    "page_index_given_in_toc": "<yes or no - are page numbers included?>"
}}

Return only JSON."""

    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    return extract_json(response)


# ============================================================================
# TOC Transformation
# ============================================================================

async def toc_transformer(toc_content: str, model: str, api_key: str, max_retries: int = 3) -> List[Dict]:
    """Transform raw TOC text into structured JSON format."""
    prompt = """You are given a table of contents. Transform it into JSON format with structure indices (1, 1.1, 1.2, etc.).

Response format:
{
    "table_of_contents": [
        {"structure": "<x.x.x>", "title": "<section_title>", "page": <page_number or None>}
    ]
}

Transform the full table of contents in one pass. Return only JSON."""

    prompt += '\nGiven table of contents:\n' + toc_content
    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)

    result = extract_json(response)
    toc_list = result.get('table_of_contents', [])

    # Convert page numbers to integers
    for item in toc_list:
        if 'page' in item and isinstance(item['page'], str):
            try:
                item['page'] = int(item['page'])
            except ValueError:
                item['page'] = None

    return toc_list


# ============================================================================
# TOC Processing
# ============================================================================

async def process_no_toc(page_list: List[Tuple[str, int]], start_index: int, model: str, api_key: str, max_retries: int = 3) -> List[Dict]:
    """Process document without TOC by generating structure from content."""
    logger.info("Processing document without TOC...")

    page_contents = []
    token_lengths = []

    for page_index in range(start_index, start_index + len(page_list)):
        page_text = f"<physical_index_{page_index}>\n{page_list[page_index-start_index][0]}\n</physical_index_{page_index}>\n\n"
        page_contents.append(page_text)
        token_lengths.append(count_tokens(page_text, model))

    # Group pages to fit token limits
    group_texts = page_list_to_group_text(page_contents, token_lengths)
    logger.info(f'Created {len(group_texts)} page groups')

    # Generate TOC from first group
    toc_with_page_number = await generate_toc_init(group_texts[0], model, api_key)

    # Continue with remaining groups
    for group_text in group_texts[1:]:
        toc_additional = await generate_toc_continue(toc_with_page_number, group_text, model, api_key)
        toc_with_page_number.extend(toc_additional)

    logger.info(f'Generated TOC: {len(toc_with_page_number)} items')

    toc_with_page_number = convert_physical_index_to_int(toc_with_page_number)
    return toc_with_page_number


def page_list_to_group_text(page_contents: List[str], token_lengths: List[int], max_tokens: int = 20000, overlap_page: int = 1) -> List[str]:
    """Group pages into chunks respecting token limits."""
    num_tokens = sum(token_lengths)

    if num_tokens <= max_tokens:
        return ["".join(page_contents)]

    subsets = []
    current_subset = []
    current_token_count = 0

    expected_parts_num = math.ceil(num_tokens / max_tokens)
    average_tokens_per_part = math.ceil(((num_tokens / expected_parts_num) + max_tokens) / 2)

    for i, (page_content, page_tokens) in enumerate(zip(page_contents, token_lengths)):
        if current_token_count + page_tokens > average_tokens_per_part:
            subsets.append(''.join(current_subset))
            overlap_start = max(i - overlap_page, 0)
            current_subset = page_contents[overlap_start:i]
            current_token_count = sum(token_lengths[overlap_start:i])

        current_subset.append(page_content)
        current_token_count += page_tokens

    if current_subset:
        subsets.append(''.join(current_subset))

    return subsets


async def generate_toc_init(part: str, model: str, api_key: str) -> List[Dict]:
    """Generate initial TOC structure from document beginning."""
    prompt = """Extract hierarchical tree structure. Structure indices: 1, 1.1, 1.2, etc.

Pages contain <physical_index_X> tags marking page boundaries.

Return JSON format:
[{"structure": "<x.x.x>", "title": "<section_title>", "physical_index": "<physical_index_X>"}]

Return only JSON."""

    prompt += '\nDocument:\n' + part
    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    return extract_json(response)


async def generate_toc_continue(toc_content: List[Dict], part: str, model: str, api_key: str) -> List[Dict]:
    """Continue TOC structure for subsequent document sections."""
    prompt = """Continue tree structure from previous part. Use hierarchy indices.

Pages contain <physical_index_X> tags.

Return JSON format:
[{"structure": "<x.x.x>", "title": "<original_title>", "physical_index": "<physical_index_X>"}]

Return only additional JSON entries."""

    prompt += '\nText:\n' + part + '\nPrevious structure:\n' + json.dumps(toc_content, indent=2)
    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    return extract_json(response)


# ============================================================================
# Title Verification
# ============================================================================

async def check_title_appearance(item: Dict, page_list: List[Tuple[str, int]], start_index: int, model: str, api_key: str) -> Dict:
    """Verify if section title appears on specified page."""
    title = item['title']
    if 'physical_index' not in item or item['physical_index'] is None:
        return {'list_index': item.get('list_index'), 'answer': 'no', 'title': title, 'page_number': None}

    page_number = item['physical_index']
    page_text = page_list[page_number - start_index][0]

    prompt = f"""Check if the section appears in the page text. Use fuzzy matching.

Section title: {title}
Page text: {page_text}

Return JSON:
{{"thinking": "<reasoning>", "answer": "yes or no"}}

Return only JSON."""

    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    response_json = extract_json(response)
    answer = response_json.get('answer', 'no')
    return {'list_index': item['list_index'], 'answer': answer, 'title': title, 'page_number': page_number}


async def check_title_appearance_in_start_concurrent(structure: List[Dict], page_list: List[Tuple[str, int]], model: str, api_key: str) -> List[Dict]:
    """Check if multiple section titles start at page beginning concurrently."""
    logger.info("Checking title appearance at page start...")

    for item in structure:
        if item.get('physical_index') is None:
            item['appear_start'] = 'no'

    tasks = []
    valid_items = []
    for item in structure:
        if item.get('physical_index') is not None:
            page_text = page_list[item['physical_index'] - 1][0]
            tasks.append(check_title_appearance_in_start(item['title'], page_text, model, api_key))
            valid_items.append(item)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for item, result in zip(valid_items, results):
        if isinstance(result, Exception):
            item['appear_start'] = 'no'
        else:
            item['appear_start'] = result

    return structure


async def check_title_appearance_in_start(title: str, page_text: str, model: str, api_key: str) -> str:
    """Check if title starts at beginning of page."""
    prompt = f"""Check if section starts at page beginning. Other content before title means 'no'.

Section title: {title}
Page text: {page_text}

Return JSON:
{{"thinking": "<reasoning>", "start_begin": "yes or no"}}

Return only JSON."""

    response = await ChatGPT_API_async(model, prompt, api_key, max_retries)
    response_json = extract_json(response)
    return response_json.get("start_begin", "no")


async def verify_toc(page_list: List[Tuple[str, int]], list_result: List[Dict], start_index: int, model: str, api_key: str, N: Optional[int] = None) -> Tuple[float, List[Dict]]:
    """Verify TOC accuracy by sampling."""
    logger.info('Verifying TOC...')

    last_physical_index = None
    for item in reversed(list_result):
        if item.get('physical_index') is not None:
            last_physical_index = item['physical_index']
            break

    if last_physical_index is None or last_physical_index < len(page_list) / 2:
        return 0, []

    if N is None:
        sample_indices = range(0, len(list_result))
    else:
        N = min(N, len(list_result))
        sample_indices = random.sample(range(0, len(list_result)), N)

    indexed_sample_list = []
    for idx in sample_indices:
        item = list_result[idx]
        if item.get('physical_index') is not None:
            item_with_index = item.copy()
            item_with_index['list_index'] = idx
            indexed_sample_list.append(item_with_index)

    tasks = [
        check_title_appearance(item, page_list, start_index, model, api_key)
        for item in indexed_sample_list
    ]
    results = await asyncio.gather(*tasks)

    correct_count = 0
    incorrect_results = []
    for result in results:
        if result['answer'] == 'yes':
            correct_count += 1
        else:
            incorrect_results.append(result)

    checked_count = len(results)
    accuracy = correct_count / checked_count if checked_count > 0 else 0
    logger.info(f"TOC Accuracy: {accuracy*100:.2f}%")
    return accuracy, incorrect_results


# ============================================================================
# Large Node Processing
# ============================================================================

async def process_large_node_recursively(node: Dict, page_list: List[Tuple[str, int]], config: Dict, model: str, api_key: str) -> Dict:
    """Recursively process large document sections."""
    node_page_list = page_list[node['start_index']-1:node['end_index']]
    token_num = sum([page[1] for page in node_page_list])

    max_pages = config.get('max_page_num_each_node', 10)
    max_tokens = config.get('max_token_num_each_node', 20000)

    if node['end_index'] - node['start_index'] > max_pages and token_num >= max_tokens:
        logger.info(f"Processing large node: {node['title']}")

        # Generate structure for this node
        node_toc_tree = await process_no_toc(node_page_list, node['start_index'], model, api_key)
        node_toc_tree = await check_title_appearance_in_start_concurrent(node_toc_tree, page_list, model, api_key)

        valid_node_toc_items = [item for item in node_toc_tree if item.get('physical_index') is not None]

        if valid_node_toc_items and node['title'].strip() == valid_node_toc_items[0]['title'].strip():
            node['nodes'] = post_processing(valid_node_toc_items[1:], node['end_index'])
            node['end_index'] = valid_node_toc_items[1]['start_index'] if len(valid_node_toc_items) > 1 else node['end_index']
        else:
            node['nodes'] = post_processing(valid_node_toc_items, node['end_index'])
            node['end_index'] = valid_node_toc_items[0]['start_index'] if valid_node_toc_items else node['end_index']

    if 'nodes' in node and node['nodes']:
        tasks = [
            process_large_node_recursively(child_node, page_list, config, model, api_key)
            for child_node in node['nodes']
        ]
        await asyncio.gather(*tasks)

    return node


# ============================================================================
# Main Tree Parser
# ============================================================================

async def page_index_main(pdf_path: Any, config: Dict, api_key: str, progress_callback=None) -> Dict:
    """
    Main entry point for PageIndex tree generation.

    Args:
        pdf_path: Path to PDF file or BytesIO object
        config: Configuration dictionary with PageIndex settings
        api_key: OpenAI API key
        progress_callback: Optional async callback function for progress updates

    Returns:
        Tree structure with nodes
    """
    model = config.get('model', 'gpt-4o-2024-11-20')
    toc_check_page_num = config.get('toc_check_page_num', 20)
    max_retry = config.get('max_retry', 3)
    if_add_node_id = config.get('if_add_node_id', True)
    if_add_node_summary = config.get('if_add_node_summary', False)
    if_add_node_text = config.get('if_add_node_text', False)

    logger.info("Starting PageIndex tree generation...")
    logger.info(f"Using max_retry={max_retry}")

    if progress_callback:
        await progress_callback(35, "Extracting text from PDF pages...")

    # Extract text and tokens from all pages
    page_list = get_page_tokens(pdf_path, model=model, pdf_parser="PyPDF2")
    logger.info(f"Extracted {len(page_list)} pages")

    if progress_callback:
        await progress_callback(40, f"Extracted {len(page_list)} pages from PDF")

    # Detect TOC
    if progress_callback:
        await progress_callback(45, "Detecting table of contents...")

    toc_page_list = await find_toc_pages(0, page_list, toc_check_page_num, model, api_key, max_retry)

    if len(toc_page_list) > 0:
        logger.info(f"Found TOC on pages: {toc_page_list}")
        if progress_callback:
            await progress_callback(50, f"Found TOC on {len(toc_page_list)} pages, extracting structure...")

        toc_json = await toc_extractor(page_list, toc_page_list, model, api_key, max_retry)

        if toc_json.get('page_index_given_in_toc') == 'yes':
            logger.info("TOC has page numbers")
            if progress_callback:
                await progress_callback(55, "TOC contains page numbers, transforming to tree structure...")
            toc_with_page_number = await toc_transformer(toc_json['toc_content'], model, api_key, max_retry)
            # Convert 'page' field to 'physical_index'
            for item in toc_with_page_number:
                if 'page' in item:
                    item['physical_index'] = item['page']
                    del item['page']
        else:
            logger.info("TOC without page numbers, generating structure...")
            if progress_callback:
                await progress_callback(55, "TOC without page numbers, analyzing document structure...")
            toc_with_page_number = await process_no_toc(page_list, 1, model, api_key, max_retry)
    else:
        logger.info("No TOC found, generating structure from content...")
        if progress_callback:
            await progress_callback(50, "No TOC found, analyzing document content to build structure...")
        toc_with_page_number = await process_no_toc(page_list, 1, model, api_key, max_retry)

    # Add preface if needed
    toc_with_page_number = add_preface_if_needed(toc_with_page_number)
    logger.info(f"After add_preface: {len(toc_with_page_number)} items")

    # Verify titles appear at page start
    logger.info("Checking title appearance at page start...")
    if progress_callback:
        await progress_callback(60, "Verifying section titles in document...")

    toc_with_page_number = await check_title_appearance_in_start_concurrent(toc_with_page_number, page_list, model, api_key)
    logger.info(f"After title check: {len(toc_with_page_number)} items")

    # Filter valid items
    valid_toc_items = [item for item in toc_with_page_number if item.get('physical_index') is not None]
    logger.info(f"Valid items with physical_index: {len(valid_toc_items)}")
    if len(valid_toc_items) > 0:
        logger.info(f"First valid item: {valid_toc_items[0]}")

    # Build tree structure
    logger.info("Building tree structure...")
    if progress_callback:
        await progress_callback(65, f"Building hierarchical tree from {len(valid_toc_items)} sections...")

    toc_tree = post_processing(valid_toc_items, len(page_list))
    logger.info(f"Tree after post_processing: type={type(toc_tree)}, len={len(toc_tree) if isinstance(toc_tree, list) else 'N/A'}")

    # Process large nodes recursively
    if progress_callback:
        await progress_callback(70, "Processing large sections recursively...")

    tasks = [
        process_large_node_recursively(node, page_list, config, model, api_key)
        for node in toc_tree
    ]
    await asyncio.gather(*tasks)

    # Add node IDs
    if if_add_node_id:
        if progress_callback:
            await progress_callback(75, "Adding unique node identifiers...")
        write_node_id(toc_tree, 0)

    # Add text to nodes
    if progress_callback:
        await progress_callback(78, "Adding text content to nodes...")

    if if_add_node_text:
        add_node_text(toc_tree, page_list)
    else:
        add_node_text_with_labels(toc_tree, page_list)

    # Generate summaries
    if if_add_node_summary:
        logger.info("Generating node summaries...")
        if progress_callback:
            await progress_callback(82, "Generating AI summaries for each node...")
        toc_tree = await generate_summaries_for_structure(toc_tree, model, api_key)

    logger.info("PageIndex tree generation complete!")

    # Debug: Log tree structure
    logger.info(f"Tree type: {type(toc_tree)}")
    logger.info(f"Tree value: {toc_tree}")
    if isinstance(toc_tree, dict):
        logger.info(f"Tree keys: {toc_tree.keys()}")
    elif isinstance(toc_tree, list):
        logger.info(f"Tree list length: {len(toc_tree)}")
        if toc_tree:
            logger.info(f"First item type: {type(toc_tree[0])}")
            logger.info(f"First item: {toc_tree[0]}")

    # Count nodes in the tree structure
    def count_nodes(tree):
        """Recursively count all nodes in the tree"""
        if not tree:
            return 0
        if isinstance(tree, dict):
            count = 1  # Count this node
            if 'nodes' in tree and tree['nodes']:
                for child in tree['nodes']:
                    count += count_nodes(child)
            return count
        elif isinstance(tree, list):
            return sum(count_nodes(item) for item in tree)
        return 0

    num_nodes = count_nodes(toc_tree)
    logger.info(f"Tree contains {num_nodes} nodes")

    return {
        'tree': toc_tree,
        'num_pages': len(page_list),
        'num_nodes': num_nodes
    }
