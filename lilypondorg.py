#!/usr/bin/python

## interaction with lp.org down/upload area.

import os
import urllib
import re
import string
import sys
import optparse

platforms = ['linux-x86',
      'darwin-ppc',
      'darwin-x86',
      'documentation',
      'freebsd-x86',
#             'linux-arm',
      'mingw']


build_platform = {
	'darwin': 'darwin-ppc',
	'linux2': 'linux',
}[sys.platform]

base_url = 'http://lilypond.org/download'


host_spec = 'hanwen@lilypond.org:/var/www/lilypond'
host_binaries_spec = host_spec + '/download/binaries'
host_doc_spec = host_spec + '/doc'

def get_alias (p):
    try:
        return {
            'linux-x86': 'linux',
            'linux-arm': 'arm',
            'freebsd-x86': 'freebsd',
            }[p]
    except KeyError:
        return p

formats = {
    'linux-x86': 'sh',
    'darwin-ppc': 'tar.bz2',
    'darwin-x86': 'tar.bz2',
    'freebsd-x86': 'sh',
    'mingw':'exe',
    'linux-arm': 'sh',
    'documentation': 'tar.bz2',
    }

def system (c):
    print c
    if os.system (c):
        raise 'barf'

def get_url_versions (url):
    opener = urllib.URLopener ()
    index = opener.open (url).read()

    versions = []
    def note_version (m):
        version = tuple (map (string.atoi,  m.group (1).split('.')))
        build = 0
        build_url = url + re.sub ("HREF=", '', m.group (0))
        build_url = build_url.replace ('"', "")
        
        # disregard buildnumber for src tarball. 
        if m.group(2):
            build = string.atoi (m.group (2))
        versions.append ((version, build, build_url))
        
        return ''

    re.sub (r'HREF="lilypond-([0-9.]+)-?([0-9]+)?\.[0-9a-z-]+\.[.0-9a-z-]+"', note_version, index)
    
    return versions
    

def get_versions (platform):
    url = base_url
    return get_url_versions ('%(url)s/binaries/%(platform)s/'
                             % locals ())

def get_src_versions (maj_min_version):
    (maj_version, min_version) = maj_min_version
    url = base_url
    return get_url_versions ('%(url)s/v%(maj_version)d.%(min_version)d/' %  locals())

def get_max_builds (platform):
    vs = get_versions (platform)

    builds = {}
    for (version, build, url) in vs:
        if builds.has_key (version):
            build = max (build, builds[version][0])

        builds[version] = (build, url)

    return builds
    
def max_branch_version_build_url (branch, platform):
    vbs = get_versions (platform)

    vs = [v for (v,b,u) in vbs if v[0:2] == branch]
    vs.sort()
    try:
        max_version = vs[-1]
    except IndexError:
        max_version = (0,0,0)
        
    max_b = 0
    max_url = ''
    for (v, b, url) in get_versions (platform):
        if v == max_version:
            max_b = max (b, max_b)
            max_url = url

    return (max_version, max_b, max_url)

def max_version_build (platform):
    vbs = get_versions (platform)
    vs = [v for (v,b,u) in vbs]
    vs.sort()
    max_version = vs[-1]

    max_b = 0
    for (v,b,u) in get_versions (platform):
        if v == max_version:
            max_b = max (b, max_b)

    return (max_version, max_b)

def max_src_version_url (maj_min):
    vs = get_src_versions (maj_min)
    vs.sort()
    try:
        return (vs[-1][0], vs[-1][2])
    except:
        ## don't crash.
        return maj_min + (-1,)

def uploaded_build_number (version):
    platform_versions = {}
    build = 0
    for p in platforms:
        vs = get_max_builds (p)
        if vs.has_key (version):
            build = max (build, vs[version][0])

    return build

def upload_binaries (version):
    build = uploaded_build_number (version) + 1
    version_str = '.'.join (['%d' % v for v in version])

    src_dests= []
    barf = 0
    for platform in platforms:
        plat = get_alias (platform)
        
        format = formats[platform]
        
        base = 'lilypond-%(version_str)s-%(build)d.%(plat)s.%(format)s' % locals()
        bin = 'uploads/%(base)s' % locals()
        
        if not os.path.exists (bin):
            print 'binary does not exist', bin
            barf = 1
        else:
            ## globals -> locals.
            host = host_binaries_spec 
            src_dests.append((bin, '%(host)s/%(platform)s' % locals()))
            
        if (platform <> 'documentation'
            and  not os.path.exists ('log/%s.test.pdf' % base)):
            print 'test result does not exist for %s' % base
            barf = 1


    cmds = ['scp %s %s' % tup for tup in src_dests]


    branch = 'HEAD'
    if (version[1] % 2) == 0:
        branch = 'lilypond_%d_%d' % (version[0], version[1])

    entries = open ('downloads/lilypond-%s/CVS/Entries' % branch).read ()
    changelog_match = re.search ('/ChangeLog/([0-9.]+)/([^/]+)', entries)
    changelog_rev = changelog_match.group (1)
    changelog_date = changelog_match.group (2)
    
    tag_cmd = 'darcs tag --patch "release %(version_str)s-%(build)d of ChangeLog rev %(changelog_rev)s %(changelog_date)s"' % locals()


    cmds.append (tag_cmd)
    d = globals().copy()
    d.update (locals())

    d['lilybuild'] = 'target/%(build_platform)s/build/lilypond-%(branch)s' % d
    d['lilysrc'] = 'target/%(build_platform)s/src/lilypond-%(branch)s' % d 

    test_cmd =r'''PYTHONPATH=%(lilysrc)s/python python test-lily/rsync-lily-doc.py \
  --upload %(host_doc_spec)s \
  %(lilybuild)s/out-www/web-root/''' % d

    cmds.insert (0, test_cmd)
    
    print '\n\n'
    print '\n'.join (cmds);
    print '\n\n'
    if barf:
        raise Exception ('barf')

    for cmd in cmds:
        system (cmd)


def get_cli_parser ():
    p = optparse.OptionParser ()

    p.usage="""lilypondorg.py [OPTION]... COMMAND [PACKAGE]...

Commands:

upload x.y.z      - upload packages
nextbuild x.y.z   - get next build number

"""
    p.description='look around on lilypond.org'

    p.add_option ('', '--url', action='store',
                  dest='url',
                  default=base_url,
                  help='select base url')
    
    p.add_option ('', '--upload-host', action='store',
                  dest='upload_host',
                  default=host_spec,
                  help='select upload directory')
    
    return p

def main ():
    cli_parser = get_cli_parser ()
    (options, commands)  = cli_parser.parse_args ()

    global base_url, host_spec
    base_url = options.url
    host_spec = options.upload_host

    command = commands[0]
    commands = commands[1:]
    
    if command == 'nextbuild':
        version = tuple (map (string.atoi, commands[0].split ('.')))
        print uploaded_build_number (version) + 1
    elif command == 'upload':
        version = tuple (map (string.atoi, commands[0].split ('.')))
        upload_binaries (version)
    else:
        base_url = "http://download.linuxaudio.org/lilypond"
        print max_src_version_url ((2,9))
        print max_version_build ('documentation')
        print max_branch_version_build_url ((2, 6), 'linux-x86')
        print max_branch_version_build_url ((2, 9), 'linux-x86')

if __name__ == '__main__':
    main()
        
