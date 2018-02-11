import os
import sys
import argparse
from shutil import fnmatch
from wx.tools import img2py


class Command:
    """The base command to define command-line actions.
    """
    name = None

    def __call__(self, args):
        raise NotImplementedError()


class PyEmbedImageCommand(Command):
    name = 'img-embed'
    ext_pattern = '*.png'

    parser = argparse.ArgumentParser(description='Python Embeddable Image')
    add = parser.add_argument
    add('source_dir')
    add('-o', '--out', dest='outfile', type=argparse.FileType('a'))

    def _norm_filename(self, filename):
        if filename:
            filename = os.path.splitext(filename)[0].replace('--', '-')
        return filename

    def __call__(self, args):
        arg = self.parser.parse_args(args)
        if not os.path.exists(arg.source_dir):
            _error('source_dir not found: %s' % arg.source_dir)

        full_filepath = os.path.abspath(arg.outfile.name)
        outdir = os.path.dirname(full_filepath)
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except Exception as ex:
                msg = "couldn't create base directory for outfile: %s. error: %s"
                _error(msg % (arg.outfile, str(ex)))

        dir_files = os.listdir(arg.source_dir)
        target_files = fnmatch.filter(dir_files, self.ext_pattern)

        if not target_files:
            print('No image file(s) found in source directory')
            sys.exit(0)

        for fn in target_files:
            img2py.img2py(os.path.join(arg.source_dir, fn), full_filepath,
                          append=True, imgName=self._norm_filename(fn))

        print('%i files processed' % len(target_files))


class Runner:
    prog = 'cli'
    _command_registry = {
        PyEmbedImageCommand
    }

    @property
    def command_dict(self):
        return {
            c.name: c
                for c in self._command_registry
        }

    def _usage(self):
        available_cmds = list(self.command_dict.keys())
        print("Usage: cli [command] [options]\n\n"
            "[commands]%s" % '\n  '.join([''] + available_cmds))
        self.exit()

    def _error(self, message, prog='cli.py'):
        print('%s: error: %s' % (self.prog or prog, message))
        self.exit()

    def exit(self, code=0):
        sys.exit(code)

    def run(self, argv):
        if argv and argv[0].lower() == '-h':
            self._usage()

        command_dict = self.command_dict
        available_cmds = command_dict.keys()
        if not argv or argv[0] not in available_cmds:
            expected = ', '.join(available_cmds)
            _error('unknown command: %s. Expected: %s' % (argv[0], expected))

        command = command_dict[argv[0]]()
        command(argv[1:])


if __name__ == '__main__':
    Runner().run(sys.argv[1:])
    print('Done!')
