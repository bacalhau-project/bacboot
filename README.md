# bacboot (EXPERIMENTAL!)
A short, snappy and powerful installer for Bacalhau. Bacalhau Bootstrapper!

In a hurry and just want to install Bacalhau on your machine?

⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢

**This is not yet production ready. 
Follow the official Bacalhau documentation if you just want to install Bacalhau. Otherwise, read on!**

⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢⚠️☢

`curl -sL https://raw.githubusercontent.com/Zorlin/bacboot/main/bacboot.py | python3 - --install --silent --ask-become-pass` 

(or the same without `--ask-become-pass` if you have passwordless sudo or will be deploying as root)

## Quick start
Want to run BacBoot and try it out? It's pretty simple! Just do the following:
```
curl -sL https://raw.githubusercontent.com/Zorlin/bacboot/main/bacboot.py -o bacboot.py && chmod +x bacboot.py && python3 bacboot.py
```
From then on, you can re-run bacboot by simple running `./bacboot.py` or `python3 bacboot.py` in the folder you downloaded it in.

Follow the prompts and have a go! It's currently capable of installing and upgrading the main Bacalhau binary (only on localhost), but a full roadmap is in the works and eventually BacBoot is intended to become the primary supported method of installing Bacalhau, alongside all the alternate methods that will be maintained alongside it.

**Only Ubuntu 22.04 has been officially tested.** Debian 11 should work, as should anything reasonably Debian-ish. RHEL/CentOS and RHEL-alike distros are not yet supported but support *is* planned for those.

You will need python3 installed and a working `apt` install - that's literally it. BacBoot will take care of installing Ansible including setting up pip3 if needed, and (soon) can even clean up afterwards and remove Ansible from the BacBoot host afterwards if needed.

## Unattended, silent and truly silent modes
You can run with one of --unattended, --silent or --truly-silent to trigger special modes.

They do the following, respectively:
* Unattended: Runs with sane choices and does not prompt you unless it must. Still outputs most messages. Will prompt the user if a become/sudo password is needed.
* Silent: Same as Unattended, except it suppresses everything except for warnings and errors. Implies --unattended.
* Truly Silent: Same as Silent, except it suppresses warnings too. Implies --silent.

When running with any of these three modes, you **must** choose an action to do, or else you will see an error.

In unattended mode, we will assume you do not need to use a sudo/become password unless you explicitly call --ask-become-pass.

## Actions
You can skip the initial menu and jump straight to a particular action - combine this with the unattended/silent modes to run entirely automatically.

The following actions are available:
* --install [components] - Installs or upgrades Bacalhau. Optionally, you can specify what components you want to install. If you don't specify --method, will install using Ansible.
* --upgrade [components] - An alias for --install, as the install step is also an upgrade playbook too. Magic!
* --verify [components ] - Specifically verify Bacalhau components. Optionally, you can specify which components you want to test. If you do not, BacBoot will ask you what to verify unless you are running in unattended mode (in which case, it will verify the client by default.

## Other options
* --method - Choose an installation method - you can choose from "docker", "ansible", "cloud" and "direct". Ansible is used by default if left unset.
* --skip-verification - Do not automatically run the verification step after installing or upgrading Bacalhau.

Enjoy!

## Credits
BacBoot was initially created in 2023 by Benjamin Arntzen and the Application Research Group, and donated to the Bacalhau Project.

It is free software licenced under the MIT Licence.
