
# FIXME: added option to add source as static build class member
# see flex.  Remove/deprecate this central source feature?
# Use only for local overrides?

# We have to find out what we want.  It is nice to have build classes
# be independent of source urls, and take a source url and list of
# patches.  Otoh, it is nice for a build class to be self-contained.
# This is a much more pluggable design for adding packages than also
# needing to update a central file.


from os.path import join
from gub import mirrors

gnu = 'http://ftp.gnu.org/pub/gnu'
nongnu = 'http://download.savannah.nongnu.org/releases'
sf = 'http://surfnet.dl.sourceforge.net/sourceforge'
gub = 'http://lilypond.org/downloads/gub-sources'
lp = 'http://lilypond.org/downloads/sources'
freedesktop = '.freedesktop.org/releases'

ltool = mirrors.gnu % { 'name': 'libtool', 'version': '1.5.22', 'format': 'gz'}

libtool = join (gnu, 'libtool/libtool-1.5.22.tar.gz')
# libtool = 'http://ftp.gnu.org/pub/gnu/libtool/libtool-1.5.22.tar.gz'

# foo__PLATFORM should also work here

#automake = join (gnu, 'automake/automake-1.10.tar.gz')
distcc = 'http://distcc.samba.org/ftp/distcc/distcc-2.18.3.tar.bz2'
expat = join (sf, 'expat/expat-1.95.8.tar.gz')
#flex = join (sf, 'flex/flex-2.5.4a.tar.gz')
flex = join (sf, 'bex/flex-2.5.4a.tar.gz')
freetype = join (nongnu, 'freetype/freetype-2.1.10.tar.gz')
gettext = join (gnu, 'gettext/gettext-0.15.tar.gz')
# git = 'http://kernel.org/pub/software/scm/git/git-1.5.1.4.tar.bz2'
guile = join (gnu, 'guile/guile-1.8.2.tar.gz')
gmp = join (gnu, 'gmp/gmp-4.2.1.tar.gz')
icoutils = join (nongnu, 'icoutils/icoutils-0.26.0.tar.gz')
libpng = join (sf, 'libpng/libpng-1.2.8-config.tar.gz')
mftrace = join (lp, 'mftrace/mftrace-1.2.14.tar.gz')
pkg_config = 'https://pkg-config' + join (freedesktop, 'pkg-config-0.29.2.tar.gz')
potrace = join (sf, 'potrace/potrace-1.7.tar.gz')
python = 'https://www.python.org/ftp/python/%(version)s/Python-2.4.2.tar.bz2'
imagemagick = 'http://www.imagemagick.org/download/releases/ImageMagick-6.5.7-9.tar.gz'
texinfo = join (gnu, 'texinfo/texinfo-4.8.tar.bz2')
ghostscript  = 'ftp://mirror.cs.wisc.edu/pub/mirrors/ghost/GPL/gs860/ghostscript-8.60.tar.bz2'
