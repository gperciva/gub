from gub import context
from gub import gnome
from gub import misc
from gub import target
from gub import tools

class Libxml2 (target.AutoBuild):
    source = 'ftp://xmlsoft.org/libxml2/libxml2-2.9.10.tar.gz'
    dependencies = ['zlib']
    configure_flags = (target.AutoBuild.configure_flags
                + misc.join_lines ('''
--without-python
'''))
    @context.subst_method
    def config_script (self):
        return 'xml2-config'

class Libxml2__mingw (Libxml2):
    configure_flags = (Libxml2.configure_flags
                + misc.join_lines ('''
--without-threads
'''))
    def install (self):
        Libxml2.install (self)
        self.copy ('%(install_prefix)s/lib/libxml2.la', '%(install_prefix)s/lib/libxml2-2.la')
        self.copy ('%(install_prefix)s/lib/libxml2.dll.a', '%(install_prefix)s/lib/libxml2-2.dll.a')

class Libxml2__tools (tools.AutoBuild, Libxml2):
    dependencies = Libxml2.dependencies + ['libtool']
    configure_flags = (tools.AutoBuild.configure_flags
                + misc.join_lines ('''
--without-python
'''))
