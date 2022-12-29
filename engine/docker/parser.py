from tarfile import TarFile


class TarFileParser(TarFile):

    def get_file_raw(self, member):
        """Extract a member from the archive to the current working directory,
           using its full name. Its file information is extracted as accurately
           as possible. `member' may be a filename or a TarInfo object. You can
           specify a different directory using `path'. File attributes (owner,
           mtime, mode) are set unless `set_attrs' is False. If `numeric_owner`
           is True, only the numbers for user/group names are used and not
           the names.
        """
        self._check("r")

        if isinstance(member, str):
            tarinfo = self.getmember(member)
        else:
            tarinfo = member

        source = self.fileobj
        source.seek(tarinfo.offset_data)

        bufsize = 16 * 1024

        blocks, remainder = divmod(tarinfo.size, bufsize)
        for b in range(blocks):
            buf = source.read(bufsize)
            if len(buf) < bufsize:
                raise OSError("unexpected end of data")

            return buf

        if remainder != 0:
            buf = source.read(remainder)
            if len(buf) < remainder:
                raise OSError("unexpected end of data")

            return buf

        return None
