.PHONY: encrypt_pypirc decrypt_pypirc pypi_register set_git_config bump_patch

encrypt_pypirc:
		-openssl enc -aes-256-cbc -salt -in ~/.pypirc -out .pypirc.secret -k $(SECRETS_PASS)

decrypt_pypirc:
		-openssl enc -aes-256-cbc -d -in .pypirc.secret -out $(HOME)/.pypirc -k $(SECRETS_PASS)

pypi_register:
		@rm -rf dist
		@make decrypt_pypirc
		@python ./setup.py register -r pypi
		@python ./setup.py sdist bdist_wheel bdist_egg
		@python ./setup.py sdist bdist_wheel bdist_egg upload -r pypi

set_git_config:
		git config --global push.default matching

config:
		rm -rf dotfiles
		if [ ! -f ~/.ssh ]; then \
    	echo "File not found!"; \
			make set_git_config; \
			git clone https://github.com/joliveros/dotfiles.git && cd ./dotfiles; \
			gpg --passphrase $(SECRETS_PASS) dotfiles.tar.gz.gpg ; \
			tar -xf dotfiles.tar.gz; \
			cp -r dotfiles/.ssh* ~/ ; \
			cp dotfiles/.gitconfig ~/ ; \
			chmod 400 ~/.ssh/id_rsa ; \
		fi

bump_patch:
		if [ $(shell git rev-parse --abbrev-ref HEAD) = master ]; then \
			if test $(findstring build:,$(shell git log -1 --pretty=%B)); then \
				echo "last commit was result of a build."; else \
				make config; \
				python -c "from bump_version import bump_patch; bump_patch()"; \
				git add . && git commit -m "build: bump patch due to build."; \
				git tag $$(eval cat .version) -m "build: bump patch due to build."; \
				ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts; \
				git push origin; \
				make pypi_register; \
			fi; \
		fi
