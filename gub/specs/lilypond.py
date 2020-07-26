import os
#
from gub import build
from gub import context
from gub import loggedos
from gub import misc
from gub import repository
from gub import target
from gub import versiondb
from gub.specs import ghostscript

VERSION='v2.14'
def url (version=VERSION):
    url = 'http://lilypond.org/downloads/source/%(version)s/' % locals ()
    raw_version_file = 'lilypond-%(version)s.index' % locals ()
    return misc.latest_url (url, 'lilypond', raw_version_file)

class LilyPond__simple (target.AutoBuild):
    '''A program for printing sheet music
LilyPond lets you create music notation.  It produces beautiful
sheet music from a high-level description file.'''

    source = 'git://git.sv.gnu.org/lilypond.git'
#    source = url () # for release builds
    branch = 'master'
    subpackage_names = ['']
    dependencies = [
        'cross/gcc-c++-runtime',

        'flex',
        'fontconfig-devel',
        'freetype-devel',
        'gettext-devel',
        'ghostscript',
        'guile-devel',
        'pango-devel',
        'python3-devel',
        'tools::fonts-texgyre',
        'tools::fonts-urw-core35',

        'tools::autoconf',
        'tools::bison',
        'tools::flex',
        'tools::fontforge',
        'tools::gettext', # AM_GNU_GETTEXT
        'tools::pkg-config',
        'tools::t1utils',
        'tools::texi2html',
        'tools::texinfo',
        'tools::ghostscript',
        'tools::extractpdfmark',
        #'tools::texlive',

        'system::mf', 
        'system::mpost', 
        'system::xetex',
        'system::xelatex',
        ]
    if 'stat' in misc.librestrict ():
        dependencies = [x for x in dependencies
                        if x not in ['system::mf', 'system::mpost']
                        ] + [
            'tools::texlive'
            ]
    configure_flags = (target.AutoBuild.configure_flags
                       + ' --enable-relocation'
                       + ' --enable-rpath'
                       + ' --disable-documentation'
                       + ' --with-texgyre-dir=%(tools_prefix)s/share/fonts/opentype/texgyre'
                       + ' --with-urwotf-dir=%(tools_prefix)s/share/fonts/opentype/urw-core35'
                       )
    make_flags = ' TARGET_PYTHON=/usr/bin/python3'

    if 'stat' in misc.librestrict ():
        home = os.environ['HOME']
        make_flags = (make_flags
                      + ' LIBRESTRICT_ALLOW=%(home)s/.texlive2009/:%(home)s/texmf/' % locals ())
    @staticmethod
    def version_from_VERSION (self):
        return self.version_from_shell_script (
            'VERSION', 'MAJOR_VERSION',
            '%(MAJOR_VERSION)s.%(MINOR_VERSION)s.%(PATCH_LEVEL)s')

    @staticmethod
    def bind_version (self):
        self.version = misc.bind_method (LilyPond.version_from_VERSION, self)

    def __init__ (self, settings, source):
        target.AutoBuild.__init__ (self, settings, source)
        # FIXME: should add to C_INCLUDE_PATH
        builddir = self.builddir ()
        # FIXME: remove after both 2.12.3, 2.13.4 (or 2.14.0) are released.
        srcdir = self.srcdir ()
        self.target_gcc_flags = (settings.target_gcc_flags
                                 + ' -I%(builddir)s' % locals ()
                                 + ' -I%(srcdir)s/lily/out' % locals ())
        if isinstance (source, repository.Git):
            if source.is_downloaded ():
                source.version = misc.bind_method (LilyPond.version_from_VERSION, source)
            else:
                source.post_download_hook = misc.bind_method (LilyPond.bind_version, source)
        if 'stat' in misc.librestrict () and not 'tools::texlive' in self.dependencies:
            build.append_dict (self, {'PATH': os.environ['PATH']}) # need mf, mpost from system
    def get_conflict_dict (self):
        return {'': ['lilypondcairo']}
    def build_version (self):
        v = self.source.version ()
        self.runner.info ('LILYPOND-VERSION: %(v)s\n' % locals ())
        return v
    def patch (self):
        target.AutoBuild.patch (self)
        # system::xetex uses system's shared libraries instead of GUB's ones.
        self.file_sub ([('^exec xetex ', 'LD_LIBRARY_PATH= exec xetex ')],
                       '%(srcdir)s/scripts/build/xetex-with-options.sh')

        # system::xelatex uses system's shared libraries instead of GUB's ones.
        self.file_sub ([('^exec xelatex ',
                         'LD_LIBRARY_PATH= exec xelatex ')],
                       '%(srcdir)s/scripts/build/xelatex-with-options.sh')
    def configure (self):
        target.AutoBuild.configure (self)
        # tools::extractpdfmark uses system's libstdc++ instead of GUB's one.
        self.file_sub ([('^EXTRACTPDFMARK = ([^L].*)$',
                         'EXTRACTPDFMARK = LD_LIBRARY_PATH=%(tools_prefix)s/lib \\1')],
                       '%(builddir)s/config.make')
    def install (self):
        target.AutoBuild.install (self)
        self.system ('cp %(tools_prefix)s/share/doc/texgyre/GUST-FONT-LICENSE.txt %(install_root)s/license/fonts-texgyre')
        self.system ('cp %(tools_prefix)s/share/doc/urw-core35/LICENSE %(install_root)s/license/fonts-urw-core35')
        # FIXME: This should not be in generic package, for installers only.
        self.installer_install_stuff ()
    def installer_install_stuff (self):
        # FIXME: is it really the installer version that we need here,
        # or do we need the version of lilypond?
        installer_version = self.build_version ()
        # WTF, current.
        self.system ('cd %(install_prefix)s/share/lilypond && mv %(installer_version)s current',
                     locals ())

        self.system ('mkdir -p %(install_prefix)s/etc/fonts/')
        self.dump ('''\
<fontconfig>
  <cachedir>~/.lilypond-fonts.cache-2</cachedir>
</fontconfig>
''',
            '%(install_prefix)s/etc/fonts/local.conf', 'w', locals ())

