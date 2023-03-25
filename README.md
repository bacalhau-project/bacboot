# bacboot
A short, snappy and powerful installer for Bacalhau. Bacalhau Bootstrapper!

Want to run BacBoot and try it out? It's pretty simple! Just do the following;

```
git clone https://github.com/zorlin/bacboot.git && cd bacboot
python3 bacboot.py
```

Follow the prompts and have a go! It's currently capable of installing and upgrading the main Bacalhau binary (only on localhost), but a full roadmap is in the works and eventually BacBoot is intended to become the primary supported method of installing Bacalhau, alongside all the alternate methods that will be maintained alongside it.

Only Ubuntu 22.04 has been officially tested. Debian 11 should work, as should anything reasonably Debian-ish. RHEL/CentOS and RHEL-alike distros are not yet supported but support *is* planned for those.

You will need python3 installed and a working `apt` install - that's literally it.

Enjoy!
