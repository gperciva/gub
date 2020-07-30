from gub import tools

class P7zip__tools (tools.MakeBuild):
    source = 'http://sourceforge.net/projects/p7zip/files/p7zip/9.20.1/p7zip_9.20.1_src_all.tar.bz2'
    patches = [ 'p7zip-gcc10-conversion.patch' ]
    dependencies = [ 'bzip2', 'system::g++' ]
    install_flags = ' DEST_HOME=%(install_prefix)s install'
    def patch (self):
        tools.MakeBuild.patch (self)
        self.system('''
sed -i -e 's/chmod 555/chmod 755/' -e 's/chmod 444/chmod 644/' %(srcdir)s/install.sh
''')
