from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
from pygit2 import Repository, GIT_STATUS_WT_DELETED, GIT_STATUS_WT_MODIFIED, GIT_STATUS_WT_RENAMED, \
    GIT_STATUS_WT_TYPECHANGE, GIT_STATUS_INDEX_NEW, GIT_STATUS_INDEX_MODIFIED, GIT_STATUS_INDEX_DELETED, \
    discover_repository
from io import open

_STATI_CONSIDERED_FOR_PRECOMMIT = GIT_STATUS_INDEX_NEW | GIT_STATUS_INDEX_MODIFIED | GIT_STATUS_WT_MODIFIED | \
                                  GIT_STATUS_WT_RENAMED | GIT_STATUS_WT_TYPECHANGE

_STATI_DELETED = GIT_STATUS_INDEX_DELETED | GIT_STATUS_WT_DELETED

def get_current_branch(path_to_repository):
    """Utility method for getting the current branch from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            str: The current branch in the provided repository.
    """
    repo = Repository(path_to_repository)
    head = repo.lookup_reference("HEAD").resolve()
    return head.shorthand

def get_repo_root_from_file_in_repo(path_to_file_in_repo):
    git_folder = discover_repository(path_to_file_in_repo)
    if not git_folder:
        return None
    return os.path.dirname(os.path.dirname(git_folder))

def get_current_timestamp(path_to_repository):
    """Utility method for getting the timestamp of the last commit from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            str: The timestamp of the last commit in the provided repository.
    """
    repo = Repository(path_to_repository)
    head = repo.revparse_single('HEAD')
    return head.commit_time

def filter_changed_files(changed_files, path_to_repository):
    """Filters the provided list of changed files.

    Files larger than 1 MB are ignored.
    """
    filtered_files = []
    for changed_file in changed_files:
        if os.path.getsize(os.path.join(path_to_repository, changed_file)) > 1 * 1024 * 1024:
            print('File too large for precommit analysis. Ignoring: %s' % changed_file)
        else:
            filtered_files.append(changed_file)
    return filtered_files

def get_changed_files_and_content(path_to_repository):
    """Utility method for getting the currently changed files from a Git repository.

    Filters the changed files using `filter_changed_files`.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            dict: Mapping of filename to file content for all changed files in the provided repository.
    """
    changed_files = filter_changed_files(get_changed_files(path_to_repository), path_to_repository)
    return {filename: open(os.path.join(path_to_repository, filename), encoding='utf-8').read() for filename in changed_files}

def get_changed_files(path_to_repository):
    """Utility method for getting the currently changed files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all changed files in the provided repository.
    """
    repo = Repository(path_to_repository)
    status_entries = repo.status()
    return [path for path, st in status_entries.items() if st & _STATI_CONSIDERED_FOR_PRECOMMIT]

def get_deleted_files(path_to_repository):
    """Utility method for getting the deleted files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all deleted files in the provided repository.
    """
    repo = Repository(path_to_repository)
    status_entries = repo.status()
    return [path for path, st in status_entries.items() if st & _STATI_DELETED]
