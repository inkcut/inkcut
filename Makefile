MAINTAINER="frmdstryr <frmdstryr@gmail.com>"
DISTRO="xenial"
PPA="ppa:inkcut/ppa"

clean:
	rm -Rf deb_dist
	rm -Rf packages

pkg:
	mkdir -p packages

atom: pkg
	cd packages; \
	    pypi-download atom; \
	    tar xzf atom-*.gz; \
	    cd atom-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO) \
                         --depends="python-future"\
                         --depends3="python3-future";\
	    cd deb_dist/atom-*;\
	    debuild -S -sa

kiwisolver: pkg
	cd packages; \
	    pypi-download kiwisolver; \
	    tar xzf kiwisolver-*.gz; \
	    cd kiwisolver-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO); \
	    cd deb_dist/kiwisolver-*; \
	    debuild -S -sa

qtpy: pkg
	cd packages; \
	    pypi-download qtpy; \
	    tar xzf QtPy-*.gz; \
	    cd QtPy-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO); \
	    cd deb_dist/qtpy-*; \
	    debuild -S -sa

enaml: pkg
	cd packages; \
	    pypi-download enaml; \
	    tar xzf enaml-*.gz; \
	    cd enaml-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO) \
                         --depends="python-atom, python-ply, python-qtpy, python-kiwisolver, python-future"\
                         --depends3="python3-atom, python3-ply, python3-qtpy, python3-kiwisolver, python3-future"; \
	    cd deb_dist/enaml-*; \
	    debuild -S -sa

enamlx: pkg
	cd packages; \
	    pypi-download enamlx; \
	    tar xzf enamlx-*.gz; \
	    cd enamlx-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO) \
                         --depends="python-enaml"\
                         --depends3="python3-enaml"; \
	    cd deb_dist/enamlx-*; \
	    debuild -S -sa

qt5reactor: pkg
	cd packages; \
	    pypi-download qt5reactor; \
	    tar xzf qt5reactor-*.gz; \
	    cd qt5reactor-*; \
	    python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True \
                         --with-python3=True --maintainer=$(MAINTAINER) --suite=$(DISTRO) \
                         --depends="python-twisted, python-pyqt5"\
                         --depends3="python3-twisted, python3-pyqt5"; \
	    cd deb_dist/enamlx-*; \
	    debuild -S -sa

inkcut: pkg
	python3 setup.py --command-packages=stdeb.command sdist_dsc \
	 --package=inkcut\
	 --with-python2=True \
	 --with-python3=False \
	 --section=graphics \
	 --mime-desktop-files="inkcut/res/inkcut.desktop"\
	 --maintainer=$(MAINTAINER) \
	 --suite=$(DISTRO)\
	 --depends="python-enaml, python-twisted, ipython-qtconsole, python-pyqtgraph, \
	            python-faulthandler, python-lxml, python-jsonpickle, python-enamlx,\
	            python-qt4reactor, python-serial"\
	 --upstream-version-suffix a7
	cd deb_dist/inkcut-* && debuild -S -sa

upload: pkg
	#find . -name "*_source.changes" -exec dput ppa:inkcut/ppa {} \;
	dput ppa:inkcut/ppa deb_dist/*_source.changes
