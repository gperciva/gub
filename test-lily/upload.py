#! /usr/bin/env python2

maintainer = "graham"
maintainer_git_username = "philholmes"

## interaction with lp.org down/upload area.

def argv0_relocation ():
    import os, sys
    bindir = os.path.dirname (sys.argv[0])
    prefix = os.path.dirname (bindir)
    if not prefix:
        prefix = bindir + '/..'
    sys.path.insert (0, prefix)

argv0_relocation ()

import os
import urllib
import re
import string
import sys
import optparse
import pickle
#
from gub.syntax import printf
from gub import versiondb
from gub import misc

platforms = ['linux-x86',
             'linux-64',
             'linux-ppc',
             'darwin-ppc',
             'darwin-x86',
             'documentation',
             'test-output',
             'freebsd-x86',
             'freebsd-64',
             'mingw',
             'cygwin',
             ]

build_platform = {
        'darwin': 'darwin-ppc',
        'linux2': 'linux-x86',
}[sys.platform]

host_spec = maintainer + '@gcp.lilypond.org:/var/www/lilypond'
host_source_spec = host_spec + '/downloads'
host_binaries_spec = host_spec + '/downloads/binaries'
host_doc_spec = host_spec + '/doc'
host_test_spec = host_spec + '/test' 

formats = {
    'darwin-ppc': 'tar.bz2',
    'darwin-x86': 'tar.bz2',

    'linux-x86': 'sh',
    'linux-64': 'sh',
    'linux-arm': 'sh',
    'linux-ppc': 'sh',

    'freebsd4-x86': 'sh',
    'freebsd6-x86': 'sh',
    'freebsd-x86': 'sh',
    'freebsd-64': 'sh',

    'mingw': 'exe',

    'cygwin': 'tar.bz2',

    'documentation': 'tar.bz2',
    'test-output': 'tar.bz2',
    }

def system (c):
    printf (c)
    if os.system (c):
        raise Exception ('barf')

def upload_binaries (repo, version, version_db):
    build = version_db.get_next_build_number (version)
    
    version_str = '.'.join (['%d' % v for v in version])
    branch = repo.branch
    flattened_branch = repo.full_branch_name ()
    dirred_branch = repo.get_ref ()
    
    src_dests = []
    cmds = ['chgrp -R lilypond uploads/lilypond*',
            'chmod -R g+rw uploads/lilypond*',
#            'chmod 4775 `find uploads/cygwin/release -type d`'
            ]


    d = globals ().copy ()
    d.update (locals ())

    d['cwd'] = os.getcwd ()
    # FIXME: what if user changes ~/.gubrc?  should use gubb.Settings!
    d['lilybuild'] = d['cwd'] + '/target/%(build_platform)s/build/lilypond-%(flattened_branch)s' % d
    d['lilysrc'] = d['cwd'] + '/target/%(build_platform)s/src/lilypond-%(flattened_branch)s' % d 

    commitishes = {}
    barf = False
    for platform in platforms:
        format = formats[platform]
        base = ('lilypond-%(version_str)s-%(build)d.%(platform)s.%(format)s'
                % locals ())
        bin = 'uploads/%(base)s' % locals ()

        head_path = 'uploads/lilypond-%(version_str)s-HEAD.%(platform)s.%(format)s' % locals ()
        if os.path.exists (head_path):
            cmds.append('mv %s %s' % (head_path, bin))
            src_dests.append ((os.path.abspath (bin),
                               '%(host)s/%(platform)s' % locals ()))
        elif platform == 'cygwin':
            continue
        elif not os.path.exists (bin):
            printf ('binary does not exist', bin)
            barf = 1
        else:
            ## globals -> locals.
            host = host_binaries_spec 
            src_dests.append ((os.path.abspath (bin),
                               '%(host)s/%(platform)s' % locals ()))

        if (platform not in ('documentation', 'test-output')
             and os.path.exists (bin)):
            branch = repo.full_branch_name ()
            # FIXME: what if user changes ~/.gubrc?  should use gubb.Settings!
            hdr = dict (pickle.load (open ('target/%(platform)s/packages/lilypond-%(branch)s.%(platform)s.hdr' % locals ())))
            key = hdr['source_checksum']
            
            lst = commitishes.get (key, [])
            lst.append (platform)
            
            commitishes[key] = lst
        
        if (platform not in ('documentation', 'test-output')
            and not os.path.exists ('log/%s.test.pdf' % base)):
            printf ('test result does not exist for %s' % base)
            cmds.append ('python test-lily/test-binary.py %s'
                         % os.path.abspath (bin))
            barf = 1

    if len (commitishes) > 1:
        printf ('uploading multiple versions')
        printf ('\n'.join (x.__repr__ () for x in list (commitishes.items ())))
        
    src_tarball = 'uploads/lilypond-%(version_str)s.tar.gz' % locals ()
    src_tarball = os.path.abspath (src_tarball)
    
    if os.path.exists (src_tarball):
        host = host_source_spec 
        majmin = '.'.join (['%d' % v for v in version[:2]])
        src_dests.append ((src_tarball, '%(host)s/sources/v%(majmin)s' % locals ()))
    elif 0:
        printf ('source tarball does not exist', src_tarball)
        barf = True

    test_cmd = r'''python %(cwd)s/test-lily/rsync-lily-doc.py \
  --upload %(host_doc_spec)s \
  --version-file %(lilybuild)s/out/VERSION \
  %(lilybuild)s/out-www/online-root/''' % d
    
    cmds.append (test_cmd)
    if tuple (version[:2]) > (2,10):
        test_cmd = r'''python %(cwd)s/test-lily/rsync-test.py \
  --upload %(host_test_spec)s \
  --version-file %(lilybuild)s/out/VERSION \
  %(lilybuild)s/out-www/online-root/''' % d
        cmds.append (test_cmd)

    cmds += ['rsync --delay-updates --progress %s %s'
             % tup for tup in src_dests]

    ## don't do cygwin .
    ##    cmds.append ('rsync -v --recursive --delay-updates --progress uploads/cygwin/release/ %(host_binaries_spec)s/cygwin/release/' % globals ())
    
    description = repo.git_pipe ('describe --always --abbrev=39 %s' % repo.get_ref ()).strip ()
    
    git_tag = 'release/%(version_str)s-%(build)d' % locals () 
    git_dir = repo.dir
    git_tag_cmd = 'git --git-dir %(git_dir)s tag -m "" -a %(git_tag)s %(dirred_branch)s' % locals ()
    my_maintainer_git_username = maintainer_git_username
    git_push_cmd = 'git --git-dir %(git_dir)s push ssh+git://%(my_maintainer_git_username)s@git.sv.gnu.org/srv/git/lilypond.git/ refs/tags/%(git_tag)s:refs/tags/%(git_tag)s' % locals ()
    git_push_cmd_gitlab = 'git --git-dir %(git_dir)s push git@gitlab.com:lilypond/lilypond.git refs/tags/%(git_tag)s:refs/tags/%(git_tag)s' % locals ()
    gub_tag_cmd = 'git tag -m "release of lilypond %(description)s (%(version_str)s-%(build)d)"  "gub-release-lilypond-%(version_str)s-%(build)d"' % locals ()

    cmds.append (git_tag_cmd)
    cmds.append (git_push_cmd)
    cmds.append (git_push_cmd_gitlab)

    cmds.append (gub_tag_cmd)
    cmds.append ('make -f lilypond.make update-versions')

    return cmds


