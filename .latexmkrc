# Сколько раз latexmk повторяет компиляцию, пока все ссылки не разрешатся
$max_repeat = 8;

# Собирать PDF через pdflatex
$pdf_mode = 1;

# Артефакты сборки — в отдельный каталог
$out_dir = 'build';

# Тихий режим: только ошибки, без прогресса компиляции
$silent = 1;

# Флаги компилятора: ошибки с номерами строк, остановка на первой ошибке, без интерактива.
# max_print_line=10000 — не ломать длинные пути и Overfull-дампы по 79 символов
# (иначе атрибуция файла в log-summary.sh ловит обрывок предыдущего пути).
$ENV{'max_print_line'} = 10000;
$pdflatex = 'pdflatex -file-line-error -halt-on-error -interaction=nonstopmode %O %S';

# Запускать biber для обработки библиографии (biblatex)
$bibtex_use = 2;
