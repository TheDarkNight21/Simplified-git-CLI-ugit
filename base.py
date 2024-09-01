import data
import os
import itertools
import operator

from collections import namedtuple


def write_tree(directory='.'):
    entries = []  # Initialize list to hold tree entries
    with os.scandir(directory) as it:  # Scan the directory
        for entry in it:
            full = f'{directory}/{entry.name}'  # Full path of the entry
            if is_ignored(full):  # Skip ignored files/folders
                continue

            if entry.is_file(follow_symlinks=False):  # If it's a file
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read())  # Create hash object for the file
                type_ = 'blob'
            elif entry.is_dir(follow_symlinks=False):  # If it's a directory
                oid = write_tree(full)  # Recursively call write_tree for subdirectory
                type_ = 'tree'

            entries.append((entry.name, oid, type_))  # Add to entries

    # Create the tree object
    tree = ''.join(f'{type_} {oid} {name}\n' for name, oid, type_ in sorted(entries))
    print(tree)
    # Hash and store the tree object
    print(data.hash_object(tree.encode(), 'tree'))
    return data.hash_object(tree.encode(), 'tree')
    
    
def _iter_tree_entries(oid): #generator that will take the oid of a tree, tokenize it line by line, and yield raw string values. 
    if not oid:
        return
    tree = data.get_object(oid, 'tree')
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(" ", 2)
        yield type_, oid, name
    
def get_tree(oid, base_path=''): # recursively parses a tree into a dictionary
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        assert '/' not in name
        assert name not in ('..','.')
        path = base_path + name
        
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update(get_tree(oid,f'{path}/'))
        else:
            assert False, f'Unknown tree entry {type_}'
            
def read_tree(tree_old, dry_run=False):
    if not dry_run:
        _empy_current_directory()
    else:
        print("[Dry-Run] Would empty current directory")

    for path, oid in get_tree(tree_old, base_path='./').items():
        if not dry_run:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data.get_object(oid))
        else:
            print(f"[Dry-Run] Would restore {path} with oid {oid}")
            
def _empy_current_directory(dry_run=False):
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')
            if is_ignored(path) or not os.path.isfile(path):
                continue
            if not dry_run:
                os.remove(path)
                print(f"File removed: {path}")
            else:
                print(f"[Dry-Run] Would remove file {path}")
        for dirname in dirnames:
            if not dry_run:
                os.rmdir(dirname)
                print(f"Directory removed: {path}")
            else:
                print(f"[Dry-Run] Would remove directory {dirname}")
            
def commit(message):
    commit = f'tree {write_tree()}\n'
    HEAD = data.get_ref('HEAD') # get the head (previous commit oid)
    commit += f'parent {HEAD}\n' # display it
    commit += "\n"
    commit += f'{message}'
    
    oid = data.hash_object(commit.encode(), 'commit')
    data.update_ref('HEAD', oid)
    
    return oid

def checkout(oid, dry_run=False):
    commit = get_commit(oid)
    print(f"Checking out commit: {commit}")
    if not dry_run:
        read_tree(commit.tree)
        data.update_ref('HEAD', oid)
    else:
        print(f"[Dry-Run] Would read tree {commit.tree} and update HEAD to {oid}")
    
def create_tag(name, oid):
    data.update_ref(f'refs/tags/{name}', oid)
   

Commit = namedtuple('Commit', ['tree', 'parent', 'message'])

def get_oid(name):
    return data.get_ref(name) or name
    
def get_commit(oid):
    oid = oid.strip()
    parent = None
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())
    
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'Unknown field {key}'
            
    message = '\n'.join(lines)
    return Commit(tree=tree, parent=parent, message=message)
    
def is_ignored (path):
    return '.ugit' in path.split ('/')