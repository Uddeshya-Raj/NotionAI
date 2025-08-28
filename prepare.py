# %%
import os
from notion_client import Client
from notion_client.errors import HTTPResponseError
import json
import time

# %%
curr_dir = os.getcwd()
token_file = os.path.join(curr_dir, 'notion_integration_token.txt')
with open(token_file, 'r') as file:
    notion_integration_token = file.read().strip()

# %%
notion = Client(auth=notion_integration_token)

# %%
def get_primary_pages_list():
    """Retrieve the list of sources from the Notion database whose parent is the workspace."""
    results = []
    next_cursor = None
    while True:
        response = notion.search(page_size=100, start_cursor=next_cursor)
        # Filter for items whose parent.type is 'workspace'
        workspace_items = [
            item.get('id', '') for item in response['results']
            if item.get('parent', {}).get('type') == 'workspace'
        ]
        results.extend(workspace_items)
        next_cursor = response.get('next_cursor')
        if not next_cursor:
            break
    return results

# %%
pages = get_primary_pages_list()
print(pages)

# %%
def show_children(
    block_id, 
    # result=None,
    retries=3, 
    delay=1
    ):
    # if result is None:
    #     result = []

    try:
        block_type = notion.blocks.retrieve(block_id=block_id)['type']
        if block_type == 'unsupported':
            return

        children = notion.blocks.children.list(block_id=block_id)['results']
        for child in children:
            # Only append if not a database without a title
            if not (
                (child.get('type') == 'child_database' and not child['child_database'].get('title', '')) or
                (child.get('type') == 'database' and not child.get('title', ''))
            ):
                print(json.dumps(child, indent=4))
                # result.append(child)
            if child.get('has_children'):
                show_children(child['id'])
    except HTTPResponseError as e:
        if retries > 0:
            print(f"Retrying due to error: {e}. Retries left: {retries}")
            time.sleep(delay)
            show_children(block_id, retries - 1, delay * 2)  # Exponential backoff
        else:
            print(f"Failed after retries. Skipping block {block_id}. Error: {e}")

    # return result

# %%
import time
import logging
from notion_client.errors import HTTPResponseError

def get_children_blocks(block_id, notion, max_retries=3, delay=1):
    """
    A page is also a block in Notion.
    Recursively retrieves all child blocks for a given Notion block ID.
    Returns a flat list of blocks. Raises an exception if retrieval fails.
    """
    result = []
    try:
        # Retrieve the block type (optional, can skip if not needed)
        block_type = notion.blocks.retrieve(block_id=block_id)['type']
        if block_type == 'unsupported':
            return result

        # Pagination handling
        next_cursor = None
        while True:
            response = notion.blocks.children.list(block_id=block_id, start_cursor=next_cursor)
            children = response['results']
            for child in children:
                if child.get('type') == 'unsupported':
                    continue
                # Skip databases without a title
                if not (
                    (child.get('type') == 'child_database' and not child['child_database'].get('title', '')) or
                    (child.get('type') == 'database' and not child.get('title', ''))
                ):
                    result.append(child)
                if child.get('has_children'):
                    # Recursively get children and extend the result
                    result.extend(get_children_blocks(child['id'], notion, max_retries, delay))
            next_cursor = response.get('next_cursor')
            if not next_cursor:
                break
    except HTTPResponseError as e:
        if max_retries > 0:
            logging.warning(f"Retrying due to error: {e}. Retries left: {max_retries}")
            time.sleep(delay)
            return get_children_blocks(block_id, notion, max_retries - 1, delay * 2)
        else:
            logging.error(f"Failed after retries. Skipping block {block_id}. Error: {e}")
            raise Exception(f"Failed after retries. Skipping block {block_id}. Error: {e}")

    return result


# %%
def extract_table_as_markdown(table_block_id):
    table_rows = notion.blocks.children.list(block_id=table_block_id)['results']
    table_data = []
    for row in table_rows:
        cells = row['table_row']['cells']
        row_text = [
            ''.join(cell_obj.get('plain_text', '') for cell_obj in cell)
            for cell in cells
        ]
        table_data.append(row_text)
    
    # Step 2: Compute the max width for each column
    num_cols = max(len(row) for row in table_data)
    col_widths = [0] * num_cols
    for row in table_data:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(cell))
    
    # Step 3: Pad each cell to column width
    def pad(cell, width):
        return cell + ' ' * (width - len(cell))
    
    padded_table = []
    for row in table_data:
        padded_row = [pad(cell, col_widths[idx]) for idx, cell in enumerate(row)]
        padded_table.append(padded_row)
    
    # Step 4: Build Markdown lines
    lines = []
    # Header
    lines.append('| ' + ' | '.join(padded_table[0]) + ' |')
    # Separator
    lines.append('|' + '|'.join(['-' * (w + 2) for w in col_widths]) + '|')
    # Data rows
    for row in padded_table[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)

