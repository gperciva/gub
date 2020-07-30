from gub import tools 

class Fontforge__tools (tools.AutoBuild):
    # 2020-04-12: the FontForge 2020 March Release drops 'most gnulib and
    # autotools logic in favor of CMake', so use the previous release.
    source = 'https://github.com/fontforge/fontforge/releases/download/20190801/fontforge-20190801.tar.gz'
    dependencies = ['freetype', 'glib-devel', 'libpng', 'libjpeg', 'libuninameslist', 'libxml2', 'python3-devel']
    configure_flags = (tools.AutoBuild.configure_flags
                + ' --without-cairo '
                + ' --without-x '
                + ' --enable-python-scripting=3 '
                + ' PYTHON=%(tools_prefix)s/bin/python3 ')
