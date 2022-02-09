.PHONY : help all clean veryclean fetch build artifacts check

help :
	@echo "Use: make [all] [clean] [veryclean] [check] ..."
	@echo ""
	@echo "  all       - Build librewolf and it's windows artifacts."
	@echo "  clean     - Remove output files and temporary files."
	@echo "  veryclean - Like 'clean', but also remove all downloaded files."
	@echo "  check     - Check if there is a new version of Firefox."
	@echo ""
	@echo "  fetch     - Fetch the latest librewolf source."
	@echo "  build     - Perform './mach build && ./mach package' on it."
	@echo "  debug     - Perform a debug build with different 'mozconfig'."
	@echo "  artifacts - Create the setup.exe and the portable.zip."
	@echo ""
	@echo "Note: to upload, after artifacts, into the windows repo, use:"
	@echo ""
	@echo " python3 mk.py upload <token>"
	@echo ""

all : fetch build artifacts

clean :
	rm -rf work

veryclean : clean
	rm -f librewolf-$(shell cat version)*.en-US.win64* sha256sums.txt upload.txt firefox-$(shell cat version)*.en-US.win64.zip
	rm -rf librewolf-$(shell cat version)-$(shell cat source_release)
	rm -f librewolf-$(shell cat version)-*.source.tar.gz

fetch :
	python3 mk.py fetch

build :
	python3 mk.py build

debug :
	python3 mk.py build-debug

artifacts :
	python3 mk.py artifacts

check : README.md
	@python3 assets/update-version.py
	@wget -q -O source_release https://gitlab.com/librewolf-community/browser/source/-/raw/main/release
	@echo ""
	@echo "Current release:" $$(cat ./release)


