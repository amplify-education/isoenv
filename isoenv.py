#! /usr/bin/env python

#This file is part of isoenv
#
#Copyright (c) 2012 Wireless Generation, Inc.
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

'''Testing a doc string'''

import sys
import os.path
from os import walk, makedirs, remove
from argparse import ArgumentParser
from shutil import copy2
import logging
import json
import subprocess
from contextlib import contextmanager
from shutil import rmtree
from tempfile import mkdtemp

log = logging.getLogger(__name__)

# Strategy:
# 1) Generate a mapping from destination files to source files.
#    This mapping prioritizes environment specific files over common files
#    and files in later directories higher than in earlier directories
# 2) Delete the output directory, and copy the files to it.

ENV_DIR = 'ENVIRONMENT_SPECIFIC'
EXCLUDED_FILES = ['.git']


def compile(sources, dest, environment, dryrun=False, excluded=EXCLUDED_FILES):
    '''
    Compiles from the listed sources to the directory dest,
    using the specified environment
    '''

    file_map = map_files(
        sources,
        dest,
        environment,
        excluded
    )

    # If we're in dryrun, we don't want to delete the destination directory
    # However, we still want to run copy_files so that the relevant logging
    # and screen output can happen
    if not dryrun:
        directories = []
        for path in list_directory(dest, excluded):
            remove(path)
    
        for (dirpath, dirnames, filenames) in walk_with_exclusions(dest, excluded):
            for dir in dirnames:
                directories.append(os.path.join(dirpath, dir))

        def directory_depth(dir):
            return len(dir.split('/'))

        for dir in sorted(directories, key=directory_depth, reverse=True):
            os.rmdir(dir)

    copy_files(file_map, dryrun)
    etc_dir = os.path.join(dest, 'etc')
    if not os.path.exists(etc_dir):
        makedirs(etc_dir)
    with open(os.path.join(etc_dir, 'mapped_files.json'), 'w') as file_log:
        json.dump(file_map, file_log, sort_keys=True, indent=4)

def map_files(sources, dest, environment, excluded=EXCLUDED_FILES):
    '''
    Generates a map of destination path -> source path for all files
    that should be compiled from repo to dest, given the environment
    '''
    file_map = {}

    environment_id = os.path.join(ENV_DIR, environment)

    for source in sources:
        for dirpath, dirnames, filenames in walk_with_exclusions(source, excluded):
            dest_dir = os.path.join(dest, dirpath.replace(source, '').replace(environment_id, '').lstrip('/'))
            if ENV_DIR in dest_dir:
                continue
            else:
                for filename in filenames:
                    dest_file = os.path.normpath(os.path.join(dest_dir, filename))
                    src_file = os.path.normpath(os.path.join(dirpath, filename))
                    if dest_file in file_map:
                        log.warning("{dest} has multiple sources, overriding {old_src} with {new_src}".format(
                            dest = dest_file,
                            old_src = file_map[dest_file],
                            new_src = src_file
                        ))
                    file_map[dest_file] = src_file

    return file_map

def copy_files(file_map, dryrun=False):
    '''
    Copies each file listed in file_map from the source to the destination.
    File_map is a dictionary mapping dest to source.
    '''

    for dest, source in file_map.iteritems():
        if not dryrun:
            try:
                makedirs(os.path.dirname(dest))
            except OSError:
                # Ignore directory creation errors. If the directory
                # isn't created, the copy will fail
                pass
            copy2(source, dest)

def walk_with_exclusions(dir, exclusions):
    for (dirpath, dirnames, filenames) in walk(dir):
        for excluded in exclusions:
            if excluded in dirnames:
                dirnames.remove(excluded)
            if excluded in filenames:
                filenames.remove(excluded)
        yield (dirpath, dirnames, filenames)

def list_directory(dir, excluded=EXCLUDED_FILES):
    '''
    Yields paths for all files underneath dir that aren't listed in
    excluded and aren't inside a directory listed in excluded
    '''
    for (dirpath, dirnames, filenames) in walk_with_exclusions(dir, excluded):
        for filename in filenames:
            yield os.path.join(dirpath, filename)

@contextmanager
def compiled(sources, environment, dest_dir=None):
    if dest_dir is None:
        dest_dir = mkdtemp()

    try:
        log.info("compiling {environment} from {sources} to {dest_dir}".format(
            environment=environment,
            sources=', '.join(sources),
            dest_dir=dest_dir))
        compile(sources, dest_dir, environment, dryrun=False)
        log.info("compile complete")
        yield dest_dir
    finally:
        rmtree(dest_dir)

def add_logging_args(parser):
    parser.add_argument("-q", "--quiet", dest="quiet",
                      action="store_true", default=False,
                      help="Run silently")
    parser.add_argument("-v", "--verbose", dest="verbose",
                      action="store_true", default=False,
                      help="Run verbosely")
    parser.add_argument("-l", "--logging_file", dest="logfile",
                      action="store",
                      help="Which file to log to")

def setup_logging(args, format):
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging_opts = dict(level=loglevel, format=format)

    if args.logfile:
        logging_opts['filename'] = args.logfile
        logging_opts['filemode'] = 'a'

    if (not args.quiet) or args.logfile:
        logging.basicConfig(**logging_opts)


def isoenv_main(args=sys.argv[1:]):
    parser = ArgumentParser(description="Compile a set of source directories containing environment specific "
        "files into a single output repository with only the files for the specified environment")
    parser.add_argument("--sources", nargs='+', metavar='source', required='true')
    parser.add_argument("--environment", required='true')
    parser.add_argument("dest")
    parser.add_argument("-d", "--dryrun", dest="dryrun",
                      action="store_true", default=False,
                      help="Don't modify the destination directory")
    add_logging_args(parser)
    
    args = parser.parse_args(args)
    
    run_mode = 'live run' if not args.dryrun else 'dry run'
    format=' - '.join(['%(asctime)s', '%(levelname)s', run_mode, '%(message)s'])
    setup_logging(args, format)
   
    compile(args.sources, args.dest, args.environment, args.dryrun)

def in_env_args():
    parser = ArgumentParser(description="Run a command inside a compiled directory")
    parser.add_argument("--sources", nargs='+', metavar='source', required='true')
    parser.add_argument("--environment", required='true')
    parser.add_argument("command", nargs="*")
    parser.add_argument("--destination")
    parser.add_argument("--shell", default="/bin/sh")
    add_logging_args(parser)
    return parser


def in_env_main(args=sys.argv[1:]):
    args = in_env_args().parse_args(args)
    setup_logging(args, ' - '.join(['%(asctime)s', '%(levelname)s', '%(message)s']))

    command = " ".join(args.command)
    subenv = dict(os.environ)
    proc = None
    with compiled(args.sources, args.environment) as compiled_dir:
        try:
            subenv['COMPILED_DIR'] = compiled_dir
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=compiled_dir,
                env=subenv,
                executable=args.shell)
            proc.wait()
            return proc.returncode
        finally:
            if proc is not None:
                if proc.returncode is None:
                    proc.terminate()
                if proc.returncode is None:
                    proc.kill()


if __name__ == "__main__":
    sys.exit(isoenv_main(sys.argv[1:]))