# %%
def extract_simple_content(info):
    # info = notion.blocks.retrieve(block_id=block_id)
    content = ''
    block_type = info['type']

    # Equation block
    if block_type == 'equation':
        content += info['equation'].get('expression', '')

    # Table block
    elif block_type == 'table':
        table_content = extract_table_as_markdown(info.get('id', ''))
        content += table_content

    # To-do block
    elif block_type == 'to_do':
        to_do = info['to_do']
        # Extract text from rich_text
        text_content = ''.join(
            t['text']['content']
            for t in to_do.get('rich_text', [])
            if 'text' in t and 'content' in t['text']
        )
        content += text_content
        if to_do.get('checked', False):
            content += ' (done)'

    # Blocks with rich_text (paragraph, heading, etc.)
    elif "rich_text" in info.get(block_type, {}):
        rich_text = info[block_type]['rich_text']
        for text in rich_text:
            if 'text' in text and 'content' in text['text']:
                text_content = text['text']['content']
                content += text_content
            elif 'equation' in text and 'expression' in text['equation']:
                equation_content = text['equation']['expression']
                content += equation_content

    return content


# %%
def extract_property_value(prop):
    """Extracts the display value from a Notion property dict."""
    prop_type = prop.get('type')
    if prop_type == 'title':
        # Title is a list of rich_text objects
        return ''.join([t.get('plain_text', '') for t in prop['title']])
    elif prop_type == 'rich_text':
        return ''.join([t.get('plain_text', '') for t in prop['rich_text']])
    elif prop_type == 'select':
        return prop['select']['name'] if prop['select'] else ''
    elif prop_type == 'multi_select':
        return ', '.join([item['name'] for item in prop['multi_select']])
    elif prop_type == 'checkbox':
        return 'Yes' if prop['checkbox'] else 'No'
    elif prop_type == 'number':
        return str(prop['number']) if prop['number'] is not None else ''
    elif prop_type == 'date':
        if prop['date']:
            start = prop['date'].get('start')
            end = prop['date'].get('end')
            if end and end != start:
                return f"{start} – {end}"
            return start or ''
        return ''
    elif prop_type == 'people':
        return ', '.join([person.get('name', '') for person in prop['people']])
    elif prop_type == 'status':
        return prop['status']['name'] if prop['status'] else ''
    elif prop_type == 'url':
        return prop['url'] if prop['url'] else ''
    else:
        # Fallback for other types (files, formula, etc.)
        return ''

# %%
def get_notion_db_content(db_id):
    database = notion.databases.retrieve(database_id=db_id)
    rows = notion.databases.query(database_id=db_id)['results']
    # Get column names in display order (title first, then others)
    properties = database['properties']
    columns = []
    # Always put the title property first
    for key, prop in properties.items():
        if prop['type'] == 'title':
            columns.append((key, prop['name']))
    for key, prop in properties.items():
        if prop['type'] != 'title':
            columns.append((key, prop['name']))
    # Build header
    header = '| ' + ' | '.join([col[1] for col in columns]) + ' |'
    # Build separator
    separator = '| ' + ' | '.join(['---' for _ in columns]) + ' |'
    # Build rows
    table_rows = []
    for row in rows:
        props = row['properties']
        row_cells = []
        for key, _ in columns:
            value = extract_property_value(props[key])
            row_cells.append(value)
        table_rows.append('| ' + ' | '.join(row_cells) + ' |')
    # Combine all
    lines = [header, separator] + table_rows
    return '\n'.join(lines)


# %%
blocks = get_children_blocks(pages[0], notion)
for block in blocks:
    print(json.dumps(block, indent=4))

# %%
def extract_content(info):
    """
    Given a Notion block ID, extract its content appropriately:
    - If it's a database (type 'child_database' or 'database'), extract as a Markdown table.
    - If it's a table block, extract as a Markdown table.
    - Otherwise, extract as simple content.
    """
    # info = notion.blocks.retrieve(block_id=block_id)
    block_id = info.get('id', '')
    block_type = info['type']

    # Handle Notion databases (inline or top-level)
    if block_type == 'child_database' or block_type == 'database':
        # For both, the block ID is the database ID
        return get_notion_db_content(block_id)

    # Handle simple tables
    elif block_type == 'table':
        return extract_table_as_markdown(block_id)

    # Handle all other block types (paragraph, heading, to_do, etc.)
    else:
        return extract_simple_content(info)