def get_cli_parser ():
    p = optparse.OptionParser ()

    p.usage = '''lilypondorg.py [OPTION]... COMMAND [PACKAGE]...

Commands:

upload x.y.z      - upload packages
'''
    
    p.description = 'look around on lilypond.org'

    p.add_option ('--branch', action='store',
                  dest='branch',
                  default='master',
                  help='select upload directory')

    p.add_option ('--url', action='store',
                  dest='url',
                  default='localhost/git',
                  help='select hostname/path for git branch')

    p.add_option ('--execute', action='store_true',
                  dest='execute',
                  default=False,
                  help='execute the commands.')

    p.add_option ('--repo-dir', action='store',
                  dest='repo_dir',
                  default='downloads/lilypond',
                  help='select repository directory')

    p.add_option ('--version-db', action='store',
                  dest='version_db',
                  default='versiondb/lilypond.versions',
                  help='version database')
    
    p.add_option ('', '--upload-host', action='store',
                  dest='upload_host',
                  default=host_spec,
                  help='select upload directory')
    return p

def get_repository (options):
    ## do here, because also used in website generation.
    from gub import repository
    dir = options.repo_dir.replace ('.git','')
    repo = repository.Git (dir, source=options.url, branch=options.branch)
    return repo

def main ():
    cli_parser = get_cli_parser ()
    (options, commands)  = cli_parser.parse_args ()

    global host_spec
    host_spec = options.upload_host

    repo = get_repository (options)

    version_dict = misc.grok_sh_variables_str (repo.read_file ('VERSION'))
    version_tup = tuple (map (version_dict.get, ('MAJOR_VERSION', 'MINOR_VERSION', 'PATCH_LEVEL')))
    version_tup = tuple (map (int, version_tup))
    
    version_db = versiondb.VersionDataBase (options.version_db)
    cmds = upload_binaries (repo, version_tup, version_db)

    if options.execute:
        cmds = [c for c in cmds if 'test-binary' not in c]
        for cmd in cmds:
            print (cmd)
            system (cmd)
    else:
        printf ('\n\n')
        printf ('\n'.join (cmds))
        printf ('\n\n')

if __name__ == '__main__':
    main ()
