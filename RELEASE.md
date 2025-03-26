## Release

In order to release a new version of the library, you will need to do the following:

- Merge all change you want to see in the new version
- Check the latest version and increment it according to [PEP440](https://peps.python.org/pep-0440/). For example,
  -  If the latest version was `v0.0.1`, the next one may be `v0.0.2` or `v0.0.2.dev1` (if you want a dev release for pre-release checks).
  - If the latest version was `v0.0.1dev1`, the next one may be `v0.0.1` or `v0.0.1.dev1` (if you want a dev release for pre-release checks).
- Create a new tag with the corresponding next version like:

```bash
git tag v0.0.2.dev1
git push --tags
```

The release automation will take care of the rest. 
It reacts to any tag that starts from `v.*` on any branch which allows to test release process without merging changes.