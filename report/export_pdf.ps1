param(
    [string]$DocxPath = (Join-Path $PSScriptRoot '결과보고서_PPA.docx'),
    [string]$PdfPath = (Join-Path $PSScriptRoot '결과보고서_PPA.pdf')
)

# Microsoft Word desktop is required. Only refresh generated fields and export;
# content/layout edits belong in make_final_report.py.
$ErrorActionPreference = 'Stop'
$resolvedDocx = (Resolve-Path -LiteralPath $DocxPath).Path
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$reportWord = $null
$reportDocument = $null
try {
    $reportWord = New-Object -ComObject Word.Application
    $reportWord.Visible = $false
    $reportWord.DisplayAlerts = 0
    $reportDocument = $reportWord.Documents.Open($resolvedDocx, $false, $false)
    [void]$reportDocument.Fields.Update()
    foreach ($reportToc in $reportDocument.TablesOfContents) {
        $reportToc.Update()
    }
    $reportDocument.Repaginate()
    foreach ($reportToc in $reportDocument.TablesOfContents) {
        $reportToc.UpdatePageNumbers()
    }
    foreach ($reportSection in $reportDocument.Sections) {
        foreach ($reportFooter in $reportSection.Footers) {
            [void]$reportFooter.Range.Fields.Update()
        }
    }
    $reportDocument.Save()
    $reportDocument.ExportAsFixedFormat($resolvedPdf, 17)
    Write-Output ('Word {0}; pages={1}; PDF={2}' -f $reportWord.Version, $reportDocument.ComputeStatistics(2), $resolvedPdf)
}
finally {
    if ($null -ne $reportDocument) { $reportDocument.Close(0) }
    if ($null -ne $reportWord) { $reportWord.Quit() }
}
