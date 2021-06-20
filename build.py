#!/bin/env python3

pkgver = '89.0.1'
nightly_ver = '91.0a1'

#
# pybuild.py - try move functionality away from that too big/horrible build script.
#

import optparse
import sys
import os
import glob
import time

start_time = time.time()
parser = optparse.OptionParser()

parser.add_option('-x', '--cross',         dest='cross_compile', default=False, action="store_true")
parser.add_option('-n', '--no-execute',    dest='no_execute',    default=False, action="store_true")
parser.add_option('-l', '--no-librewolf',  dest='no_librewolf',  default=False, action="store_true")
parser.add_option('-s', '--src',           dest='src',           default='release')
parser.add_option('-t', '--distro',        dest='distro',        default='win')
parser.add_option('-T', '--token',         dest='token',         default='')

options, remainder = parser.parse_args()
                
def script_exit(statuscode):
        if (time.time() - start_time) > 60:
                # print elapsed time
                elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
                print(f"\n\aElapsed time: {elapsed}")

        sys.exit(statuscode)
        
def enter_srcdir():
        dir = "firefox-{}".format(pkgver)
        if options.src == 'nightly':
                dir = 'mozilla-unified'
        elif options.src == 'tor-browser':
                dir = 'tor-browser'
        print("cd {}".format(dir))
        if not options.no_execute:
                try:
                        os.chdir(dir)
                except:
                        print("fatal error: can't change to '{}' folder.".format(dir))
                        script_exit(1)
                
def leave_srcdir():
        print("cd ..")
        if not options.no_execute:
                os.chdir("..")
        
def exec(cmd):
        print(cmd)
        if not options.no_execute:
                retval = os.system(cmd)
                if retval != 0:
                        print("fatal error: command '{}' failed".format(cmd))
                        script_exit(1)

def patch(patchfile):
        cmd = "patch -p1 -i {}".format(patchfile)
        print(cmd)
        if not options.no_execute:
                retval = os.system(cmd)
                if retval != 0:
                        print("fatal error: patch '{}' failed".format(patchfile))
                        script_exit(1)


#        
# Utilities:
#



def execute_update_submodules():
        exec("git submodule update --recursive")
        exec("git submodule foreach git pull origin master")
        exec("git submodule foreach git merge origin master")

def execute_git_init():
        if options.src != 'release':
            print("fatal error: git_init only works with the release source (--src release)")
            script_exit(1)
        enter_srcdir()
        exec("rm -rf .git")
        exec("git init")
        exec("git config core.safecrlf false")
        exec("git config commit.gpgsign false")
        exec("git add -f * .[a-z]*")
        exec("git commit -am initial")
        leave_srcdir()
        
        
def execute_deps_deb():
        deps1 = "python python-dev python3 python3-dev python3-distutils clang pkg-config libpulse-dev gcc"
        deps2 = "curl wget nodejs libpango1.0-dev nasm yasm zip m4 libgtk-3-dev libgtk2.0-dev libdbus-glib-1-dev"
        deps3 = "libxt-dev python3-pip mercurial automake autoconf libtool m4"
        exec("apt install -y {} {} {}".format(deps1,deps2,deps3))
        
def execute_deps_rpm():
        deps1 = "python3 python3-distutils-extra clang pkg-config gcc curl wget nodejs nasm yasm zip m4"
        deps2 = "python3-zstandard python-zstandard python-devel python3-devel gtk3-devel llvm gtk2-devel dbus-glib-devel libXt-devel pulseaudio-libs-devel"
        exec("dnf -y install {} {}".format(deps1,deps2))
        
def execute_deps_pkg():
        deps = "wget gmake m4 python3 py37-sqlite3 pkgconf llvm node nasm zip unzip yasm"
        exec("pkg install {}".format(deps))

        
def execute_rustup():        
        # rust needs special love: https://www.atechtown.com/install-rust-language-on-debian-10/
        exec("curl https://sh.rustup.rs -sSf | sh")
        exec("cargo install cbindgen")
        
def execute_mach_env():
        enter_srcdir()
        exec("bash ./mach create-mach-environment")
        leave_srcdir()
        

def execute_reset():
        if options.src == 'release':
                path = "firefox-{}/.git/index".format(pkgver)
                if not os.path.isfile(path):
                        print("fatal error: cannot reset '--src release' sources as it's not under version control.")
                        script_exit(1)
                enter_srcdir()
                exec("git reset --hard")
                leave_srcdir()
        elif options.src == 'nightly':
                enter_srcdir()
                exec("hg up -C")
                exec("hg purge")
                exec("hg pull -u")
                leave_srcdir()
        elif options.src == 'tor-browser':
                enter_srcdir()
                exec("git reset --hard")
                leave_srcidr()


        

