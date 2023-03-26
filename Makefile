install::
	pip install -r requirements.txt
	rm -r -f /usr/share/ipnd/
	mkdir -p /usr/share/ipnd/
	cp -r -f -v src/* /usr/share/ipnd/
	ln -f -s /usr/share/ipnd/server.py /usr/bin/ipnd
	cp -f ipnd.service /etc/systemd/user/ipnd.service