from gub import build
from gub import context
from gub import misc
from gub import tools

class ImageMagick__tools (tools.AutoBuild):
    source = 'http://www.imagemagick.org/download/releases/ImageMagick-6.9.11-28.tar.xz'
    dependencies = [
            'automake',
            'bzip2',
            'fontconfig',
            'ghostscript',
            'libpng',
            'libjpeg',
            'libtiff',
            'libxml2',
            'libtool',
            'perl',
            'zlib',
            'tools::xzutils',
            ]
    configure_flags = (tools.AutoBuild.configure_flags
                + misc.join_lines ('''
--enable-zero-configuration
--without-magick-plus-plus
--without-perl
--disable-openmp
'''))
    # Setting `CFLAGS' is not sufficient since ImageMagick's `configure'
    # script prepends stuff for libraries like libpng to `CFLAGS'.  We thus
    # explicitly set `INCLUDES' (as documented in the automake info file) to
    # ensure that the path to gub's header files comes first.
    #
    # However, there seems to be a bug (or a feature) in at least gcc 4.8.5:
    # Directories in the environment variable `C_INCLUDE_PATH' are processed
    # similar to `-isystem' arguments, this is, they are handled after `-I'
    # options but before standard system directories.  Alas, if a directory
    # `foo' appears in both `C_INCLUDE_PATH' and as an argument to `-I', the
    # latter is obviously ignored.  For this reason we have to unset
    # `C_INCLUDE_PATH' (which is set by gub) to really get gub's C header
    # directory first.
    make_flags = (tools.AutoBuild.make_flags
                  + ' INCLUDES=-I%(tools_prefix)s/include '
                  + ' C_INCLUDE_PATH=')

class ImageMagick__tools__autoupdate (ImageMagick__tools):
    def autoupdate (self):
        self.system ('''
cd %(autodir)s && libtoolize --copy --force --automake --ltdl
cd %(autodir)s && autoheader -I m4 -I %(system_prefix)s/share/aclocal
cd %(autodir)s && aclocal -I m4 -I %(system_prefix)s/share/aclocal
cd %(autodir)s && autoconf -I m4 -I %(system_prefix)s/share/aclocal
cd %(autodir)s && automake --add-missing --copy --foreign
''')
    def configure (self):
        tools.AutoBuild.configure (self)
        self.file_sub ([('(( *)install_libdir="\$2")',
                         r'''\1
\2if test -z "$install_libdir"; then
\2    install_libdir=%(system_prefix)s/lib;
\2fi
''')],
                       '%(builddir)s/libtool')

# Hmm, see LilyPond
Imagemagick__tools = ImageMagick__tools