class LilyPond__smart (LilyPond__simple):
    configure_binary = '%(srcdir)s/smart-configure.sh'
    if 'stat' in misc.librestrict ():
        def patch (self):
            LilyPond__simple.patch (self)
            # How weird is this?  With LIBRESTRICT=open:stat [see
            # TODO] the set -eux carry over into autoconf and
            # configure runs.
            for i in ('smart-autogen.sh', 'smart-configure.sh'):
                self.file_sub ([
                        ('^([$][{]?srcdir[}]?/.*$)', r'(set +eux; \1) || exit 1'),
                        ], '%(srcdir)s/' + i)
    def autoupdate (self):
        self.system ('cd %(srcdir)s && ./smart-autogen.sh --noconfigure') 

LilyPond = LilyPond__smart

class LilyPond__freebsd (LilyPond):
    dependencies = LilyPond.dependencies + ['cross/gcc-runtime']

## shortcut: take python out of dependencies
class LilyPond__no_python (LilyPond):
    dependencies = [x for x in LilyPond.dependencies
                if x != 'python3-devel']
    def configure (self):
        self.system ('mkdir -p %(builddir)s || true') 
        self.system ('touch %(builddir)s/Python.h') 
        LilyPond.configure (self)
        self.dump ('''
all:
        true

install:
        -mkdir -p $(DESTDIR)%(prefix_dir)s/lib/lilypond/%(version)s
''', '%(builddir)s/python/GNUmakefile')
        
class LilyPond__mingw (LilyPond):
    dependencies = LilyPond.dependencies + [
            'tools::imagemagick',
            'tools::icoutils',
            'mingw-w64-runtime-winpthread-dll',
            ]
    # ugh Python hack: C&P Cygwin
    def compile (self):
        self.system ('''
cd %(builddir)s/lily && rm -f out/lilypond
''')
        LilyPond.compile (self)
        self.system ('''
cd %(builddir)s/lily && mv out/lilypond out/lilypond-console
cd %(builddir)s/lily && make MODULE_LDFLAGS='-mwindows'
cd %(builddir)s/lily && mv out/lilypond out/lilypond-windows
cd %(builddir)s/lily && touch out/lilypond
''')
    def configure (self):
        LilyPond.configure (self)
        self.file_sub ([(' -mwindows', ' '),
                        (' -g ', ' '),],
                       '%(builddir)s/config.make')
    def install (self):
        LilyPond.install (self)
        self.system ('''
rm -f %(install_prefix)s/bin/lilypond
install -m755 %(builddir)s/lily/out/lilypond-windows %(install_prefix)s/bin/lilypond-windows.exe
install -m755 %(builddir)s/lily/out/lilypond-console %(install_prefix)s/bin/lilypond.exe
cp %(install_prefix)s/share/lilypond/*/python/*.py %(install_prefix)s/bin
''')
        def rename (logger, name):
            header = open (name).readline ().strip ()
            if header.endswith ('guile'):
                loggedos.system (logger, 'mv %(name)s %(name)s.scm' % locals ())
            elif header.endswith ('python') and not name.endswith ('.py'):
                loggedos.system (logger, 'mv %(name)s %(name)s.py' % locals ())
        def asciify (logger, name):
            loggedos.file_sub (logger, [('\r*\n', '\r\n')], name)
        self.map_locate (rename, self.expand ('%(install_prefix)s/bin/'), '*')
        self.map_locate (asciify, self.expand ('%(install_root)s'), '*.ly')
        bat = r'''@echo off
"@INSTDIR@\usr\bin\lilypond-windows.exe" -dgui %1 %2 %3 %4 %5 %6 %7 %8 %9
'''.replace ('%', '%%').replace ('\n', '\r\n')
            
        self.dump (bat, '%(install_prefix)s/bin/lilypond-windows.bat.in')

