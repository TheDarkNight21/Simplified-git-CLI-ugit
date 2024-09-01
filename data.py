import os
import hashlib

GIT_DIR = ".ugit"


def init():
    """
    Initializing Git:
    - Make git directory
    - Make git/objects directory for hash
    """
    os.makedirs(GIT_DIR)
    os.makedirs(f'{GIT_DIR}/objects')

def hash_object(data, type_='blob'):
    """

    :param data:
    :param type_:
    :return:
    """
    obj = type_.encode() + b'\x00' + data
    oid = hashlib.sha1(obj).hexdigest()
    os.makedirs(f"{GIT_DIR}/objects/{oid[:2]}", exist_ok=True)
    try:
        with open(f"{GIT_DIR}/objects/{oid[:2]}/{oid[2:]}", 'xb') as f:
            f.write(obj)
    except FileExistsError:
        pass
        
    return oid

def get_object(oid, expected='blob'):
    with open(f"{GIT_DIR}/objects/{oid[:2]}/{oid[2:]}", "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b'\x00')
    type_ = type_.decode()

    if expected is None or type_ == expected:
        return content
    else:
        raise ValueError(f"Expected {expected}, got {type_}")
    
def update_ref(ref, oid): # set the head of the commits
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(oid)
        
def get_ref(ref): # retrieves the head from the headfile
    ref_path = f'{GIT_DIR}/{ref}'
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            return f.read().strip()

