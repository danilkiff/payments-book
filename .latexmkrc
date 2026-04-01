# .latexmkrc — конфигурация latexmk для XeLaTeX + biber

# Используем XeLaTeX (для fontspec, polyglossia и русского языка)
$pdf_mode = 5;               # xelatex → PDF
$postscript_mode = 0;
$dvi_mode = 0;

$xelatex = 'xelatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
$bibtex_use = 2;             # biber вместо bibtex
$biber = 'biber %O %S';

# Папка для артефактов сборки
$out_dir = '../build';
$aux_dir = '../build/aux';

# Файл для компиляции
@default_files = ('src/main.tex');

# Дополнительные расширения для очистки
$clean_ext = 'synctex.gz synctex.gz(busy) bbl bcf fdb_latexmk fls run.xml';
