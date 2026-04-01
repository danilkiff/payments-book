# Сколько раз latexmk повторяет компиляцию, пока все ссылки не разрешатся
$max_repeat = 8;

# Собирать PDF через pdflatex
$pdf_mode = 1;

# Артефакты сборки — в отдельный каталог
$out_dir = 'build';

# Тихий режим: только ошибки, без прогресса компиляции
$silent = 1;

# Флаги компилятора: ошибки с номерами строк, остановка на первой ошибке, без интерактива
$pdflatex = 'pdflatex -file-line-error -halt-on-error -interaction=nonstopmode %O %S';
