import os
import unittest
from datetime import datetime
from main import (
    parse_object, parse_commit, parse_tree, find_last_commit_before_date,
    build_commit_graph, generate_plantuml, generate_graph_image
)


class TestGitDependencyGraph(unittest.TestCase):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_path = os.path.join(script_dir, 'test-repo')
    config = {"repo_path": repo_path}

    def test_parse_commit(self):
        raw_commit_content = (
            b"tree abcdef1234567890abcdef1234567890abcdef12\n"
            b"parent 1234567890abcdef1234567890abcdef12345678\n"
            b"author Test User <test@example.com> 1672531199 +0000\n"
            b"committer Test User <test@example.com> 1672531199 +0000\n\n"
            b"Initial commit\n"
        )
        commit_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t"
        result = parse_commit(commit_hash, raw_commit_content)

        self.assertEqual(result['hash'], commit_hash)
        self.assertEqual(result['tree'], "abcdef1234567890abcdef1234567890abcdef12")
        self.assertEqual(result['parents'], ["1234567890abcdef1234567890abcdef12345678"])
        self.assertEqual(result['date'], datetime(2023, 1, 1, 2, 59, 59))
        self.assertEqual(result['message'], "Initial commit")

    def test_parse_object(self):
        commit_hash = "f70b0e4ba9d2b0ccae84d415419080da1e86ea10"
        result = parse_object(commit_hash, self.config)

        self.assertEqual(result['type'], 'commit')
        self.assertEqual(result['label'], '[commit] add first.txt in branch master')
        self.assertEqual(result['date'], datetime(2024, 12, 4, 17, 21, 7))
        self.assertEqual(result['children'], [{'type': 'tree', 'hash': '66dac8d5243886b9ef0ce5c9bc912f86056fed8b', 'label': '[tree] 66dac8', 'children': [{'type': 'blob', 'hash': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 'label': '[blob] first.txt', 'children': []}]}])

    def test_parse_tree(self):
        raw_content = b'100644 first.txt\x00\xe6\x9d\xe2\x9b\xb2\xd1\xd6CK\x8b)\xaewZ\xd8\xc2\xe4\x8cS\x91100644 third.txt\x00\xe6\x9d\xe2\x9b\xb2\xd1\xd6CK\x8b)\xaewZ\xd8\xc2\xe4\x8cS\x91'
        result = parse_tree(raw_content, self.config)

        self.assertIn('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', map(lambda x: x['hash'], result))

    def test_find_last_commit_before_date(self):
        head_path = os.path.join(self.config['repo_path'], '.git', 'refs', 'heads', 'master')
        with open(head_path, 'r') as f:
            last_commit = f.read().strip()

        result = find_last_commit_before_date(last_commit, datetime(2024, 12, 5), self.config)
        self.assertEqual(result, 'd30136ebf8ad8431b8ae1adb05fa5feb9741f922')

    def test_build_commit_graph(self):
        head_path = os.path.join(self.config['repo_path'], '.git', 'refs', 'heads', 'master')
        with open(head_path, 'r') as f:
            last_commit = f.read().strip()
        starting_commit = find_last_commit_before_date(last_commit, datetime(2024, 12, 30), self.config)

        graph = build_commit_graph(starting_commit, datetime(2024, 12, 30), self.config)
        
        self.assertEqual(graph['hash'], 'd30136ebf8ad8431b8ae1adb05fa5feb9741f922')
        self.assertIn('e06d1ad04c2710e792b5a9675bc005c430dbe848', list(map(lambda x: x['hash'], graph['children'])))
        self.assertIn('2f10084116afabe2e128b779bb60a5715f94bcb6', list(map(lambda x: x['hash'], graph['children'])))
        self.assertIn('ed004bc5d19f57490b343ae91d1ee4cf26243f8a', list(map(lambda x: x['hash'], graph['children'])))

    def test_generate_plantuml(self):
        head_path = os.path.join(self.config['repo_path'], '.git', 'refs', 'heads', 'master')
        with open(head_path, 'r') as f:
            last_commit = f.read().strip()
        starting_commit = find_last_commit_before_date(last_commit, datetime(2024, 12, 30), self.config)

        graph = build_commit_graph(starting_commit, datetime(2024, 12, 30), self.config)
        plantuml_path = os.path.join(self.script_dir, 'graph.puml')

        generate_plantuml(graph, plantuml_path)

        self.assertTrue(os.path.exists(plantuml_path))

    def test_generate_graph_image(self):
        head_path = os.path.join(self.config['repo_path'], '.git', 'refs', 'heads', 'master')
        with open(head_path, 'r') as f:
            last_commit = f.read().strip()
        starting_commit = find_last_commit_before_date(last_commit, datetime(2024, 12, 30), self.config)

        graph = build_commit_graph(starting_commit, datetime(2024, 12, 30), self.config)
        plantuml_path = os.path.join(self.script_dir, 'graph.puml')

        generate_plantuml(graph, plantuml_path)
        generate_graph_image(os.path.join(self.script_dir, 'plantuml-1.2024.8.jar'), plantuml_path)

        self.assertTrue(os.path.exists(plantuml_path.replace('.puml', '.png')))


if __name__ == "__main__":
    unittest.main()
