#! /bin/sh

me="$0"
root="$HOME"
doc=no
extract=no
interactive=yes
arch=$(uname -m)

if test `id -u` = "0"; then
    root=/usr/local
fi

while test -n "$1";
do
    case "$1" in
	--help)
	    cat <<EOF
$me - install %(pretty_name)s tarball
Options
  --batch             no interaction
  --doc               [attempt to] download and install documentation
  --prefix PREFIX     install into PREFIX/%(name)s (default: ${root})
  --help              this help
  --tarball           extract tar file for archive
EOF
	    exit 0
	    ;;
	--tarball)
	    extract=yes
	    ;;
	--prefix*)
	    root=`echo "$1" | sed -e 's/.*=//g' -e 's/--prefix//g'`
	    if test -z "${root}"; then
		shift
		root="$1"
	    fi
	    if test -z "${root}"; then
		echo 'Option --prefix requires argument.'
		exit 1
	    fi
	    if test ! -d "${root}"; then
		mkdir -p "${root}"
	    fi
	    root=`cd ${root}; pwd`
	    ;;
	--batch)
	    interactive=no
	    ;;
	--doc*)
	    doc=yes
	    ;;
	*)
	    echo Unknown option: $1
	    exit 2
	    ;;
    esac
    shift
done


cat <<EOF

%(name)s installer for version %(version)s release %(release)s,
%(target_cpu)s build.
For a list of options, abort (^C) then do:
sh $me --help

EOF

if test "$arch" != "%(target_cpu)s"; then
    cat <<EOF

Warning: this build is not optimized for your architecture;
please install a ${arch} build instead.

Press C to install the program anyway (not recommended),
E to only extract the program files, or any other key to exit.
EOF
    read -sn1 input 2> /dev/null || read input
    case "$input" in
	C)
	  echo "Ignoring architecture incompatibility."
	;;
	E)
	  extract=yes;
	;;
	*)
	  exit 1
	;;
    esac
fi


if test "$extract" = "yes"; then
    echo "extracting %(base_file)s"
    tail -c+%(header_length)012d $0 > %(base_file)s
    exit 0
fi


if test "$interactive" = "yes"; then
    cat <<EOF

You are about to install %(pretty_name)s in ${root}/%(name)s
A script in ${root}/bin will be created as a shortcut.

Press ^C to abort, or Enter to proceed.
EOF
    read junk
fi


prefix="${root}/%(name)s"
bindir="${root}/bin"
binwrapscript="${bindir}/%(name)s"
uninstall_script="${bindir}/uninstall-%(name)s"
expandargs='"$@"'
dollar='$'
backquote='`'
binaries=%(name)s
EOF=EOF

if test -d "${prefix}"; then
    echo "Directory ${prefix} already exists."
    echo "Remove old %(name)s installations before installing this one."
    if test -x "$uninstall_script"; then
	echo "Run $uninstall_script to uninstall previous version."
    fi
    exit 1
fi

for d in "${prefix}" "${bindir}"; do
    if test ! -d "$d"; then
	echo Making "$d"
	mkdir -p "$d"
    fi
done


################
## Wrappers

echo Creating script $binwrapscript

## LD_LIBRARY_PATH is necessary for ao. FreeBSD.
rm -f "$binwrapscript" > /dev/null 2>&1
cat <<EOF > "$binwrapscript"
#!/bin/sh
me=${backquote}basename ${dollar}0${backquote}
export LD_LIBRARY_PATH="${prefix}/usr/lib"
exec "${prefix}/usr/bin/${dollar}me" $expandargs
EOF
chmod +x "$binwrapscript"