class LilyPond__darwin (LilyPond):
    dependencies = (LilyPond.dependencies
                # FIXME: move to lilypond-installer.py, see __mingw.
                + [
                'fondu',
                'osx-lilypad',
                ])
    configure_flags = (LilyPond.configure_flags
                .replace ('--enable-rpath', '--disable-rpath'))
    make_flags = ' TARGET_PYTHON="/usr/bin/env python3"'

class LilyPond__darwin__ppc (LilyPond__darwin):
    def configure (self):
        LilyPond__darwin.configure (self)
        self.dump ('CXXFLAGS += -fpermissive -DGUILE_ELLIPSIS=...',
                   '%(builddir)s/local.make')

class LilyPond_base (target.AutoBuild):
    source = LilyPond.source
    branch = LilyPond.branch
    install_after_build = False
    ghostscript_version = ghostscript.Ghostscript.static_version ()
    def __init__ (self, settings, source):
        target.AutoBuild.__init__ (self, settings, source)
        if isinstance (source, repository.Git):
            source.source = source.source.replace (self.name (), 'lilypond')
            source.dir = source.dir.replace (self.name (), 'lilypond')
            source.url_dir = source.url_dir.replace (self.name (), 'lilypond')
            source.version = misc.bind_method (LilyPond.version_from_VERSION, source)
            source.is_tracking = misc.bind_method (lambda x: True, source)
            source.is_downloaded = misc.bind_method (lambda x: True, source)
            source.update_workdir = misc.bind_method (lambda x: True, source)
            self.dependencies = (self.__class__.dependencies
                                 + [self.settings.target_platform + '::'
                                    + source.source + '?branch=' + source.branch])
    subpackage_names = ['']
    def stages (self):
        return ['compile', 'install', 'package']
    def builddir (self):
        #URWGSGSEWNG
        return '%(allbuilddir)s/lilypond%(ball_suffix)s'
    def srcdir (self):
        #URWGSGSEWNG
        return '%(allsrcdir)s/lilypond%(ball_suffix)s'

    @context.subst_method
    def doc_limits (self):
        if '64' in self.settings.build_platform:
            return 'ulimit -m 1048576 && ulimit -d 1048576 && ulimit -v 3145728'
        return 'ulimit -m 524288 && ulimit -d 524288 && ulimit -v 1048576'
    @context.subst_method
    def doc_relocation (self):
        # These environment variables control lilypond while being run
        # within gub to build documentation.  In particular, we use a
        # special fontconfig setup that doesn't use fonts outside of gub.
        return misc.join_lines ('''
LILYPOND_EXTERNAL_BINARY=%(system_prefix)s/bin/lilypond
PATH=%(tools_prefix)s/bin:%(system_prefix)s/bin:$PATH
MALLOC_CHECK_=2
LD_LIBRARY_PATH=%(tools_prefix)s/lib:%(system_prefix)s/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
GS_FONTPATH=%(system_prefix)s/share/ghostscript/%(ghostscript_version)s/fonts:%(system_prefix)s/share/gs/fonts
GS_LIB=%(system_prefix)s/share/ghostscript/%(ghostscript_version)s/Resource/Init:%(system_prefix)s/share/ghostscript/%(ghostscript_version)s/Resource
FONTCONFIG_FILE=%(system_prefix)s/etc/fonts-gub/fonts.conf
FONTCONFIG_PATH=%(tools_prefix)s/etc/fonts-gub
''')
    compile_command = ('%(doc_limits)s '
                '&& %(doc_relocation)s '
                + target.AutoBuild.compile_command)
    install_command = ('%(doc_limits)s '
                '&& %(doc_relocation)s '
                + target.AutoBuild.install_command)

Lilypond_base = LilyPond_base

#Hmm
Lilypond = LilyPond
Lilypond__darwin = LilyPond__darwin
Lilypond__darwin__ppc = LilyPond__darwin__ppc
Lilypond__freebsd = LilyPond__freebsd
Lilypond__mingw = LilyPond__mingw
