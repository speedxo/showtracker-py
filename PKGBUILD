# Maintainer: ShowTracker <nobody@example.com>
pkgname=showtracker
pkgver=0.1.0
pkgrel=1.1
pkgdesc="CLI to track TV shows (season/episode) and books (chapter)"
arch=('any')
url="https://github.com/speedxo/showtracker-py"
license=('MIT')
depend=('python')
makedepends=('python')
source=("showtracker.py" "README.md")
sha256sums=('SKIP' 'SKIP')

build() {
    # nothing to build; script is pure python
    return 0
}

package() {
    install -Dm755 "${srcdir}/showtracker.py" "${pkgdir}/usr/bin/showtracker"
    install -Dm644 "${srcdir}/README.md" "${pkgdir}/usr/share/doc/${pkgname}/README.md"
}
