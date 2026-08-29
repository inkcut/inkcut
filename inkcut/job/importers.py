# -*- coding: utf-8 -*-
"""
Copyright (c) 2026, The Inkcut authors.

Distributed under the terms of the GPL v3 License.

Import support for non-SVG vector documents (PDF and Adobe Illustrator).

Inkcut's document parser only understands SVG, so other vector formats
are converted to a temporary SVG first using an external converter
(poppler's pdftocairo, or Inkscape as a fallback). Modern .ai files are
PDF-compatible — Illustrator embeds a full PDF unless "Create PDF
Compatible File" was disabled — so they go through the same pipeline.

"""
import os
import hashlib
import shutil
import subprocess
import sys
import tempfile

from inkcut.core.api import log

#: Cache directory for converted documents. Content-hashed filenames let
#: repeated opens of the same file reuse the previous conversion.
CACHE_DIR = os.path.expanduser('~/.config/inkcut/imports')

#: GUI apps launched from Finder/Dock on macOS do not inherit the shell
#: PATH, so Homebrew and MacPorts locations must be searched explicitly.
#: Harmless elsewhere: these are only tried after shutil.which() fails.
EXTRA_PATHS = ('/opt/homebrew/bin', '/usr/local/bin', '/opt/local/bin')

#: Per-platform hint for installing poppler, used only in the error
#: raised when neither converter is present.
POPPLER_HINTS = {
    'darwin': 'brew install poppler',
    'linux': 'apt install poppler-utils (or dnf install poppler-utils)',
    'win32': 'install poppler and add its bin directory to PATH',
}

IMPORTABLE_EXTENSIONS = ('.pdf', '.ai')


def _find_tool(name):
    """ Find an executable, also searching common install locations that
    are missing from a GUI app's environment PATH.

    """
    path = shutil.which(name)
    if path:
        return path
    for prefix in EXTRA_PATHS:
        candidate = os.path.join(prefix, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def is_importable(path):
    """ Whether the path is a non-SVG document this module can convert.

    """
    return path.lower().endswith(IMPORTABLE_EXTENSIONS)


def _check_ai_compatible(path):
    """ Verify an .ai file contains an embedded PDF. Illustrator files
    saved without PDF compatibility are plain PostScript, which none of
    the SVG converters can read.

    """
    with open(path, 'rb') as f:
        head = f.read(2048)
    if b'%PDF' in head:
        return
    from .models import JobError
    raise JobError(
        "Cannot import %s: this .ai file was saved without PDF "
        "compatibility — re-save it in Illustrator with 'Create PDF "
        "Compatible File' enabled." % os.path.basename(path))


def _page_count(path):
    """ Number of pages via poppler's pdfinfo. Returns None when the
    count cannot be determined (pdfinfo missing or failing) — the caller
    then skips the multi-page warning instead of blocking the import.

    """
    pdfinfo = _find_tool('pdfinfo')
    if not pdfinfo:
        return None
    try:
        result = subprocess.run(
            [pdfinfo, path], capture_output=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.decode('utf-8', 'replace').splitlines():
        if line.startswith('Pages:'):
            try:
                return int(line.split(':', 1)[1].strip())
            except ValueError:
                return None
    return None


def _cache_path(path):
    """ Deterministic cache location derived from the source name and
    content hash, so edits to the source produce a fresh conversion while
    unchanged files reuse the cached SVG.

    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    base = os.path.splitext(os.path.basename(path))[0]
    return os.path.join(CACHE_DIR, '%s-%s.svg' % (base, h.hexdigest()[:16]))


def convert_to_svg(path):
    """ Convert a PDF or PDF-compatible .ai document to SVG and return
    the path of the converted file. Results are cached in CACHE_DIR.

    Raises JobError with an actionable message when the file cannot be
    converted or no converter is installed.

    """
    return convert_to_svg_info(path)[0]


def convert_to_svg_info(path):
    """ Like convert_to_svg but also returns the source page count, so a
    GUI caller can warn the user about dropped pages without running
    pdfinfo a second time. Returns (svg_path, pages) where pages is None
    when the count could not be determined.

    """
    from .models import JobError

    if not os.path.exists(path):
        raise JobError("Cannot import %s, it does not exist!" % path)

    if path.lower().endswith('.ai'):
        _check_ai_compatible(path)

    #: Only the first page can become one cut job; warn (on every open,
    #: not just cache misses) rather than silently dropping pages.
    pages = _page_count(path)
    if pages and pages > 1:
        log.warning(
            "import | %s has %d pages; only page 1 is imported"
            % (os.path.basename(path), pages))

    out = _cache_path(path)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        log.debug("import | using cached conversion %s" % out)
        return out, pages

    os.makedirs(CACHE_DIR, exist_ok=True)

    pdftocairo = _find_tool('pdftocairo')
    inkscape = _find_tool('inkscape')
    if not pdftocairo and not inkscape:
        hint = POPPLER_HINTS.get(sys.platform, POPPLER_HINTS['linux'])
        raise JobError(
            "Importing PDF/AI files requires poppler or Inkscape. "
            "Install poppler with: %s" % hint)

    #: Unique temp file in the cache dir: a fixed name would race
    #: between concurrent Inkcut processes converting the same document
    fd, tmp = tempfile.mkstemp(
        prefix=os.path.basename(out) + '.', suffix='.tmp', dir=CACHE_DIR)
    os.close(fd)
    if pdftocairo:
        cmd = [pdftocairo, '-svg', '-f', '1', '-l', '1', path, tmp]
    else:
        cmd = [inkscape, path, '--export-type=svg',
               '--export-plain-svg', '--export-filename=%s' % tmp]

    log.info("import | converting %s with %s" % (path, cmd[0]))
    try:
        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise JobError("Importing %s timed out" % path)
        if result.returncode != 0 or not os.path.exists(tmp) \
                or os.path.getsize(tmp) == 0:
            stderr = result.stderr.decode('utf-8', 'replace').strip()
            log.error("import | conversion failed: %s" % stderr)
            raise JobError(
                "Could not convert %s to SVG: %s"
                % (os.path.basename(path), stderr or "converter error"))
        os.replace(tmp, out)
    finally:
        #: Gone already when os.replace succeeded
        try:
            os.unlink(tmp)
        except OSError:
            pass
    log.info("import | converted to %s" % out)
    return out, pages
