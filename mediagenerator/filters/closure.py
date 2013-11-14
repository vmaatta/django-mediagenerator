from django.conf import settings
from django.utils.encoding import smart_str
from mediagenerator.generators.bundles.base import Filter

COMPILATION_LEVEL = getattr(settings, 'CLOSURE_COMPILATION_LEVEL',
                            'SIMPLE_OPTIMIZATIONS')

class Closure(Filter):
    def __init__(self, **kwargs):
        self.config(kwargs, compilation_level=COMPILATION_LEVEL)
        super(Closure, self).__init__(**kwargs)
        assert self.filetype == 'js', (
            'Closure only supports compilation to js. '
            'The parent filter expects "%s".' % self.filetype)

    def get_output(self, variation):
        # We import this here, so App Engine Helper users don't get import
        # errors.
        from subprocess import Popen, PIPE
        for input in self.get_input(variation):
            try:
                try:
                    compressor = settings.CLOSURE_COMPILER_PATH
                except AttributeError:
                    compressor = settings.CLOSURE_COMPILER_CMD
                    pre_commands = None
                else:
                    pre_commands = ['java', '-jar']
                finally:
                    command = [compressor,
                             '--charset', 'utf-8',
                             '--compilation_level', self.compilation_level]
                    post_commands = getattr(settings, 'CLOSURE_COMPILER_PARAMS',
                                            None)
                    if post_commands:
                        for c in post_commands:
                            command.append(c)
                    if pre_commands:
                		pre_commands.reverse()
                		for c in pre_commands:
                			command.insert(0, c)
                cmd = Popen(command,
                            stdin=PIPE, stdout=PIPE, stderr=PIPE,
                            universal_newlines=True)
                output, error = cmd.communicate(smart_str(input))
                assert cmd.wait() == 0, 'Command returned bad result:\n%s' % error
                yield output.decode('utf-8')
            except Exception, e:
                raise ValueError("Failed to execute Java VM or Closure. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_COMPILER_PATH or CLOSURE_COMPILER_CMD "
                    "in your settings correctly.\n"
                    "Error was: %s" % e)
