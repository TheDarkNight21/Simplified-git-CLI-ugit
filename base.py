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
    
    # Hash and store the tree object
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
            
def read_tree(tree_old): # goal of reading and writing a tree is so the user can write a tree at a point in time, and go back to look at their previous code via read_tree
    _empy_current_directory()
    for path, oid in get_tree(tree_old, base_path='./').items(): # gets path and oid of all objects in the tree
        os.makedirs(os.path.dirname(path), exist_ok=True) # makes directory (if they are there, nothing will happen)
        with open(path, 'wb') as f: # opens the directory
            f.write(data.get_object(oid)) # write the previous data
            
def _empy_current_directory():
    for root,dirnames, filenames in os.walk('.', topdown=False): # go through all items in directory
        for filename in filenames: # for each file
            path = os.path.relpath(f'{root}/{filename}') # make path
            if is_ignored(path) or not os.path.isfile(path): # if it needs to be ignored or its not a file
                continue # ignore
            os.remove(path) # remove file
        for dirname in dirnames: # go through directories
            path = os.path.relpath(f'{root}/{dirname}') # make path
            if is_ignored(path): # if its ignored
                continue # ignore it
            try:
                os.rmdir(path) # remove directory
            except (FileNotFoundError, OSError):
                pass # if its already not there or removed, ignore errors. 
            
def commit(message):
    commit = f'tree {write_tree}\n'
    HEAD = data.get_ref('HEAD') # get the head (previous commit oid)
    commit += f'parent {HEAD}\n' # display it
    commit += "\n"
    commit += f'{message}'
    
    oid = data.hash_object(commit.encode(), 'commit')
    data.update_ref('HEAD', oid)
    
    return oid

def checkout(oid):
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.update_ref('HEAD', oid)
    
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