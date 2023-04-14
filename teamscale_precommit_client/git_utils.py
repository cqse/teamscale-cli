from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import locale
import os
from io import open

from git import Repo, InvalidGitRepositoryError, Diffable

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


def get_current_commit_sha(path_to_repository):
    """Get the commit SHA (ID) of the current commit

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            str: SHA of current commit.
    """
    return Repo(path_to_repository).active_branch.commit.hexsha


def get_repo_root_from_file_in_repo(path_to_file_in_repo):
    """Get the repository root for the given path in the repository."""
    try:
        repo = Repo(path=path_to_file_in_repo, search_parent_directories=True)

        submodules_root = repo.git.rev_parse("--show-superproject-working-tree")
        if submodules_root:
            return submodules_root

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


def filter_changed_files(changed_files, path_to_repository, file_encoding):
    """Filters the provided list of changed files.

    Non UTF-8 files and files larger than 1 MB are ignored.
    """
    filtered_files = []
    for changed_file in changed_files:
        file_is_valid = True
        if (os.path.isdir(os.path.join(path_to_repository, changed_file))):
            #ignore directories (e.g., git submodule folders)
            continue
        if os.path.getsize(os.path.join(path_to_repository, changed_file)) > 1 * 1024 * 1024:
            print('File too large for precommit analysis. Ignoring: %s' % changed_file)
            file_is_valid = False

        try:
            with open(os.path.join(path_to_repository, changed_file), encoding=file_encoding) as file:
                file.read()
        except UnicodeDecodeError:
            encoding_string = file_encoding
            if encoding_string is None:
                encoding_string = locale.getpreferredencoding() + ' (system encoding)'

            print(
                'File at %s is not encoded in %s. Try using the --file-encoding option.' % (
                    changed_file, encoding_string))
            file_is_valid = False

        if file_is_valid:
            filtered_files.append(changed_file)

    return filtered_files


def get_changed_files_and_content(path_to_repository, file_encoding, ignore_subrepositories):
    """Utility method for getting the currently changed files from a Git repository.

    Filters the changed files using `filter_changed_files`.

        Args:
            path_to_repository (str): Path to the Git repository
            file_encoding (str): Encoding of the files in the repository (c.f. https://docs.python.org/3/library/codecs.html#standard-encodings)

        Returns:
            dict: Mapping of filename to file content for all changed files in the provided repository.
            :param ignore_subrepositories:
    """
    changed_files = filter_changed_files(get_changed_files(path_to_repository, ignore_subrepositories),
                                         path_to_repository, file_encoding)
    return {filename: open(os.path.join(path_to_repository, filename), encoding=file_encoding).read() for filename in
            changed_files}


def get_changed_files(path_to_repository, ignore_subrepositories):
    """Utility method for getting the currently changed files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all changed files in the provided repository.
    """
    diff = _get_diff_to_last_commit(path_to_repository, ignore_subrepositories)
    return [item.b_path for item in diff if item.change_type in _CHANGE_TYPES_CONSIDERED_FOR_PRECOMMIT]


def get_deleted_files(path_to_repository, ignore_subrepositories):
    """Utility method for getting the deleted files from a Git repository.

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(str): List of filenames of all deleted files in the provided repository.
    """
    diff = _get_diff_to_last_commit(path_to_repository, ignore_subrepositories)
    return [item.b_path for item in diff if item.change_type == _CHANGE_TYPE_DELETED]


def _get_diff_to_last_commit(path_to_repository, ignore_subrepositories):
    """ Utility method for getting a diff between the working copy and the HEAD commit

        Args:
            path_to_repository (str): Path to the Git repository

        Returns:
            List(git.diff.Diff): List of Diff objects for every file
    """
    repo = Repo(path_to_repository)
    if ignore_subrepositories==True:
        unstaged_diff = repo.index.diff(other=None, paths=None, create_patch=False, ignore_submodules="all")
        staged_diff = repo.head.commit.diff(other=Diffable.Index, paths=None, create_patch=False, ignore_submodules="all")
    else:
        unstaged_diff = repo.index.diff(other=None, paths=None, create_patch=False)
        staged_diff = repo.head.commit.diff(other=Diffable.Index, paths=None, create_patch=False)

    return unstaged_diff + staged_diff
