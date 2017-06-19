# use the rest as arguments for "run"
RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
# ...and turn them into do-nothing targets
$(eval $(RUN_ARGS):;@:)

.PHONY: encrypt_pypirc decrypt_pypirc pypi_register set_git_config bump_patch

encrypt_pypirc:
		openssl enc -aes-256-cbc -salt -in ~/.pypirc -out .pypirc.secret -k $(RUN_ARGS)

decrypt_pypirc:
		openssl enc -aes-256-cbc -d -in .pypirc.secret -out $(HOME)/.pypirc -k $(RUN_ARGS)

pypi_register:
		make decrypt_pypirc $(SECRETS_PASS) && \
		python ./setup.py register -r pypi && \
		python ./setup.py sdist upload -r pypi

set_git_config:
		git config user.email "jose.oliveros.1983@gmail.com" && \
		git config user.name "José Oliveros"
		git config --global push.default matching

config:
		rm -rf dotfiles
		if [ ! -f ~/.ssh ]; then \
    	echo "File not found!"; \
			make set_git_config; \
			git clone https://github.com/joliveros/dotfiles.git && cd ./dotfiles; \
			gpg --passphrase $(SECRETS_PASS) dotfiles.tar.gz.gpg ; \
			tar -xf dotfiles.tar.gz; \
			cp -r dotfiles/ ~/ ; \
		fi

bump_patch:
		@make config
		@python -c "from bump_version import bump_patch; bump_patch()"
		@git add . && git commit -m "bump patch due to build."
		@git tag $$(eval cat .version) -m "bump patch due to build."
		@ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
		@git push origin