#
# Targets:
#


def execute_fetch():
        if options.src == 'release':
                exec("rm -f firefox-{}.source.tar.xz".format(pkgver))
                exec("wget -q https://archive.mozilla.org/pub/firefox/releases/{}/source/firefox-{}.source.tar.xz".format(pkgver, pkgver))
        elif options.src == 'nightly':
                exec("rm -f bootstrap.py")
                exec("rm -rf mozilla-unified")
                exec("wget -q https://hg.mozilla.org/mozilla-central/raw-file/default/python/mozboot/bin/bootstrap.py")
                exec("python3 bootstrap.py --no-interactive --application-choice=browser")
        elif options.src == 'tor-browser':
                exec("rm -rf tor-browser")
                exec("git clone --no-checkout --recursive https://git.torproject.org/tor-browser.git")
                enter_srcdir()
                exec("git checkout tor-browser-89.0-10.5-1-build1")
                exec("git submodule update --recursive")
                patch("../patches/tb-mozconfig-win10.patch")
                leave_srcdir()

def execute_extract():
        if options.src == 'release':
                exec("rm -rf firefox-{}".format(pkgver))
                exec("tar xf firefox-{}.source.tar.xz".format(pkgver))
        
def execute_build():
        enter_srcdir()
        exec("bash ./mach build")
        leave_srcdir()
        
def execute_package():
        enter_srcdir()
        exec("bash ./mach package")
        leave_srcdir()








        
#
# LibreWolf specific:
#

def create_mozconfig(contents):
        if not options.no_execute:
                f = open('mozconfig', 'w')
                f.write(contents)
                f.close()

def execute_lw_do_patches():
        if options.no_librewolf:
                return
        if not options.src in ['release','nightly']:
                return

        enter_srcdir()
        # create the right mozconfig file..
        create_mozconfig(mozconfig_release)
        
        # copy branding files..
        exec("cp -vr ../common/source_files/* .")
        exec("cp -v ../files/configure.sh browser/branding/librewolf")

        patches = [
                "../common/patches/context-menu.patch",
                "../common/patches/remove_addons.patch",
                "../common/patches/megabar.patch",
                "../common/patches/mozilla-vpn-ad.patch",
                "../common/patches/allow_dark_preference_with_rfp.patch",
                "../common/patches/about-dialog.patch",
                
                # sed patches..
                "../common/patches/sed-patches/allow-searchengines-non-esr.patch",
                "../common/patches/sed-patches/disable-pocket.patch",
                "../common/patches/sed-patches/remove-internal-plugin-certs.patch",
                "../common/patches/sed-patches/stop-undesired-requests.patch",
                ]
                
        for p in patches:
            patch(p)
            
        # local windows patches
        for p in ["../patches/browser-confvars.patch", "../patches/package-manifest.patch"]:
            patch(p)

                
        leave_srcdir()


def get_objdir():
        pattern = "obj-*"
        retval = glob.glob(pattern)
        if options.no_execute:
                return "obj-XXX"
        if len(retval) != 1:
                print("fatal error: in execute_lw_post_build(): cannot glob build output folder '{}'".format(pattern))
                script_exit(1)
        return retval[0]
        
def execute_lw_post_build():
        if options.no_librewolf:
                return
        enter_srcdir()
        dirname = get_objdir()

        if not options.no_execute:
                os.makedirs("{}/dist/bin/defaults/pref".format(dirname), exist_ok=True)
                os.makedirs("{}/dist/bin/distribution".format(dirname), exist_ok=True)
        exec("cp -v ../settings/defaults/pref/local-settings.js {}/dist/bin/defaults/pref/".format(dirname))
        exec("cp -v ../settings/distribution/policies.json {}/dist/bin/distribution/".format(dirname))
        exec("cp -v ../settings/librewolf.cfg {}/dist/bin/".format(dirname))
        leave_srcdir()
        
