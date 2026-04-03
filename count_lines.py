#!/usr/bin/env python3
"""
代码行数统计工具
递归统计指定文件夹中代码文件的行数，支持排除目录和自定义扩展名。
"""

import os
import argparse
from pathlib import Path

# 默认统计的代码文件扩展名
DEFAULT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.h', '.hpp',
    '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.kts', '.scala', '.html',
    '.htm', '.css', '.scss', '.less', '.vue', '.svelte', '.xml', '.json', '.yaml',
    '.yml', '.toml', '.ini', '.sh', '.bash', '.zsh', '.ps1', '.pl', '.lua', '.r',
    '.m', '.mm', '.sql'
}

# 默认统计的特殊文件名（无扩展名但常见的代码文件）
DEFAULT_SPECIAL_NAMES = {
    'Makefile', 'Dockerfile', '.gitignore', '.dockerignore', 'CMakeLists.txt',
    'Cargo.toml', 'Cargo.lock', 'Gemfile', 'Rakefile', 'Vagrantfile'
}

# 默认排除的目录（版本控制、缓存、虚拟环境等）
DEFAULT_EXCLUDE_DIRS = {
    '.git', '__pycache__', 'node_modules', '.vscode', '.idea', 'dist', 'build',
    'venv', 'env', '.venv', '.mypy_cache', '.pytest_cache', '.cache', 'target'
}


def count_lines(file_path):
    """
    统计文件的行数（文本模式，UTF-8编码，忽略解码错误）
    返回行数，若无法读取则返回0并打印警告
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"警告：无法读取文件 {file_path} - {e}")
        return 0


def is_code_file(file_path, extensions, use_default_ext=True, special_names=None):
    """
    判断是否为需要统计的代码文件
    :param file_path: 文件路径（Path对象或字符串）
    :param extensions: 用户指定的扩展名集合（带点，小写）
    :param use_default_ext: 是否使用默认扩展名（当extensions为空时生效）
    :param special_names: 特殊文件名集合（无扩展名）
    """
    path = Path(file_path)
    if not path.is_file():
        return False

    suffix = path.suffix.lower()
    # 如果用户指定了扩展名，仅匹配这些扩展名
    if extensions:
        return suffix in extensions
    # 否则使用默认扩展名或特殊文件名
    if use_default_ext and suffix in DEFAULT_EXTENSIONS:
        return True
    if special_names and path.name in special_names:
        return True
    return False


def walk_directory(root_path, exclude_dirs, extensions, special_names):
    """
    遍历目录，生成所有符合条件的代码文件路径
    """
    root_path = os.path.abspath(root_path)
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # 原地修改 dirnames 以排除指定目录
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if is_code_file(file_path, extensions, special_names=special_names):
                yield file_path


def main():
    parser = argparse.ArgumentParser(
        description='统计文件夹内代码文件的行数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  %(prog)s                        # 统计当前目录\n'
               '  %(prog)s /path/to/project       # 统计指定目录\n'
               '  %(prog)s -e .py .js --summary   # 仅统计.py和.js，输出总计\n'
               '  %(prog)s -x test .git --no-default-exclude  # 不排除默认目录，额外排除test和.git'
    )
    parser.add_argument('path', nargs='?', default='.',
                        help='要统计的文件夹路径（默认为当前目录）')
    parser.add_argument('-e', '--extensions', nargs='+', metavar='EXT',
                        help='要统计的文件扩展名（例如 .py .js），可指定多个，覆盖默认扩展名')
    parser.add_argument('-x', '--exclude-dirs', nargs='+', metavar='DIR',
                        help='额外排除的目录名（默认已排除 .git, node_modules 等）')
    parser.add_argument('--no-default-exclude', action='store_true',
                        help='不使用默认排除目录列表')
    parser.add_argument('--no-special-names', action='store_true',
                        help='不统计特殊文件名（如 Makefile, Dockerfile 等）')
    parser.add_argument('--summary', action='store_true',
                        help='仅输出总计行数和文件数，不列出每个文件')

    args = parser.parse_args()

    # 处理扩展名
    extensions = None
    if args.extensions:
        # 标准化扩展名（确保带点且小写）
        extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions}
        extensions = {ext.lower() for ext in extensions}

    # 处理特殊文件名
    special_names = None if args.no_special_names else DEFAULT_SPECIAL_NAMES

    # 处理排除目录
    exclude_dirs = set()
    if not args.no_default_exclude:
        exclude_dirs.update(DEFAULT_EXCLUDE_DIRS)
    if args.exclude_dirs:
        exclude_dirs.update(args.exclude_dirs)

    root_path = args.path

    # 统计
    total_lines = 0
    file_count = 0
    file_results = []

    for file_path in walk_directory(root_path, exclude_dirs, extensions, special_names):
        lines = count_lines(file_path)
        if lines is not None:
            total_lines += lines
            file_count += 1
            rel_path = os.path.relpath(file_path, start=root_path)
            file_results.append((rel_path, lines))

    # 输出结果
    if not args.summary:
        print(f"统计文件夹: {os.path.abspath(root_path)}")
        print("-" * 50)
        for rel_path, lines in sorted(file_results):
            print(f"{rel_path}: {lines} 行")
        print("-" * 50)

    print(f"总计代码行数: {total_lines} 行")
    print(f"统计文件数: {file_count}")


if __name__ == '__main__':
    main()