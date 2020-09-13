import os
#
from gub import context
from gub import misc
from gub import target
from gub.specs import lilypond
from gub.syntax import printf

class LilyPond_doc (lilypond.LilyPond_base):
    dependencies = (lilypond.LilyPond_base.dependencies
                + [
                'tools::imagemagick',
                'tools::rsync', # ugh, we depend on *rsync* !?
                #'tools::texlive',
                'tools::fonts-dejavu',
                'tools::fonts-libertine',
                'tools::fonts-bitstream-charter',
                'tools::fonts-bitstream-vera',
                'tools::fonts-liberation',
                'tools::fonts-urw-core35',
                'tools::fonts-luximono',
                'tools::fonts-ipafont',
                'tools::fonts-gnufreefont',
                'tools::texinfo',
                'system::zip',
                ])
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
        # The timestamp of these scripts should not be older than config.make.
        # Otherwise, they will be regenerated from the source directory
        # and the above substitutes will be lost.
        self.system ('touch %(srcdir)s/scripts/build/xetex-with-options.sh')
        self.system ('touch %(srcdir)s/scripts/build/xelatex-with-options.sh')
        lilypond.LilyPond_base.compile (self)
    make_flags = misc.join_lines ('''
CROSS=no
DOCUMENTATION=yes
WEB_TARGETS="offline online"
TARGET_PYTHON=/usr/bin/python
CPU_COUNT=%(cpu_count)s
MISSING_OPTIONAL=dblatex
''')
    compile_flags = lilypond.LilyPond_base.compile_flags + ' top-doc doc'
    install_flags = (' install-doc install-help2man'
                     ' prefix='
                     ' infodir=/share/info'
                     ' DESTDIR=%(install_root)s'
                     ' mandir=/share/man')
    @context.subst_method
    def doc_ball (self):
        return '%(uploads)s/lilypond-%(version)s-%(build_number)s.documentation.tar.bz2'
    @context.subst_method
    def web_ball (self):
        return '%(uploads)s/lilypond-%(version)s-%(build_number)s.webdoc.tar.bz2'
    def install (self):
        target.AutoBuild.install (self) 
        self.system ('''
LD_PRELOAD= cp -f sourcefiles/dir %(install_root)s/share/info/dir
cd %(install_root)s/share/info && %(doc_relocation)s install-info --info-dir=. lilypond-notation.info
LD_PRELOAD= tar -C %(install_root)s -cjf %(doc_ball)s .
LD_PRELOAD= tar --exclude '*.signature' -C %(builddir)s/out-www/online-root -cjf %(web_ball)s .
''')

Lilypond_doc = LilyPond_doc
