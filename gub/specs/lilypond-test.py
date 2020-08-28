#
from gub import context
from gub import misc
from gub import target
from gub.specs import lilypond

class LilyPond_test (lilypond.LilyPond_base):
    dependencies = (lilypond.LilyPond_base.dependencies
                + [
                'tools::imagemagick',
                'tools::fonts-dejavu',
                'tools::fonts-libertine',
                'tools::fonts-bitstream-charter',
                'tools::fonts-bitstream-vera',
                'tools::fonts-liberation',
                'tools::fonts-urw-core35',
                'tools::fonts-luximono',
                'tools::fonts-ipafont',
                'tools::fonts-gnufreefont',
                'tools::rsync',
                ])
    @context.subst_method
    def test_ball (self):
        return '%(uploads)s/lilypond-%(version)s-%(build_number)s.test-output.tar.bz2'
    make_flags = misc.join_lines ('''
CPU_COUNT=%(cpu_count)s
MISSING_OPTIONAL=dblatex
''')
    compile_flags = lilypond.LilyPond_base.compile_flags + ' test'
        #return (lilypond.LilyPond_base.install_command
    install_command = 'true'
    def install (self):
        target.AutoBuild.install (self) 
        # Store the `$targetdir' value in file `AAA-prefix'.  This is needed
        # in case the tarball gets extracted by another gub incarnation that
        # uses a different platform, architecture, user, or top-level
        # directory.
        self.system('''
echo %(targetdir)s > %(builddir)s/input/regression/out-test/AAA-prefix
''')
        # Exclusions: from share/lilypond/current we only need fonts,
        # and we don't need their sources.
        self.system (misc.join_lines ('''
LD_PRELOAD=
tar -C %(builddir)s -chjf %(test_ball)s
--exclude 'current/[^f]*'
--exclude 'fonts/source'
input/regression/out-test
'''))
    def compile (self):
        # system::xetex uses system's shared libraries instead of GUB's ones.
        self.file_sub ([('^exec xetex ', 'LD_LIBRARY_PATH= exec xetex ')],
                       '%(srcdir)s/scripts/build/xetex-with-options.sh')

        # system::xelatex uses system's shared libraries instead of GUB's ones.
        self.file_sub ([('^exec xelatex ',
                         'LD_LIBRARY_PATH= exec xelatex ')],
                       '%(srcdir)s/scripts/build/xelatex-with-options.sh')

        # tools::extractpdfmark uses system's libstdc++ instead of GUB's one.
        self.file_sub ([('^EXTRACTPDFMARK = ([^L].*)$',
                         'EXTRACTPDFMARK = LD_LIBRARY_PATH=%(tools_prefix)s/lib \\1')],
                       '%(builddir)s/config.make')

        # Touch all targets to avoid rebuilds (ugh).
        for d in [ 'python', 'scripts', 'flower', 'lily', 'mf' ]:
            # Cannot use formatting because %(builddir)s must be passed as-is...
            self.system('make -C %(builddir)s/' + d + ' --touch all')

        lilypond.LilyPond_base.compile (self)

Lilypond_test = LilyPond_test
