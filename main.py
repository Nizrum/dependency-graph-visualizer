import os
import zlib
import subprocess
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
            commit_data['date'] = datetime.fromtimestamp(timestamp)
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


def find_last_commit_before_date(commit_hash, cutoff_date, config):
    """
    Рекурсивно находит последний коммит, сделанный до cutoff_date.
    """
    current_commit = parse_object(commit_hash, config)

    if current_commit['type'] != 'commit':
        return None

    if not current_commit.get('date') or current_commit['date'] > cutoff_date:
        for parent in current_commit.get('parents', []):
            result = find_last_commit_before_date(parent, cutoff_date, config)
            if result:
                return result
        return None

    return commit_hash


def build_commit_graph(starting_commit, cutoff_date, config):
    """
    Построение полного графа зависимостей с включением trees и blobs.
    """
    visited = set()
    stack = [starting_commit]
    graph = {}

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        node = parse_object(current, config)
        if node['type'] == 'commit' and node.get('date') and node['date'] > cutoff_date:
            continue

        graph[current] = node
        stack.extend(child['hash'] for child in node['children'])

    return graph[starting_commit]


def generate_plantuml(graph, output_path):
    """
    Генерация файла PlantUML с включением commit, tree и blob объектов.
    """
    with open(output_path, 'w') as f:
        f.write('@startuml\n')
        f.write('skinparam linetype ortho\n')

        def write_node_relations(node):
            node_label = f'"{node["label"]}"'
            for child in node['children']:
                child_label = f'"{child["label"]}"'
                f.write(f'{node_label} --> {child_label}\n')
                write_node_relations(child)

        write_node_relations(graph)

        f.write('@enduml\n')


def generate_graph_image(visualizer_path, plantuml_path):
    """
    Генерирует изображение с графом с помощью PlantUML и возвращает путь к созданному изображению.
    """
    output_image = plantuml_path.replace('.puml', '.png')
    subprocess.run(["java", "-jar", visualizer_path, "-tpng", plantuml_path])
    return output_image


def open_image(image_path):
    """
    Открывает изображение с графом в стандартной программе просмотра.
    """
    if os.name == 'posix':  # macOS или Linux
        subprocess.run(["open", image_path])
    elif os.name == 'nt':  # Windows
        subprocess.run(["start", image_path], shell=True)
    else:
        print(f"Не удалось автоматически открыть файл: {image_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Visualize git commit dependencies.")
    parser.add_argument('--visualizer', required=True, help='Path to the PlantUML executable.')
    parser.add_argument('--repo-path', required=True, help='Path to the git repository.')
    parser.add_argument('--date', required=True, help='Cutoff date for commits (YYYY-MM-DD).')
    args = parser.parse_args()

    config = {"repo_path": args.repo_path}
    cutoff_date = datetime.strptime(args.date, '%Y-%m-%d')

    head_path = os.path.join(config['repo_path'], '.git', 'refs', 'heads', 'master')
    with open(head_path, 'r') as f:
        last_commit = f.read().strip()

    starting_commit = find_last_commit_before_date(last_commit, cutoff_date, config)
    if not starting_commit:
        print(f"No commits found before {cutoff_date}.")
        return

    graph = build_commit_graph(starting_commit, cutoff_date, config)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    plantuml_path = os.path.join(script_dir, 'graph.puml')

    generate_plantuml(graph, plantuml_path)

    image_path = generate_graph_image(args.visualizer, plantuml_path)
    open_image(image_path)


if __name__ == "__main__":
    main()
