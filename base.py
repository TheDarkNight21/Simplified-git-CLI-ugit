import data
import os
import itertools
import operator
import string
import data
import diff

from collections import namedtuple
from collections import deque, namedtuple

def init():
    data.init()
    data.update_ref('HEAD', data.RefValue(symbolic=True, value='refs/header/master'))


def write_tree(directory='.'):
    index_as_tree = {}
    with data.get_index () as index:
        for path, oid in index.items ():
            path = path.split ('/')
            dirpath, filename = path[:-1], path[-1]

            current = index_as_tree
            # Find the dict for the directory of this file
            for dirname in dirpath:
                current = current.setdefault (dirname, {})
            current[filename] = oid

    def write_tree_recursive (tree_dict):
        entries = []
        for name, value in tree_dict.items ():
            if type (value) is dict:  # Recursively call write_tree for subdirectory
                type_ = 'tree'
                oid = write_tree_recursive(value)
            else:
                type_ = 'blob'
                oid = value
            entries.append((name, oid, type_))
    # Create the tree object
        tree = ''.join(f'{type_} {oid} {name}\n' for name, oid, type_ in sorted(entries))
    # Hash and store the tree object
        return data.hash_object(tree.encode(), 'tree')
    return write_tree_recursive (index_as_tree)
    
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
            
def read_tree (tree_oid, update_working=False):
    with data.get_index () as index:
        index.clear ()
        index.update (get_tree (tree_oid))

        if update_working:
            _checkout_index (index)


def _checkout_index (index):
    _empty_current_directory()
    for path, oid in index.items():
        os.markedirs(os.path.dirname(f'./{path}'), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid, 'blob'))
            
def get_working_tree():
    result = {}
    for root, _, filenames in os.walk('.'):
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')
            if is_ignored(path) or not os.path.isfile(path):
                continue
            with open(path, 'rb') as f:
                result[path] = data.hash_object(f.read())
    return result
            
def get_index_tree():
    with data.get_index() as index:
        return index

def _empty_current_directory(dry_run=False):
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')
            try:
                if is_ignored(path) or not os.path.isfile(path):
                    continue
                os.remove(path)
                print(f"File removed: {path}")    
            except FileNotFoundError:
                print(f"File not Found: {path}, skipping.")
            except Exception as e:
                print(f"Error deleting file {path}: {e}")
                
        for dirname in dirnames:
            try:
                os.rmdir(dirname)
                print(f"Directory removed: {path}")
            except OSError as e:
                print(f"Error deleting directory {path}: {e}")


def read_tree_merged(t_base, t_HEAD, t_other):
    _empty_current_directory()
    for path, blob in diff.merge_trees(get_tree(t_base), get_tree(t_HEAD),(t_other)).items():
        os.makedirs(f'./{os.path.dirname(path)}', exist_ok=True)
        with open(path, 'wb') as f:
            f.write(blob)
            
def commit(message):
    commit = f'tree {write_tree()}\n'
    HEAD = data.get_ref('HEAD').value # get the head (previous commit oid)
    if HEAD:
        commit += f'parent {HEAD}\n' # display it
    MERGE_HEAD = data.get_ref('MERGE_HEAD').value
    if MERGE_HEAD:
        commit += f'parent {MERGE_HEAD}\n'
        data.delete_ref('MERGE_HEAD', deref=False)
    commit += "\n"
    commit += f'{message}'
    
    oid = data.hash_object(commit.encode(), 'commit')
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))
    
    return oid

def checkout(name):
    oid = get_oid(name)
    commit = get_commit(oid)
    print(f"Checking out commit: {commit}")
    read_tree(commit.tree, update_working=True)
    
    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=f'refs/heads/{name}')
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)
        
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))
    
def reset(oid):
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))
    
def merge(other):
    HEAD = data.get_ref('HEAD').value
    assert HEAD
    merge_base = get_merge_base(other, HEAD)
    c_other = get_commit(other)
    
    if merge_base == HEAD:
        read_tree(c_other.tree, update_working=True)
        data.update_ref('HEAD',
                        data.RefValue(symbolic=False, value=other))
        print('Fast-forwad merge, no need to commit')
        return 
    
    data.update_ref('MERGE_HEAD', data.RefValue(symbolic=False, value=other))
    
    c_base = get_commit (merge_base)
    c_HEAD = get_commit (HEAD)
    read_tree_merged(c_base.tree, c_HEAD.tree, c_other.tree, update_working=True)
    print('Merged in working tree\nPlease commit')
    
def get_merge_base(oid1, oid2):
    parents1 = set(iter_commits_and_parents({oid1}))
    
    for oid in iter_commits_and_parents({oid2}):
        if oid in parents1:
            return oid
    
def create_tag(name, oid):
    data.update_ref(f'refs/tags/{name}', data.RefValue(symbolic=False, value=oid))
   
def create_branch(name, oid):
    data.update_ref(f'refs/heads/{name}', data.RefValue(symbolic=False, value=oid))
    
def iter_branch_names():
    for refname, _ in data.iter_refs('refs/heads/'):
        yield os.path.relpath(refname, 'refs/heads/')    
    
def is_branch(branch):
    return data.get_ref(f'refs/heads/{branch}').value is not None

def is_ancestor_of(commit, maybe_ancestor):
    return maybe_ancestor in iter_commits_and_parents({commit})

def get_branch_name():
    HEAD = data.get_ref('HEAD', deref=False)
    if not HEAD.symbolic:
        return None
    HEAD = HEAD.value
    assert HEAD.startswith('refs/heads/')
    return os.path.relpath(HEAD, 'refs/heads')

Commit = namedtuple('Commit', ['tree', 'parents', 'message'])

def iter_commits_and_parents(oids):
    oids = deque(oids)
    visited = set()
    
def iter_objects_in_commits (oids):
    visited = set()
    visited.add (oid)
    yield oid
    for type_, oid, _ in _iter_tree_entries (oid):
        if oid not in visited:
            if type_ == 'tree':
                yield from iter_objects_in_commits (oid)
            else:
                visited.add (oid)
                yield oid

    for oid in iter_commits_and_parents (oids):
        yield oid
        commit = get_commit (oid)
        if commit.tree not in visited:
           yield from iter_objects_in_commits (commit.tree)

def get_oid(name):
    if name == "@": name = 'HEAD'
    refs_to_try = [
        f'{name}',
        f'refs/{name}',
        f'refs/tags/{name}',
        f'refts/heads/{name}',
    ]
    for ref in refs_to_try:
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref).value
        
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name
    
    assert False, f'Unknown name {name}'
    
def get_commit(oid):
    parents = []
    oid = oid.strip()
    if not oid or oid == "None":
        return
    parent = None
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())
    
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parents.append(value)
        else:
            assert False, f'Unknown field {key}'
            
    message = '\n'.join(lines)
    return Commit(tree=tree, parents=parents, message=message)

    
def add (filenames):
    
    def add_file (filename):
        # Normalize path
        filename = os.path.relpath (filename)
        with open (filename, 'rb') as f:
            oid = data.hash_object (f.read ())
        index[filename] = oid
 
    def add_directory (dirname):
        for root, _, filenames in os.walk (dirname):
            for filename in filenames:
                 # Normalize path
                 path = os.path.relpath (f'{root}/{filename}')
                 if is_ignored (path) or not os.path.isfile (path):
                     continue
                 add_file (path)
    
    with data.get_index () as index:
        for name in filenames:
            if os.path.isfile (name):
                add_file (name)
            elif os.path.isdir (name):
                add_directory (name)

def is_ignored (path):
    return '.ugit' in path.split ('/')