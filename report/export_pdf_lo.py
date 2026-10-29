"""Update TOC/fields and export a generated report using LibreOffice's UNO API.

Run with LibreOffice's bundled Python (which provides `uno`).
Arguments: DOCX --soffice SOFFICE.COM --profile WRITABLE_PROFILE_DIRECTORY
This runs a private headless process, updates cached fields, and saves DOCX/PDF.
Content changes belong in make_final_report.py, not in this export step.
API: https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1text_1_1XDocumentIndex.html
"""
from pathlib import Path
import argparse, os, socket, subprocess, time
import uno


def prop(name, value):
    p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    p.Name, p.Value = name, value
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx', type=Path)
    ap.add_argument('--soffice', type=Path, required=True)
    ap.add_argument('--profile', type=Path, required=True)
    a = ap.parse_args()
    source = a.docx.resolve()
    a.profile.mkdir(parents=True, exist_ok=True)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    connection = 'socket,host=127.0.0.1,port=' + str(port)
    tmp = a.profile.resolve() / 'tmp'
    tmp.mkdir(exist_ok=True)
    child_env = os.environ.copy()
    child_env['TEMP'] = child_env['TMP'] = str(tmp)
    log = (a.profile / 'export-service.log').open('wb')
    proc = subprocess.Popen([
        str(a.soffice.resolve()), '-env:UserInstallation=' + a.profile.resolve().as_uri(),
        '--headless', '--invisible', '--nologo', '--nodefault', '--norestore',
        '--accept=' + connection + ';urp;StarOffice.ComponentContext',
    ], stdout=log, stderr=subprocess.STDOUT, env=child_env,
       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    doc = desktop = None
    try:
        ctx = uno.getComponentContext()
        resolver = ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', ctx)
        end = time.monotonic() + 60
        while True:
            try:
                remote = resolver.resolve('uno:' + connection + ';urp;StarOffice.ComponentContext')
                break
            except Exception:
                if proc.poll() is not None:
                    raise RuntimeError('LibreOffice exited: ' + str(proc.returncode))
                if time.monotonic() >= end:
                    raise RuntimeError('Private LibreOffice service did not start within 60 seconds')
                time.sleep(0.25)
        desktop = remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', remote)
        print('Connected to private LibreOffice process', flush=True)
        doc = desktop.loadComponentFromURL(source.as_uri(), '_blank', 0,
            (prop('Hidden', True), prop('ReadOnly', False), prop('UpdateDocMode', 3), prop('MacroExecutionMode', 0)))
        if doc is None:
            raise RuntimeError('Could not load DOCX')
        indexes = doc.getDocumentIndexes()
        if indexes.getCount() != 1:
            raise RuntimeError('Expected exactly one report table of contents')
        for _ in range(2):
            doc.refresh()
            doc.getTextFields().refresh()
            for i in range(indexes.getCount()):
                indexes.getByIndex(i).update()
        # Save to a separate DOCX first; replace the input only after a successful export.
        updated = source.with_name(source.stem + '_fields.docx')
        doc.storeToURL(updated.as_uri(), (prop('FilterName', 'Office Open XML Text'), prop('Overwrite', True)))
        pdf = source.with_suffix('.pdf')
        doc.storeToURL(pdf.as_uri(), (prop('FilterName', 'writer_pdf_Export'), prop('Overwrite', True)))
        doc.close(True)
        doc = None
        updated.replace(source)
        print('Updated TOC/fields and exported:', source, pdf, flush=True)
    finally:
        if doc is not None:
            doc.close(True)
        if desktop is not None:
            desktop.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
        log.close()


if __name__ == '__main__':
    main()
