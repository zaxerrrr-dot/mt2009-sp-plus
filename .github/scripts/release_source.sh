#!/bin/sh
# release_source.sh VERSION_FILE VERSION ZIP_NAME OUT_DIR
#
# The commit a release of VERSION belongs to, printed on stdout, and its
# update zip copied to OUT_DIR/ZIP_NAME when that commit has one in releases/.
# The current version is the checked-out commit ($GITHUB_SHA); an older one,
# run by hand afterwards, is the newest commit whose VERSION_FILE says it -
# the release commit - so its tag, its Source code archives and its zip are
# that version's and not whatever main holds now (releases/ keeps only the
# newest zips).
set -eu
file=$1; v=$2; zip=$3; out=$4
target=${GITHUB_SHA:-$(git rev-parse HEAD)}
if [ "$(tr -d ' \r\n' < "$file")" != "$v" ]; then
  target=
  for c in $(git log --format=%H -- "$file"); do
    if [ "$(git show "$c:$file" 2>/dev/null | tr -d ' \r\n')" = "$v" ]; then target=$c; break; fi
  done
  [ -n "$target" ] || { echo "no commit has $file = $v" >&2; exit 1; }
fi
# The zip as it was last published: for an older version the newest commit
# that still has it (a merge that rebuilt the package after the release
# commit carries the one the manifest pointed at), for the current one the
# checked-out commit.
mkdir -p "$out"
src=$target
if [ "$target" != "${GITHUB_SHA:-$(git rev-parse HEAD)}" ]; then
  for c in $(git log --format=%H -- "releases/$zip"); do
    if git cat-file -e "$c:releases/$zip" 2>/dev/null; then src=$c; break; fi
  done
fi
if git cat-file -e "$src:releases/$zip" 2>/dev/null; then
  git show "$src:releases/$zip" > "$out/$zip"
else
  echo "::warning::releases/$zip not found; release without the zip" >&2
fi
echo "$target"