##gtk##cat <<EOF > "$binwrapscript"
##gtk###! /bin/sh
##gtk### relocate script for [gtk+ programs like] denemo, inkscape
##gtk### See http://www.gtk.org/api/2.6/gtk/gtk-running.html
##gtk##
##gtk##INSTALLER_PREFIX=${prefix}/usr
##gtk##ENV=${dollar}HOME/.%(name)s.env
##gtk##
##gtk##cat > ${dollar}ENV <<$EOF
##gtk##INSTALLER_PREFIX=${prefix}/usr
##gtk##if test -d ${dollar}INSTALLER_PREFIX/lib/gtk-2.0/2.10.0/loaders; then
##gtk##    export GIO_MODULE_DIR=${dollar}INSTALLER_PREFIX/lib/gio/modules
##gtk##    export GDK_PIXBUF_MODULEDIR=${dollar}INSTALLER_PREFIX/lib/gtk-2.0/2.10.0/loaders
##gtk##    export GDK_PIXBUF_MODULE_FILE=${dollar}INSTALLER_PREFIX/etc/gtk-2.0/gdk-pixbuf.loaders
##gtk##    export GTK_EXE_PREFIX=${dollar}INSTALLER_PREFIX
##gtk##    export GTK_IM_MODULE_FILE=${dollar}INSTALLER_PREFIX/etc/gtk-2.0/gtk.immodules
##gtk##    export GTK_PATH=${dollar}INSTALLER_PREFIX/lib/gtk-2.0
##gtk##    export GTK_SYSCONFDIR=${dollar}INSTALLER_PREFIX/etc
##gtk##fi
##gtk##export LD_LIBRARY_PATH="${dollar}{INSTALLER_PREFIX}/lib"
##gtk##$EOF
##gtk##
##gtk##for file in ${dollar}INSTALLER_PREFIX/etc/relocate/*.reloc; do
##gtk##    cat ${dollar}file \
##gtk##	| while read line; do
##gtk##	case ${dollar}line in
##gtk##	    set*)
##gtk##		echo ${dollar}line | sed -e 's/^[^ ]* /export /'  >> ${dollar}ENV
##gtk##		;;
##gtk##	    prepend*)
##gtk##		var=${dollar}(expr "${dollar}line" : "^[^ ]* \([^ =]*\)=")
##gtk##		echo ${dollar}line | sed -e 's/^[^ ]* /export /' -e 's/ *([^:])$/\1:$'"${dollar}var/" >> ${dollar}ENV
##gtk##		;;
##gtk##	esac
##gtk##    done
##gtk##done
##gtk##
##gtk##. ${dollar}ENV
##gtk##
##gtk##if test -d "${dollar}GDK_PIXBUF_MODULEDIR" -a ! -f "${dollar}GDK_PIXBUF_MODULE_FILE"; then
##gtk##    ${dollar}INSTALLER_PREFIX/bin/gdk-pixbuf-query-loaders > ${dollar}GDK_PIXBUF_MODULE_FILE
##gtk##fi
##gtk##
##gtk##if test -d "${dollar}GTK_PATH" -a ! -f "${dollar}GTK_IM_MODULE_FILE"; then
##gtk##    ${dollar}INSTALLER_PREFIX/bin/gtk-query-immodules-2.0 > ${dollar}GTK_IM_MODULE_FILE
##gtk##fi
##gtk##
##gtk##me=${backquote}basename ${dollar}0${backquote}
##gtk##exec "${dollar}{INSTALLER_PREFIX}/bin/${dollar}me" $expandargs
##gtk##EOF
##gtk##
#####################
### LilyPond wrappers

wrapscript="${bindir}/%(name)s-wrapper"

for interp in python3 guile; do
    echo "Creating script $wrapscript.$interp"

    rm -f "$wrapscript.$interp" > /dev/null 2>&1
    cat <<EOF > "$wrapscript.$interp"
#!/bin/sh
export PYTHONPATH="${prefix}/usr/lib/lilypond/current/python:${prefix}/usr/share/lilypond/current/python:${dollar}PYTHONPATH"
export GUILE_LOAD_PATH="${prefix}/usr/share/lilypond/current"
export LD_LIBRARY_PATH="${prefix}/usr/lib:${dollar}LD_LIBRARY_PATH"
me=${backquote}basename ${dollar}0${backquote}
exec "${prefix}/usr/bin/$interp" "${prefix}/usr/bin/${dollar}me" $expandargs
EOF
    chmod +x "$wrapscript.$interp"
done

#######################
## symlinks to wrappers

cd ${bindir};
    for a in abc2ly musicxml2ly convert-ly midi2ly etf2ly lilypond-book mup2ly; do
	rm -f $a;
	ln -s $wrapscript.python3 $a;
	binaries="$binaries $a"
    done
    for a in lilypond-invoke-editor; do
	rm -f $a;
	ln -s $wrapscript.guile $a;
	binaries="$binaries $a"
    done
cd - > /dev/null;

###################
## uninstall script

echo Creating script $uninstall_script
cat <<EOF > $uninstall_script
#! /bin/sh

quiet=no
while test -n "${dollar}1";
do
    case "${dollar}1" in
	--help)
	    cat <<BLA
options
  --help    this help
  --quiet   do not ask for confirmation
BLA
	    exit 0
	    ;;
	--quiet)
	    quiet=yes
	    ;;
    esac
    shift
done
if test "${dollar}quiet" = "no"; then
    echo "About to remove a %(name)s installation from ${prefix}"
    echo "Press ^C to abort, Enter to proceed"
    read junk
fi

for binary in ${binaries}; do
    rm ${bindir}/${dollar}binary
done
rm -f $wrapscript.guile $wrapscript.python3
rm -rf ${prefix}
rm $uninstall_script
EOF
chmod +x $uninstall_script

echo Untarring "$me"
tail -c+%(header_length)012d "$0" | tar -C "${prefix}" %(_z)s -xf -

documentation="http://%(name)s.org/doc"

mirror="http://lilypond.org/downloads"
doc_url_base="$mirror/binaries/documentation"
if test "$doc" = yes; then
    documentation="file://${prefix}/usr/share/doc/lilypond/html/index.html
    file://${prefix}/usr/share/info/dir"
    docball=`basename $me | sed -e 's/[.][^.]\+[.]sh/.documentation.tar.bz2/'`
    doc_url="$doc_url_base/$docball"
    if ! test -e $docball; then
	echo "No ./$docball found, downloading."
	wget $doc_url
    fi
    if test -e $docball; then
	echo Untarring "$docball"
	tar -C ${prefix}/usr -xjf $docball
    fi
fi

cat <<EOF
To uninstall %(name)s, run

    ${root}/bin/uninstall-%(name)s

For license and warranty information, consult

    ${prefix}/license/README

Full documentation can be found at

    $documentation

EOF

## need this because binary data starts after this.
exit 0
## END of script
