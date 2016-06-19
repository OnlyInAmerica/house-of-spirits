import os

LOCKFILE_EXT = '.lockfile'


def is_locked(process_name: str):
    try:
        lock_file = open(process_name + LOCKFILE_EXT, 'r')
        lock_file.close()
        return True

    except FileNotFoundError:
        return False


def lock(process_name: str):
    lock_file = open(process_name + LOCKFILE_EXT, 'w')
    lock_file.close()


def unlock(process_name: str):
    try:
        os.remove(process_name + LOCKFILE_EXT)
    except FileNotFoundError:
        pass