# .latexmkrc — конфигурация latexmk для XeLaTeX + biber

use Cwd ();

# На macOS TeX Live обычно живёт здесь; добавляем путь явно, чтобы
# сборка работала и из GUI/CI-окружений с урезанным PATH.
my $texbin = '/Library/TeX/texbin';
$ENV{'PATH'} = "$texbin:$ENV{'PATH'}" if -d $texbin;

# Используем XeLaTeX (для fontspec, polyglossia и русского языка)
$pdf_mode = 5;               # xelatex → PDF
$postscript_mode = 0;
$dvi_mode = 0;

$xelatex = 'TEXINPUTS=./src/:./src/texmf//:$TEXINPUTS xelatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
$bibtex_use = 2;             # biber вместо bibtex
$biber = 'biber %O %S';

# Папка для артефактов сборки (относительно корня проекта, где запускается latexmk)
$out_dir = 'build';
$aux_dir = 'build/aux';

# Файл для компиляции
@default_files = ('src/main.tex');

# glossaries не поддерживается latexmk "из коробки". Для основной
# глоссарийной базы запускаем xindy напрямую: так сборка стабильнее в
# mixed Russian/English документе, чем через makeglossaries.
add_cus_dep('glo', 'gls', 0, 'makeglossaries');

sub makeglossaries {
  my ($base_name, $path) = fileparse($_[0]);
  my $cwd = Cwd::getcwd();
  chdir $path or return 1;
  my $status = system 'xindy',
    '-L', 'english',
    '-C', 'utf8',
    '-I', 'xindy',
    '-M', $base_name,
    '-t', "$base_name.glg",
    '-o', "$base_name.gls",
    "$base_name.glo";
  chdir $cwd;
  return $status;
}

# Дополнительные расширения для очистки
$clean_ext = 'synctex.gz synctex.gz(busy) bbl bcf fdb_latexmk fls run.xml acr acn alg glo gls glg xdy';