# %%
# for block in blocks:
#     # print(json.dumps(block, indent=4))
#     x = extract_content(block['id'])
#     print(x)

# %%
def extract_children(block_id):
    children = notion.blocks.children.list(block_id=block_id)['results']
    ids = [child['id'] for child in children]
    return ids
        

# %%
def extract_caption(block):
    block_type = block.get('type')
    content_field = block.get(block_type, {})
    if 'caption' in content_field:
        return ''.join(rt.get('plain_text', '') for rt in content_field['caption'])
    return ''

# %%
def extract_comments(block_id):
    """Extracts all comment texts from a list of Notion comment objects."""
    comments_json = notion.comments.list(block_id=block_id)['results']
    comments_list = []
    for comment in comments_json:
        # Each comment's text is in the 'rich_text' field (list of rich text objects)
        text = ''.join(rt.get('plain_text', '') for rt in comment.get('rich_text', []))
        comments_list.append(text)
    return comments_list

# %%


# %%
def get_database_blocks(blocks):
    """
    Returns a list of Notion blocks that are databases (type 'child_database' or 'database').
    """
    db_blocks = []
    for block in blocks:
        if block.get('type') == 'child_database':
            title = block['child_database'].get('title', '')
            if title == '':
                continue
            db_blocks.append(block)
        elif block.get('type') == 'database':
            title = block.get('title', '')
            if title == '':
                continue
            db_blocks.append(block)
    return db_blocks

# Example usage:
# all_blocks = show_children(root_block_id)
database_blocks = get_database_blocks(blocks)
for db in database_blocks:
    db_type = db['type']
    db_id = db['id']
    if db_type == 'child_database':
        title = db['child_database'].get('title', '')
        print(f"Database Block: Title='{title}', ID={db_id}, Type={db_type}")
    elif db_type == 'database':
        title = db.get('title', '')
        print(f"Database Object: Title='{title}', ID={db_id}, Type={db_type}")


# %%
# for idx in range(len(database_blocks)):    
#     db_prop = notion.databases.retrieve(database_id=database_blocks[idx]['id'])
#     db_rows = notion.databases.query(database_id=database_blocks[idx]['id'])['results']
#     print("Database Properties:")
#     print(json.dumps(db_prop, indent=4))
#     print("-"*100)
#     print("Database Rows:")
#     print(json.dumps(db_rows, indent=4))
#     print("="*100, "\n\n")

# %%
# markdown_table = get_notion_db_content("21c4ba0f-0a3c-80b3-acd1-fc68b6c39c71")
# print(markdown_table)


# %%
def make_block_dict(block, context = None, children_map = None):
    parent = block.get('parent', {})
    parent_id = parent.get('page_id', '') or parent.get('block_id', '')
    return {
        'id': block.get('id', ''),
        'parent_id': parent_id,
        'date_created': block.get('created_time', ''),
        'date_updated': block.get('last_edited_time', ''),
        'type': block.get('type', ''),
        'content': extract_content(block),
        'context': context if context else None,
        'children': children_map.get(block.get('id', ''), []) if children_map else [],
        'caption': extract_caption(block),
        'comments': extract_comments(block.get('id', ''))
    }

# %%

def prepare_page(page_id):
    blocks = get_children_blocks(page_id, notion)
    stack = []
    page_data = []
    children_map = {}
    
    for block in blocks:
        parent_id = block.get('parent', {}).get('block_id') or block.get('parent', {}).get('page_id')
        if parent_id:
            children_map.setdefault(parent_id, []).append(block['id'])

    for block in blocks:
        if(block.get('type') == 'unsupported'):
            continue
        if "heading" in block.get('type'):
            heading_level = int(block['type'].split('_')[1])  # e.g., 'heading_1' -> 1
            while stack and stack[-1][0] >= heading_level:
                stack.pop()
            stack.append((heading_level, extract_content(block)+ '\n' + extract_caption(block)))
        else:
            block_id = block.get('id', '')
            if block_id:
                context = ' > '.join([st[1] for st in stack]) or "No heading"
            else:
                context = "No heading"
        block_dict = make_block_dict(block, context=context, children_map=children_map)
        page_data.append(block_dict)
    
    return page_data

# %%
page_data = prepare_page(pages[0])
print(json.dumps(page_data, indent=4))

# %%

