import os
import zlib
from datetime import datetime


def parse_object(object_hash, config, description=None):
    """
    Извлечь информацию из git-объекта (commit, tree, blob).
    """
    object_path = os.path.join(config['repo_path'], '.git', 'objects', object_hash[:2], object_hash[2:])
    with open(object_path, 'rb') as file:
        raw_object_content = zlib.decompress(file.read())
        header, raw_object_body = raw_object_content.split(b'\x00', maxsplit=1)
        object_type, _ = header.decode().split(' ')

    object_dict = {'type': object_type, 'hash': object_hash, 'label': object_hash[:6], 'children': []}

    if object_type == 'commit':
        commit_data = parse_commit(object_hash, raw_object_body)
        object_dict['label'] = f"[commit] {commit_data['message']}"
        object_dict['date'] = commit_data['date']
        object_dict['parents'] = commit_data['parents']
        if commit_data['tree']:
            object_dict['children'].append(parse_object(commit_data['tree'], config))
        object_dict['children'] += [parse_object(parent, config) for parent in commit_data['parents']]
    elif object_type == 'tree':
        object_dict['label'] = f"[tree] {object_hash[:6]}"
        object_dict['children'] = parse_tree(raw_object_body, config)
    elif object_type == 'blob':
        object_dict['label'] = f"[blob] {description or object_hash[:6]}"
    
    return object_dict


def parse_commit(commit_hash, raw_content):
    """
    Парсинг git-объекта коммита, включая информацию о дереве, родителях, дате и сообщении.
    """
    content = raw_content.decode()
    lines = content.split('\n')

    commit_data = {
        'hash': commit_hash,
        'message': '',
        'parents': [],
        'tree': None,
        'date': None
    }

    for line in lines:
        if line.startswith('tree '):
            commit_data['tree'] = line.split()[1]
        elif line.startswith('parent '):
            commit_data['parents'].append(line.split()[1])
        elif line.startswith('author '):
            parts = line.split()
            timestamp = int(parts[-2])
            commit_data['date'] = datetime.utcfromtimestamp(timestamp)
        elif line.strip() == '':
            commit_data['message'] = '\n'.join(lines[lines.index(line) + 1:]).strip()
            break

    return commit_data


def parse_tree(raw_content, config):
    """
    Парсинг git-объекта дерева.
    """
    children = []
    rest = raw_content

    while rest:
        mode, rest = rest.split(b' ', maxsplit=1)
        name, rest = rest.split(b'\x00', maxsplit=1)
        sha1, rest = rest[:20].hex(), rest[20:]
        children.append(parse_object(sha1, config, description=name.decode()))

    return children
