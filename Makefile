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

bump_patch:
		@python -c "from bump_version import bump_patch; bump_patch()"
		@make set_git_config
		@git add . && git commit -m "bump patch due to build."
		@git tag $$(eval cat .version) -m "bump patch due to build."
		@ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
		@git push origin