def execute_lw_artifacts():
        if options.no_librewolf:
                return
        
        enter_srcdir()
        
        if options.distro == 'win':
                exe = ".exe"
                ospkg = "win64"
                dirname = "{}/dist/firefox".format(get_objdir())
        elif options.distro == 'deb':
                exe = ""
                ospkg = "deb"
                dirname = "{}/dist/firefox".format(get_objdir())
        elif options.distro == 'rpm':
                exe = ""
                ospkg = "rpm"
                dirname = "{}/dist/firefox".format(get_objdir())

        exec("rm -rf ../firefox ../librewolf")
        exec("cp -rv {} ..".format(dirname))
        leave_srcdir()
        
        exec("mv firefox librewolf")
        exec("mv -v librewolf/firefox{} librewolf/librewolf{}".format(exe,exe));
        exec("rm -rf librewolf/maintainanceservice* librewolf/pingsender* librewolf/firefox.*.xml librewolf/precomplete librewolf/removed-files librewolf/uninstall")
        exec("cp -v common/source_files/browser/branding/librewolf/firefox.ico librewolf/librewolf.ico")
        if options.distro != 'win':
                exec("cp -v files/register-librewolf files/start-librewolf files/start-librewolf.desktop.in librewolf")
        
        # create zip file
        if options.src == 'release':
                zipname = "librewolf-{}.en-US.{}.zip".format(pkgver,ospkg)
        elif options.src == 'nightly':
                zipname = "librewolf-{}.en-US.{}-nightly.zip".format(nightly_ver,ospkg)

        exec("rm -f {}".format(zipname))
        exec("zip -qr9 {} librewolf".format(zipname))
        
        # create installer
        if options.distro == 'win':
                setupname = "librewolf-{}.en-US.win64-setup.exe".format(pkgver)
                if options.src == 'nightly':
                        if os.path.isfile(setupname):
                                exec("rm -f tmp.exe")
                                exec("mv {} tmp.exe".format(setupname))
                        setupname = "librewolf-{}.en-US.win64-nightly-setup.exe".format(nightly_ver)
                        
                exec("rm -f {} tmp.nsi".format(setupname))
                exec("sed \"s/pkg_version/{}/g\" < setup.nsi > tmp.nsi".format(pkgver))
                exec("makensis-3.01.exe -V1 tmp.nsi")
                exec("rm -f tmp.nsi")
                if os.path.isfile("tmp.exe"):
                        exec("mv librewolf-{}.en-US.win64-setup.exe {}".format(pkgver,setupname))
                        exec("mv tmp.exe librewolf-{}.en-US.win64-setup.exe".format(pkgver))

def do_upload(filename):
        exec("echo "" >> upload.txt")
        exec("curl --request POST --header \"PRIVATE-TOKEN: {}\" --form \"file=@{}\" \"https://gitlab.com/api/v4/projects/13852981/uploads\" >> upload.txt".format(options.token,filename))
        exec("echo "" >> upload.txt")
        
def execute_upload():
        if options.token =='':
                print("fatal error: You must specify a private token when using the 'upload' command.")
                script_exit(1)

        if options.distro == 'win':
                ospkg = "win64"
        elif options.distro == 'deb':
                ospkg = "deb"
        elif options.distro == 'rpm':
                ospkg = "rpm"

                
        zip_filename = "librewolf-{}.en-US.{}.zip".format(pkgver,ospkg)
        setup_filename = "librewolf-{}.en-US.win64-setup.exe".format(pkgver)
        nightly_setup_filename = "librewolf-{}.en-US.win64-nightly-setup.exe".format(nightly_ver)
        
        if not os.path.isfile(zip_filename):
                print("fatal error: File '{}' not found.".format(zip_filename))
                script_exit(1)
        if not os.path.isfile(setup_filename):
                print("fatal error: File '{}' not found.".format(setup_filename))
                script_exit(1)
        if not os.path.isfile(nightly_setup_filename):
                print("fatal error: File '{}' not found.".format(nightly_setup_filename))
                script_exit(1)

        exec("sha256sum {} {} {} > sha256sums.txt".format(zip_filename,setup_filename,nightly_setup_filename))
        exec("rm -f upload.txt")
        do_upload(setup_filename)
        do_upload(zip_filename)
        do_upload(nightly_setup_filename)
        do_upload("sha256sums.txt")

#
# Main targets:
#


def execute_all():
        execute_fetch()
        execute_extract()
        execute_lw_do_patches()
        execute_build()
        execute_lw_post_build()
        execute_package()
        execute_lw_artifacts() 

def execute_clean():
        exec("rm -rf firefox-{} mozilla-unified tor-browser".format(pkgver))
        exec("rm -rf librewolf firefox-{}.source.tar.xz bootstrap.py tmp.nsi tmp.exe".format(pkgver))

def execute_veryclean():
        execute_clean()
        exec("rm -f sha256sums.txt pybuild.upload.txt")
        for filename in glob.glob("librewolf-*"):
                os.remove(filename)
        





        



#
# main commandline interface
#

