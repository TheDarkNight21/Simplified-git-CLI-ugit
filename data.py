# Refactoring and minor cleanup of functions in data.py

import os
import hashlib
import shutil
import json

from collections import namedtuple
from contextlib import contextmanager

GIT_DIR = None

@contextmanager
def get_index ():
    index = {}
    if os.path.isfile (f'{GIT_DIR}/index'):
        with open (f'{GIT_DIR}/index') as f:
            index = json.load (f)

    yield index
    with open (f'{GIT_DIR}/index', 'w') as f:
        json.dump (index, f)

def init():
    """Initializes the repository by creating necessary directories."""
    os.makedirs(GIT_DIR, exist_ok=True)
    os.makedirs(f'{GIT_DIR}/objects', exist_ok=True)

def hash_object(data, type_='blob'):
    """Hashes an object and stores it in the repository."""
    obj = type_.encode() + b'\x00' + data
    oid = hashlib.sha1(obj).hexdigest()
    obj_dir = f"{GIT_DIR}/objects/{oid[:2]}"
    os.makedirs(obj_dir, exist_ok=True)
    
    try:
        with open(f"{obj_dir}/{oid[2:]}", 'xb') as f:
            f.write(obj)
    except FileExistsError:
        pass

    return oid

def get_object(oid, expected='blob'):
    """Retrieves an object by its OID and checks its type."""
    oid = oid.strip()
    if not oid or oid == "None":
        return None
    
    obj_path = f"{GIT_DIR}/objects/{oid[:2]}/{oid[2:]}"
    with open(obj_path, "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b'\x00')
    type_ = type_.decode()

    if expected is None or type_ == expected:
        return content
    else:
        raise ValueError(f"Expected {expected}, got {type_}")
    
RefValue = namedtuple('RefValue', ['symbolic', 'value'])

def update_ref(ref, value, deref=True):
    """Updates a reference to point to a specific OID."""
    ref = _get_ref_internal(ref, deref)[0]
    assert value.value
    if value.symbolic:
        value = f'ref:{value.value}'
    else:
        value=value.value
        
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(value)

def get_ref(ref, deref=True):
    """Retrieves the OID pointed to by a reference."""
    return _get_ref_internal(ref, deref)[1]

def delete_ref(ref, deref=True):
    ref = _get_ref_internal(ref, deref)[0]
    os.remove(f'{GIT_DIR}/{ref}')

def _get_ref_internal(ref, deref):
    ref_path = f'{GIT_DIR}/{ref}'
    value = None
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()
    symbolic = bool (value) and value.startswith ('ref:')
    if symbolic:
        value = value.split (':', 1)[1].strip ()
        if deref:
            return _get_ref_internal(value)
    
    return ref, RefValue(symbolic=symbolic, value=value)

def iter_refs(prefix='',deref=True):
    """Iterates over all references in the repository."""
    refs = ['HEAD', 'MERGE_HEAD']
    for root, _, filenames in os.walk(f'{GIT_DIR}/refs/'):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f'{root}/{name}' for name in filenames)
        
    for refname in refs:
        if not refname.startswith(prefix):
            continue
        ref = get_ref(refname, deref=deref)
        if ref.value:
            yield refname, ref

# This cleanup improves error handling, ensures directories are created only if they don't exist,
# and overall improves readability and consistency.

def object_exists(oid):
    return os.path.isfile(f'{GIT_DIR}/objects/{oid}')

def push_object(oid, remote_git_dir):
    remote_git_dir += './ugit'
    shutil.copy(f'{GIT_DIR}/objects/{oid}',
                f'{remote_git_dir}/objects/{oid}')

def fetch_object_if_missing(oid, remote_git_dir):
    if object_exists(oid):
        return
    remote_git_dir += '/.ugit'
    shutil.copy(f'{remote_git_dir}/objects/{oid}', 
               f'{GIT_DIR}/objects/{oid}' )