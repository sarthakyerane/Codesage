"""
Multi-language parser using tree-sitter.
Extracts functions, call graphs, and complexity scores.
"""
import re
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger

try:
    from tree_sitter_languages import get_language, get_parser
    TS_AVAILABLE = True
except Exception:
    TS_AVAILABLE = False
    logger.warning("tree-sitter not available, using regex fallback")

# extension -> (tree-sitter lang, display name)
EXTENSION_MAP = {
    ".cpp": ("cpp", "C++"), ".cc": ("cpp", "C++"), ".cxx": ("cpp", "C++"),
    ".c": ("c", "C"), ".h": ("cpp", "C++"), ".hpp": ("cpp", "C++"),
    ".py": ("python", "Python"), ".js": ("javascript", "JavaScript"),
    ".ts": ("typescript", "TypeScript"), ".jsx": ("javascript", "JavaScript"),
    ".tsx": ("typescript", "TypeScript"), ".java": ("java", "Java"),
    ".go": ("go", "Go"), ".rs": ("rust", "Rust"),
    ".rb": ("ruby", "Ruby"), ".php": ("php", "PHP"),
}
SUPPORTED_EXTENSIONS = set(EXTENSION_MAP.keys())

# AST node types that represent functions in each language
FUNC_NODES = {
    "cpp": ["function_definition"], "c": ["function_definition"],
    "python": ["function_definition"], "javascript": ["function_declaration", "arrow_function"],
    "typescript": ["function_declaration", "arrow_function"],
    "java": ["method_declaration"], "go": ["function_declaration"],
    "rust": ["function_item"], "ruby": ["method"], "php": ["function_definition"],
}

COMPLEXITY_KW = {"if", "else", "for", "while", "switch", "case", "catch", "&&", "||", "?"}


def get_language_from_filename(filename):
    for ext, info in EXTENSION_MAP.items():
        if filename.lower().endswith(ext):
            return info
    return None, None


@dataclass
class ParsedFunction:
    name: str
    return_type: str
    parameters: str
    body: str
    line_start: int
    line_end: int
    language: str = "unknown"
    calls: list[str] = field(default_factory=list)
    complexity: int = 1
    tags: list[str] = field(default_factory=list)


class MultiLanguageParser:
    def parse_file(self, source_code, file_path=""):
        ts_lang, _ = get_language_from_filename(file_path)
        if not ts_lang:
            return self._regex_parse(source_code, "unknown")
        if TS_AVAILABLE:
            try:
                return self._ts_parse(source_code, ts_lang)
            except Exception as e:
                logger.warning(f"tree-sitter failed: {e}, falling back to regex")
        return self._regex_parse(source_code, ts_lang)

    def _ts_parse(self, src, lang):
        parser = get_parser(lang)
        tree = parser.parse(bytes(src, "utf8"))
        node_types = FUNC_NODES.get(lang, ["function_definition"])
        fns = []

        def visit(node):
            if node.type in node_types:
                fn = self._extract_fn(node, src, lang)
                if fn: fns.append(fn)
            for c in node.children:
                visit(c)
        visit(tree.root_node)
        return fns

    def _extract_fn(self, node, src, lang):
        try:
            name = self._get_name(node, src)
            if not name: return None
            body = src[node.start_byte:node.end_byte]
            ret = self._get_return_type(node, src)
            params = self._get_params(node, src)
            return ParsedFunction(
                name=name, return_type=ret, parameters=params, body=body,
                line_start=node.start_point[0]+1, line_end=node.end_point[0]+1,
                language=lang, calls=self._find_calls(body),
                complexity=self._calc_complexity(body),
                tags=self._make_tags(name, body, lang),
            )
        except Exception:
            return None

    def _get_name(self, node, src):
        for c in node.children:
            if c.type == "identifier":
                return src[c.start_byte:c.end_byte]
            if c.type in ("function_declarator", "declarator", "name"):
                for s in c.children:
                    if s.type == "identifier":
                        return src[s.start_byte:s.end_byte]
                return src[c.start_byte:c.end_byte]
        return ""

    def _get_return_type(self, node, src):
        for c in node.children:
            if c.type in ("primitive_type", "type_identifier", "type_annotation"):
                return src[c.start_byte:c.end_byte]
        return ""

    def _get_params(self, node, src):
        for c in node.children:
            if c.type in ("parameter_list", "parameters", "formal_parameters"):
                return src[c.start_byte:c.end_byte]
            if c.type in ("function_declarator", "declarator"):
                for s in c.children:
                    if s.type in ("parameter_list", "parameters"):
                        return src[s.start_byte:s.end_byte]
        return "()"

    # regex fallback for when tree-sitter isn't available
    def _regex_parse(self, src, lang):
        fns = []
        pattern = re.compile(r'(?P<ret>[\w:*&<>\s]+?)\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{', re.MULTILINE)
        skip = {"if", "while", "for", "switch", "catch"}
        for m in pattern.finditer(src):
            name = m.group("name")
            if name in skip: continue
            brace = src.index("{", m.end()-1)
            body, end = self._match_braces(src, brace)
            fns.append(ParsedFunction(
                name=name, return_type=m.group("ret").strip(),
                parameters=m.group("params"), body=body,
                line_start=src[:m.start()].count("\n")+1,
                line_end=src[:end].count("\n")+1,
                language=lang, calls=self._find_calls(body),
                complexity=self._calc_complexity(body),
                tags=self._make_tags(name, body, lang),
            ))
        return fns

    def _match_braces(self, src, start):
        depth = 0
        for i in range(start, len(src)):
            if src[i] == "{": depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0: return src[start:i+1], i
        return src[start:], len(src)

    def _find_calls(self, body):
        skip = {"if", "while", "for", "switch", "return", "sizeof", "print", "len"}
        calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', body)
        return list({c for c in calls if c not in skip})

    def _calc_complexity(self, body):
        tokens = re.findall(r'\b\w+\b|[&|?]', body)
        return 1 + sum(1 for t in tokens if t in COMPLEXITY_KW)

    def _make_tags(self, name, body, lang):
        tags = []
        text = (name + body).lower()
        if any(k in text for k in ["graph", "edge", "dijkstra", "bfs", "dfs"]): tags.append("graph")
        if any(k in text for k in ["sort", "merge", "quick"]): tags.append("sort")
        if any(k in text for k in ["tree", "bst", "inorder"]): tags.append("tree")
        if any(k in text for k in ["dp[", "memo", "knapsack"]): tags.append("dp")
        if any(k in text for k in ["new ", "delete", "malloc", "free"]): tags.append("memory")
        if lang not in ("cpp", "c"): tags.append(lang)
        return tags

    def build_call_graph(self, functions):
        known = {f.name for f in functions}
        return {f.name: [c for c in f.calls if c in known] for f in functions}


_parser_instance = None

def get_parser_instance():
    global _parser_instance
    if not _parser_instance:
        _parser_instance = MultiLanguageParser()
    return _parser_instance
