#!/usr/bin/env python3

import os,sys,subprocess

# native()/bash()/exec() utility functions
def native(cmd):
    sys.stdout.flush()
    print(cmd)
    sys.stdout.flush()
   
    retval = os.system(cmd)
    if retval != 0:
        sys.exit(retval)

_no_exit = False
def bash(cmd):
    tmp = []
    tmp += ['c:/mozilla-build/msys/bin/bash.exe', '-c', cmd]
    sys.stdout.flush()
    print(cmd)
    sys.stdout.flush()
    
    retval = subprocess.run(tmp).returncode
    if _no_exit:
        return
    if retval != 0:
        sys.exit(retval)

_native = False
_no_exit = False
def exec(cmd):
    if _native:
        return native(cmd)
    return bash(cmd)

def patch(patchfile):
    cmd = "patch -p1 -i {}".format(patchfile)
    sys.stdout.flush()
    print("\n*** -> {}".format(cmd))
    sys.stdout.flush()
    
    retval = os.system(cmd)
    if retval != 0:
        sys.stdout.flush()
        print("fatal error: patch '{}' failed".format(patchfile))
        sys.stdout.flush()
        sys.exit(retval)



#
# main functions
#


def fetch():
    print('mk.py: fetch(): Disabled due to "artifacts" now has priority.')
    sys.exit(1)
    
    exec('wget -q -O version https://gitlab.com/librewolf-community/browser/source/-/raw/main/version')
    exec('wget -q -O source_release https://gitlab.com/librewolf-community/browser/source/-/raw/main/release')
    exec('wget -O librewolf-$(cat version)-$(cat source_release).source.tar.gz https://gitlab.com/librewolf-community/browser/source/-/jobs/artifacts/main/raw/librewolf-$(cat version)-$(cat source_release).source.tar.gz?job=build-job')

def build():
    print('mk.py: build(): Disabled due to "artifacts" now has priority.')
    sys.exit(1)
    
    exec('rm -rf librewolf-$(cat version)')
    exec('tar xf librewolf-$(cat version)-$(cat source_release).source.tar.gz')
    
    with open('version','r') as file:
        version = file.read().rstrip()
        os.chdir('librewolf-{}'.format(version))

        # patches
        exec('cp -v ../assets/mozconfig.windows mozconfig')
        patch('../assets/package-manifest.patch')
        
        exec('MACH_USE_SYSTEM_PYTHON=1 ./mach build')
        _no_exit = True
        exec('MACH_USE_SYSTEM_PYTHON=1 ./mach package')
        _no_exit = False
        exec('cp -v obj-x86_64-pc-mingw32/dist/firefox-{}.en-US.win64.zip ..'.format(version))
        os.chdir('..')



def artifacts():
    
    with open('version','r') as file1:
        version = file1.read().rstrip()
        buildzip_filename = 'firefox-{}.en-US.win64.zip'.format(version)
        exec('cp -v librewolf-{}/obj-x86_64-pc-mingw32/dist/{} .'.format(version,buildzip_filename))
        exec('rm -rf work && mkdir work')
        os.chdir('work')
        exec('unzip ../{}'.format(buildzip_filename))
        exec('mv firefox librewolf')
        os.chdir('librewolf')
        exec('mv firefox.exe librewolf.exe')
        os.chdir('..')
        os.chdir('..')

        # let's get 'release'.
        with open('release','r') as file2:
            release = file2.read().rstrip()
            full_version = '{}.{}'.format(version,release)

            # let's copy in the .ico icon.
            exec('cp -v assets/librewolf.ico work/librewolf')

            # Let's make the portable zip first.
            os.chdir('work')
            exec('rm -rf librewolf-{}'.format(version))
            os.makedirs('librewolf-{}/Profiles/Default'.format(version), exist_ok=True)
            os.makedirs('librewolf-{}/LibreWolf'.format(version), exist_ok=True)
            exec('cp -vr librewolf/* librewolf-{}/LibreWolf'.format(version))
            exec('wget -q -O librewolf-{}/librewolf-portable.exe https://gitlab.com/librewolf-community/browser/windows/uploads/8347381f01806245121adcca11b7f35c/librewolf-portable.exe'.format(version))
            zipname = 'librewolf-{}.en-US.win64.zip'.format(full_version)
            exec("rm -f ../{}".format(zipname))
            exec("zip -qr9 ../{} librewolf-{}".format(zipname,version))            
            os.chdir('..')

            # With that out of the way, we need to create the nsis setup.
            os.chdir('work')
            setupname = 'librewolf-{}.en-US.win64-setup.exe'.format(full_version)
            exec('sed \"s/pkg_version/{}/g\" < ../assets/setup.nsi > tmp.nsi'.format(full_version))
            exec('makensis-3.01.exe -V1 tmp.nsi')
            exec('rm -f tmp.nsi')
            exec("mv {} ..".format(setupname))
            os.chdir('..')




def do_upload(filename,token):
    exec('echo _ >> upload.txt')
    exec('curl --request POST --header \"PRIVATE-TOKEN: {}\" --form \"file=@{}\" \"https://gitlab.com/api/v4/projects/13852981/uploads\" >> upload.txt'.format(token,filename))
    exec('echo _ >> upload.txt')

def upload(token):

    with open('version','r') as file1:
        version = file1.read().rstrip()
        with open('release','r') as file2:
            release = file2.read().rstrip()
            full_version = '{}.{}'.format(version,release)

            # Files we need to upload..
            zip_filename = 'librewolf-{}.en-US.win64.zip'.format(full_version)
            setup_filename = 'librewolf-{}.en-US.win64-setup.exe'.format(full_version)
            exec('md5sum {} {} > md5sums.txt'.format(setup_filename,zip_filename))
            exec('rm -f upload.txt')
            do_upload(setup_filename,token)
            do_upload(zip_filename,token)
            do_upload('md5sums.txt',token)
    
#
# parse commandline for commands
#

help_msg = '''
Use: ./mk.py <command> ...

commands:
  fetch
  build
  artifacts
  upload <token>

'''

done_something = False

in_upload=False
for arg in sys.argv:
    if in_upload:
        upload(arg)
        done_something=True
    elif arg == 'fetch':
        fetch()
        done_something = True
    elif arg == 'build':
        build()
        done_something = True
    elif arg == 'artifacts':
        artifacts()
        done_something = True
    elif arg == 'upload':
        in_upload = True
    else:
        if arg == sys.argv[0]:
            pass
        else:
            print(help_msg)
            sys.exit(1)


        
if done_something:
    sys.exit(0)
    
print(help_msg)
sys.exit(1)
