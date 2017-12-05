#!/usr/bin/env python
# Copyright 2017, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import glob
import os
import stat
import time


class LogWatcher(object):
    """Looks for changes in all files of a directory.
    This is useful for watching log file changes in real-time.
    It also supports files rotation.
    Example:
    >>> def callback(filename, lines):
    ...     print filename, lines
    ...
    >>> l = LogWatcher("/var/log/", callback)
    >>> l.loop()
    """

    def __init__(self, folder, callback,
                 matching_file_names=[],
                 extensions=["log"], tail_lines=0):
        """Arguments:
        (str) @folder:
            the folder to watch
        (callable) @callback:
            a function which is called every time a new line in a
            file being watched is found;
            this is called with "filename" and "lines" arguments.
        (list) @matching_file_names:
            only watch files file names
        (list) @extensions:
            only watch files with these extensions
        (int) @tail_lines:
            read last N lines from files being watched before starting
        """
        self.files_map = {}
        self.callback = callback
        self.folder = os.path.realpath(folder)
        self.extensions = extensions
        self.matching_file_names = matching_file_names
        assert os.path.isdir(self.folder), "%s does not exists" \
            % self.folder
        assert callable(callback)
        self.update_files()
        # The first time we run the script we move all file markers at EOF.
        # In case of files created afterwards we don't do this.
        # In ascyn mode we will need to move to the last recorded offset
        for id, file in self.files_map.iteritems():
            offset_file_name = self._get_offset_file(file.name)
            if (os.path.exists(offset_file_name) and
                    os.path.getsize(offset_file_name)):
                offset_fh = open(offset_file_name, "r")
                _file_inode, offset = \
                    [int(line.strip()) for line in offset_fh]
                # file has been rotated, need to real all the left over
                # from the rotated file before
                if _file_inode != os.stat(file.name).st_ino:
                    rotated_file_name = (
                        self._determine_rotated_logfile(file.name,
                                                        _file_inode)
                    )
                    if rotated_file_name:
                        rotated_file_handle = open(
                            rotated_file_name, "r")
                        rotated_file_handle.seek(offset)
                        self.readfile(rotated_file_handle)
                    offset = 0
            else:
                offset = os.path.getsize(file.name)
            file.seek(offset)  # EOF
            if tail_lines:
                lines = self.tail(file.name, tail_lines)
                if lines:
                    self.callback(file.name, lines)

    def _determine_rotated_logfile(self, fname, old_file_inode):
        """
        We suspect the logfile has been rotated, so try to guess what the
        rotated filename is, and return it.
        """
        rotated_filename = self._check_rotated_filename_candidates(fname)
        if rotated_filename and os.path.exists(rotated_filename):
            if os.stat(rotated_filename).st_ino == old_file_inode:
                return rotated_filename

            # These logics are handling file shranks
            # if the inode hasn't changed, then the file shrank; this is
            # expected with copytruncate,
            # otherwise print a warning
            # if stat(self.filename).st_ino == self._offset_file_inode:
            # if self.copytruncate:
            # return rotated_filename
            # else:
            # sys.stderr.write(
            #          "[pygtail] [WARN] file size of %s shrank, "
            #          "and copytruncate support is "
            #          "disabled (expected at least %d bytes, was %d bytes)"
            # ".\n" %
            # (self.filename, self._offset,
            # stat(self.filename).st_size))

        return None

    def _check_rotated_filename_candidates(self, fname):
        """
        Check for various rotated logfile filename patterns and return the
        first match we find.
        """
        # savelog(8)
        candidate = "%s.0" % fname
        if (os.path.exists(candidate) and os.path.exists("%s.1.gz" % fname) and
                (stat(candidate).st_mtime > stat("%s.1.gz" % fname).st_mtime)):
            return candidate

        # logrotate(8)
        # with delaycompress
        candidate = "%s.1" % fname
        if os.path.exists(candidate):
            return candidate

        # without delaycompress
        candidate = "%s.1.gz" % fname
        if os.path.exists(candidate):
            return candidate

        rotated_filename_patterns = (
            # logrotate dateext rotation scheme - `dateformat -%Y%m%d` + with
            # `delaycompress`
            "-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
            # logrotate dateext rotation scheme - `dateformat -%Y%m%d` +
            # without `delaycompress`
            "-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].gz",
            # logrotate dateext rotation scheme - `dateformat -%Y%m%d-%s` +
            # with `delaycompress`
            ("-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-"
             "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"),
            # logrotate dateext rotation scheme - `dateformat -%Y%m%d-%s` +
            # without `delaycompress`
            ("-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-"
             "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].gz"),
            # for TimedRotatingFileHandler
            ".[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]",
        )
        for rotated_filename_pattern in rotated_filename_patterns:
            candidates = glob.glob(fname + rotated_filename_pattern)
            if candidates:
                candidates.sort()
                return candidates[-1]  # return most recent

        # no match
        return None

    def __del__(self):
        self.close()

    def loop(self, interval=0.1, async=False):
        """Start the loop.
        If async is True make one loop then return.
        """
        while True:
            self.update_files(async)
            for fid, file in list(self.files_map.iteritems()):
                self.readfile(file)
            if async:
                return
            time.sleep(interval)

    def log(self, line):
        """Log when a file is un/watched"""
        print(line)

    def listdir(self):
        """List directory and filter files by extension.
        You may want to override this to add extra logic or
        globbling support.
        """
        ls = os.listdir(self.folder)
        if self.extensions:
            res = [x for x in ls if os.path.splitext(x)[1][1:]
                   in self.extensions]
            if self.matching_file_names:
                res = [x for x in res if os.path.basename(x) in
                       self.matching_file_names]
            return res
        else:
            return ls

    @staticmethod
    def tail(fname, window):
        """Read last N lines from file fname."""
        try:
            f = open(fname, 'r')
        except IOError as err:
            if err.errno == errno.ENOENT:
                return []
            else:
                raise
        else:
            BUFSIZ = 1024
            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            block = -1
            data = ""
            exit = False
            while not exit:
                step = (block * BUFSIZ)
                if abs(step) >= fsize:
                    f.seek(0)
                    exit = True
                else:
                    f.seek(step, os.SEEK_END)
                data = f.read().strip()
                if data.count('\n') >= window:
                    break
                else:
                    block -= 1
            return data.splitlines()[-window:]

    def update_files(self, async=False):
        ls = []
        for name in self.listdir():
            absname = os.path.realpath(os.path.join(self.folder, name))
            try:
                st = os.stat(absname)
            except EnvironmentError as err:
                if err.errno != errno.ENOENT:
                    raise
            else:
                if not stat.S_ISREG(st.st_mode):
                    continue
                fid = self.get_file_id(st)
                ls.append((fid, absname))

        # check existent files
        for fid, file in list(self.files_map.iteritems()):
            try:
                st = os.stat(file.name)
            except EnvironmentError as err:
                if err.errno == errno.ENOENT:
                    self.unwatch(file, fid)
                else:
                    raise
            else:
                if fid != self.get_file_id(st):
                    # same name but different file (rotation); reload it.
                    self.unwatch(file, fid)
                    self.watch(file.name)

        # add new ones
        for fid, fname in ls:
            if fid not in self.files_map:
                self.watch(fname)

        # for async mode we will need to keep track of the last bulk
        if async:
            for fid, file in list(self.files_map.iteritems()):
                offset = os.path.getsize(file.name)
                inode = os.stat(file.name).st_ino
                fh = open(self._get_offset_file(file.name), "w")
                fh.write("%s\n%s\n" % (inode, offset))
                fh.close()

    def _get_offset_file(self, fname):
        base_fname = os.path.basename(fname)
        return os.path.join('/tmp/%s.offset' % base_fname)

    def readfile(self, file_h):
        current_p = file_h.tell()
        file_h.seek(current_p)
        lines = file_h.readlines()
        if lines:
            self.callback(file_h.name, lines)

    def watch(self, fname):
        try:
            file = open(fname, "r")
            fid = self.get_file_id(os.stat(fname))
        except EnvironmentError as err:
            if err.errno != errno.ENOENT:
                raise
        else:
            self.log("watching logfile %s" % fname)
            self.files_map[fid] = file

    def unwatch(self, file, fid):
        # file no longer exists; if it has been renamed
        # try to read it for the last time in case the
        # log rotator has written something in it.
        # (TODO): test this!
        lines = self.readfile(file)
        self.log("un-watching logfile %s" % file.name)
        del self.files_map[fid]
        if lines:
            self.callback(file.name, lines)

    @staticmethod
    def get_file_id(st):
        return "%xg%x" % (st.st_dev, st.st_ino)

    def _update_offset_file(self):
        pass

    def close(self):
        for id, file in self.files_map.iteritems():
            file.close()
        self.files_map.clear()


if __name__ == '__main__':
    import base64
    import zlib

    def callback(filename, lines):
        for line in lines:
            if not line.strip():
                pass
            elif line.find(':::') == -1:
                print("new line in file %s: %s" % (filename, line))
            else:
                data = line.split(':::')
                try:
                    print(data[0], data[1],
                          zlib.decompress(base64.decodestring(data[2])))
                except Exception as e:
                    print(str(e))
                    print(time.time(),
                          'caught exception rendering a new log line in %s'
                          % filename)

    l = LogWatcher("/var/log/", callback)
    l.loop()
