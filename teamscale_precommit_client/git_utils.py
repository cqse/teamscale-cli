from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
from io import open

from git import Repo, InvalidGitRepositoryError

# [M]odified, [A]dded, [C]opied, [T]ype changed, [R]enamed (R092 should be R according to
# https://gitpython.readthedocs.io/en/stable/reference.html#git.diff.DiffIndex, but testing it locally gave R092)
_CHANGE_TYPES_CONSIDERED_FOR_PRECOMMIT = ['M', 'A', 'C', 'T', 'R', 'R092']

_CHANGE_TYPE_DELETED = 'D'


def get_current_branch(path_to_repository):
    """Utility method for getting the current branch from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            str: The current branch in the provided repository.
    """
    repo = Repo(path_to_repository)
    return repo.active_branch.name


def get_repo_root_from_file_in_repo(path_to_file_in_repo):
    """Get the repository root for the given path in the repository."""
    try:
        repo = Repo(path=path_to_file_in_repo, search_parent_directories=True)
        git_root = repo.git.rev_parse("--show-toplevel")
        return git_root
    except InvalidGitRepositoryError:
        return None


def get_current_timestamp(path_to_repository):
    """Utility method for getting the timestamp of the last commit from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            str: The timestamp of the last commit in the provided repository.
    """
    repo = Repo(path_to_repository)
    return repo.head.commit.committed_date


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
    return {filename: open(os.path.join(path_to_repository, filename), encoding='utf-8').read() for filename in
            changed_files}


def get_changed_files(path_to_repository):
    """Utility method for getting the currently changed files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all changed files in the provided repository.
    """
    diff = _get_diff_to_last_commit(path_to_repository)
    return [item.b_path for item in diff if item.change_type in _CHANGE_TYPES_CONSIDERED_FOR_PRECOMMIT]


def get_deleted_files(path_to_repository):
    """Utility method for getting the deleted files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all deleted files in the provided repository.
    """
    diff = _get_diff_to_last_commit(path_to_repository)
    return [item.b_path for item in diff if item.change_type == _CHANGE_TYPE_DELETED]


def _get_diff_to_last_commit(path_to_repository):
    """ Utility method for getting a diff between the working copy and the HEAD commit

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(git.diff.Diff): List of Diff objects for every file
    """
    repo = Repo(path_to_repository)
    unstaged_diff = repo.index.diff(None)
    staged_diff = repo.head.commit.diff()
    return unstaged_diff + staged_diff