def main():
        if options.src == 'tor-browser':
                options.no_librewolf = True

        if len(remainder) > 0:
                if not options.src in ['release','nightly','tor-browser']:
                        print("error: option --src invalid value")
                        script_exit(1)
                if not options.distro in ['deb','rpm', 'win']:
                        print("error: option --distro invalid value")
                        script_exit(1)

                for arg in remainder:
                        if arg == 'all':
                                execute_all()
                        elif arg == 'clean':
                                execute_clean()
                        elif arg == 'veryclean':
                                execute_veryclean()
                        
                        # Targets:
                        
                        elif arg == 'fetch':
                                execute_fetch()
                        elif arg == 'extract':
                                execute_extract()
                        elif arg == 'lw_do_patches':
                                execute_lw_do_patches()
                        elif arg == 'build':
                                execute_build()
                        elif arg == 'lw_post_build':
                                execute_lw_post_build()
                        elif arg == 'package':
                                execute_package()
                        elif arg == 'lw_artifacts':
                                execute_lw_artifacts()

                        # Utilities
                        
                        elif arg == 'update_submodules':
                                execute_update_submodules()
                        elif arg == 'upload':
                                execute_upload()
                        
                        elif arg == 'git_init':
                                execute_git_init()
                        
                        elif arg == 'deps_deb':
                                execute_deps_deb()
                        elif arg == 'deps_rpm':
                                execute_deps_rpm()
                        elif arg == 'deps_pkg':
                                execute_deps_pkg()
                        
                        elif arg == 'rustup':
                                execute_rustup()
                        elif arg == 'mach_env':
                                execute_mach_env()
                        elif arg == 'reset':
                                execute_reset()
                        
                        else:
                                print("error: unknown command on command line: ", arg)
                                script_exit(1)
        else:
                # Print help message
                print(help_message)




#
# Large multiline strings
#



help_message = """# Use: 

     pybuild [<options>] clean | all | <targets> | <utilities>

# Options:

    -n,--no-execute            - print commands, don't execute them
    -l,--no-librewolf          - skip LibreWolf specific stages.
    -x,--cross                 - crosscompile from linux, implies -t win
    -s,--src <src>             - release,nightly,tor-browser
                                 (default=release)
    -t,--distro <distro>       - deb,rpm,win (default=win)
    -T,--token <private_token> - private token used to upload to gitlab.com

# Targets:

    all        - all steps from fetch to producing setup.exe
    clean      - clean everything, including extracted/fetched sources
    veryclean  - clean like above, and also remove build artifacts.

    fetch               - wget or hg clone or git pull
    extract             - when using wget, extract the archive.
    lw_do_patches       - [librewolf] patch the source
    build               - build the browser
    lw_post_build       - [librewolf] insert our settings
    package             - package the browser into zip/apk
    lw_artifacts        - [librewolf] build setup.exe

# Utilities:

    update_submodules   - git update submodules
    upload              - upload the build artifacts to gitlab.com

    git_init    - put the source folder in a .git repository
    reset       - use git/mercurial to revert changes to a clean state

    deps_deb    - install dependencies with apt
    deps_rpm    - install dependencies with dnf
    deps_pkg    - install dependencies on freebsd

    rustup      - update rust
    mach_env    - create mach environment
"""

#
# mozconfig files:
#

mozconfig_release = """
ac_add_options --enable-application=browser

# This supposedly speeds up compilation (We test through dogfooding anyway)
ac_add_options --disable-tests
ac_add_options --disable-debug

ac_add_options --enable-release
ac_add_options --enable-hardening
ac_add_options --enable-rust-simd
ac_add_options --enable-optimize


# Branding
ac_add_options --enable-update-channel=release
# theming bugs: ac_add_options --with-app-name=librewolf
# theming bugs: ac_add_options --with-app-basename=LibreWolf
ac_add_options --with-branding=browser/branding/librewolf
ac_add_options --with-distribution-id=io.gitlab.librewolf-community
ac_add_options --with-unsigned-addon-scopes=app,system
ac_add_options --allow-addon-sideload
#export MOZ_REQUIRE_SIGNING=0

# Features
ac_add_options --disable-crashreporter
ac_add_options --disable-updater

# Disables crash reporting, telemetry and other data gathering tools
mk_add_options MOZ_CRASHREPORTER=0
mk_add_options MOZ_DATA_REPORTING=0
mk_add_options MOZ_SERVICES_HEALTHREPORT=0
mk_add_options MOZ_TELEMETRY_REPORTING=0

# testing..
# MOZ_APP_NAME=librewolf
# This gives the same theming issue as --with-app-name=librewolf
"""





main()
script_exit(0)