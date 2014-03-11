#! /bin/zsh

set -x

unset options

cd "$0"(:h) &&
. ./PKGBUILD &&
pkgver="$(git describe --tags --match='[0-9]*' | sed -n '/^[0-9][.0-9a-z-]\+$/{s/-/./g;p;Q0};Q1')" &&
src="src/$pkgname-$pkgver" &&
rm -rf src pkg &&
mkdir -p "$src" &&
sed "s/^pkgver=.*\$/pkgver=$pkgver/" ./PKGBUILD >src/PKGBUILD &&
(cd "$OLDPWD" && git ls-files -z | xargs -0 cp --parents --target-directory="$OLDPWD/$src") &&
export PACKAGER="`git config user.name` <`git config user.email`>" &&
makepkg --noextract --force -p src/PKGBUILD &&
rm -rf src pkg &&
sudo pacman -U --noconfirm "$pkgname-$pkgver-$pkgrel-any.pkg.tar.xz"

