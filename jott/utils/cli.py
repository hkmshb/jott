import os
import sys
import argparse
from shutil import fnmatch
from wx.tools import img2py


class Command:
    """The base command to define command-line actions.
    """
    name = None

    def __init__(self, runner):
        self._runner = runner

    def __call__(self, args):
        self.execute(args)

    def _error(self, message):
        self._runner._error(message, prog=self.name)

    def execute(self, args):
        raise NotImplementedError()


class PyEmbedImageCommand(Command):
    name = 'img-embed'
    ext_pattern = '*.png'

    parser = argparse.ArgumentParser(description='Python Embeddable Image')
    add = parser.add_argument
    add('source', help='Directory containing files or file to embed')
    add('-o', '--out', dest='outfile', type=argparse.FileType('a'))

    def _norm_filename(self, filename):
        if filename:
            filename = os.path.splitext(filename)[0].replace('--', '-')
        return filename

    def execute(self, args):
        arg = self.parser.parse_args(args)
        if not os.path.exists(arg.source):
            self._error('source not found: %s' % arg.source)

        if os.path.isfile(arg.source):
            reldir, fn = os.path.split(arg.source)
            source_path = os.path.abspath(reldir)
            target_files = (fn,)
        else:
            source_path = os.path.abspath(arg.source)
            dir_files = os.listdir(source_path)
            target_files = fnmatch.filter(dir_files, self.ext_pattern)

        if not target_files:
            print('No image file(s) found at provided source')
            sys.exit(0)

        full_filepath = os.path.abspath(arg.outfile.name)
        outdir = os.path.dirname(full_filepath)
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except Exception as ex:
                msg = "couldn't create base directory for outfile: %s. error: %s"
                self._error(msg % (arg.outfile, str(ex)))

        for fn in sorted(target_files):
            img2py.img2py(os.path.join(source_path, fn), full_filepath,
                          append=True, imgName=self._norm_filename(fn))

        print('%i file(s) processed' % len(target_files))


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
            xarg = argv[0] if argv else '?'
            self._error('unknown command: %s. Expected: %s' % (xarg, expected))

        command = command_dict[argv[0]](self)
        command.execute(argv[1:])


if __name__ == '__main__':
    Runner().run(sys.argv[1:])
    print('Done!')
