#!/usr/bin/env python

import os
import re
import sys
from contextlib import contextmanager
from subprocess import Popen, PIPE

sys.dont_write_bytecode = True

@contextmanager
def cd(*args, **kwargs):
    mkdir = kwargs.pop('mkdir', True)
    path = os.path.sep.join(args)
    path = os.path.normpath(path)
    path = os.path.expanduser(path)
    prev = os.getcwd()
    if path != prev:
        if mkdir:
            run('mkdir -p %(path)s' % locals())
        os.chdir(path)
        curr = os.getcwd()
        sys.path.append(curr)
    try:
        yield
    finally:
        if path != prev:
            sys.path.remove(curr)
            os.chdir(prev)

def run(*args, **kwargs):
    process = Popen(
        shell=kwargs.pop('shell', True),
        stdout=kwargs.pop('stdout', PIPE),
        stderr=kwargs.pop('stderr', PIPE),
        *args, **kwargs)
    stdout, stderr = process.communicate()
    exitcode = process.poll()
    return exitcode, stdout.strip(), stderr.strip()

def expand(path):
    if path:
        return os.path.expanduser(path)

class RepospecDecompositionError(Exception):
    '''
    exception when repospec can't be decomposed
    '''
    pass

def decompose(repospec, giturl=None):
    pattern = r'(((((ssh|https)://)?([a-zA-Z0-9_.\-]+@)?)([a-zA-Z0-9_.\-]+))([:/]{1,2}))?([a-zA-Z0-9_.\-\/]+)@?([a-zA-Z0-9_.\-\/]+)?'
    match = re.search(pattern, repospec)
    if match:
        return match.group(2) or giturl, match.group(8), match.group(9), match.group(10) or 'HEAD'
    raise RepospecDecompositionError(repospec)

def divine(giturl, sep, reponame, revision):
    r2c = {}
    c2r = {}
    result = run('git ls-remote %(giturl)s%(sep)s%(reponame)s' % locals())[1]
    for line in result.split('\n'):
        commit, refname = line.split('\t')
        r2c[refname] = commit
        c2r[commit] = refname

    refnames = [
        'refs/heads/' + revision,
        'refs/tags/' + revision,
        revision
    ]

    commit = None
    for refname in refnames:
        commit = r2c.get(refname, None)
        if commit:
            break

    if not commit:
        commit = revision

    return c2r.get(commit, None), commit

def clone(giturl, sep, reponame, commit, clonepath, mirrorpath, versioning=False):
    clonepath = expand(clonepath)
    mirrorpath = expand(mirrorpath)
    mirror = ''
    if mirrorpath:
        mirror = '--reference %(mirrorpath)s/%(reponame)s.git' % locals()
    path = os.path.join(clonepath, reponame)
    repopath = reponame
    if versioning:
        repopath = os.path.join(repopath, commit)
    with cd(clonepath, mkdir=True):
        if not os.path.isdir(repopath):
            run('git clone %(mirror)s %(giturl)s%(sep)s%(reponame)s %(repopath)s' % locals())
        with cd(repopath):
            run('git clean -xfd')
            run('git checkout %(commit)s' % locals())
    return os.path.join(clonepath, repopath)

if __name__ == '__main__':
    try:
        import argparse
    except:
        print 'missing argparse; clone.py can be used as a library w/o argparse'
        sys.exit(-1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--clonepath',
        default=os.getcwd(),
        help='path to store all cloned repos')
    parser.add_argument(
        '--mirrorpath',
        help='path to cached repos to support fast cloning')
    parser.add_argument(
        '--giturl',
        help='the giturl to be used with git clone')
    parser.add_argument(
        '--versioning',
        action='store_true',
        help='turn on versioning; checkout in reponame/commit rather than reponame')
    parser.add_argument(
        'repospec',
        help='repospec schema is giturl?reponame@revision?')

    ns = parser.parse_args()
    locals().update(ns.__dict__)
    giturl, sep, reponame, revision = decompose(repospec, giturl)
    _, commit = divine(giturl, sep, reponame, revision)
    print clone(giturl, sep, reponame, commit, clonepath, mirrorpath, versioning)
