# Figure Placement Audit

- Margin target: width <= 45.0 mm, typical height 60.0-80.0 mm.
- Result now: 15 of 42 figures fit marginalia as generated.
- Smallest current width: `fig:contactless-protocol-stack` at 31.2 mm.
- Widest current figure: `fig:decline-retry-tree` at 245.4 mm.
- Tallest current figure: `fig:disputes-lifecycle` at 169.4 mm.

## Summary

- `margin-ok`: 15
- `main-text`: 27
- `vertical-relayout-for-marginalia`: 0

## margin-ok

| id | bbox mm | target | reason |
|---|---:|---|---|
| `fig:interchange-flow` | 41.4 x 56.5 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:emv-chip-architecture` | 42.4 x 73.6 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:emv-cryptogram-decision` | 44.3 x 69.8 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:emv-dda-sequence` | 43.1 x 70.3 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:contactless-protocol-stack` | 31.2 x 63.8 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:token-detokenization-flow` | 31.2 x 84.9 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию; высота выше типовых 80 мм, но ещё приемлема для сложной схемы. |
| `fig:crypto-dukpt` | 35.0 x 75.2 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:crypto-hsm-flow` | 31.2 x 72.3 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:mc-ipm-structure` | 36.2 x 76.7 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:mir-unionpay-routing` | 33.0 x 64.8 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:sbp-architecture` | 37.0 x 78.3 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:fraud-hybrid` | 41.9 x 76.4 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:pisp-flow` | 31.2 x 77.0 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `fig:recon-exception-waterfall` | 42.3 x 68.4 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |
| `todo:ch26-payment-gateway:gateway-components` | 43.1 x 67.5 | `marginal-vertical` | Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты. |

## vertical-relayout-for-marginalia

| id | bbox mm | target | reason |
|---|---:|---|---|

## main-text

| id | bbox mm | target | reason |
|---|---:|---|---|
| `fig:four-party-model` | 131.8 x 52.8 | `main-wide` | Топология держится на одновременном сравнении пяти равноправных ролей; узкая маргиналия исказит горизонтальные связи. |
| `fig:three-party-model` | 131.8 x 56.8 | `main-wide` | Контраст с четырёхсторонней моделью важен именно как широкая peer-to-peer topology, а не как узкая колонка. |
| `fig:card-data-storage` | 162.0 x 47.4 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:tx-cancellation-timeline` | 166.6 x 41.5 | `main-wide` | временная ось теряет смысл при сжатии до узкой маргиналии; фазы и подписи нужно видеть одновременно. |
| `fig:tx-edge-cases` | 176.0 x 52.5 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:tx-lifecycle-timeline` | 159.6 x 40.8 | `main-wide` | временная ось теряет смысл при сжатии до узкой маргиналии; фазы и подписи нужно видеть одновременно. |
| `fig:contactless-kernel-comparison` | 196.0 x 34.4 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:contactless-provisioning` | 147.3 x 85.3 | `main-wide` | sequence diagram с несколькими участниками и подписями сообщений не читается в узком поле. |
| `fig:token-network-vs-psp` | 170.7 x 37.6 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:token-tsp-comparison` | 139.2 x 68.0 | `main-vertical` | Сравнение трёх TSP построено как параллельные колонки; без полной ширины теряется сама сравнительная идея. |
| `fig:crypto-key-hierarchy` | 184.2 x 88.3 | `main-vertical` | Несколько ветвей, примеры PAN и уровни ключей требуют ширины для одновременного сравнения. |
| `fig:3ds-three-domains` | 171.2 x 99.3 | `main-vertical` | Смысл схемы держится на параллельном сравнении трёх доменов, а не на одной вертикальной оси. |
| `fig:3ds-v1-vs-v2` | 180.2 x 100.6 | `main-wide` | sequence diagram с несколькими участниками и подписями сообщений не читается в узком поле. |
| `fig:pci-cde-boundary` | 143.7 x 125.8 | `main-wide` | параллельные подсистемы, зоны или уровни требуют одновременного обзора по ширине. |
| `fig:pci-saq-decision` | 239.9 x 146.4 | `main-vertical` | Это разветвлённое decision tree с длинными исходами SAQ; узкое поле здесь не сохранит читаемость. |
| `fig:pci-scope-reduction` | 172.2 x 41.1 | `main-wide` | временная ось теряет смысл при сжатии до узкой маргиналии; фазы и подписи нужно видеть одновременно. |
| `fig:visa-direct-flow` | 196.2 x 81.7 | `main-wide` | временная ось теряет смысл при сжатии до узкой маргиналии; фазы и подписи нужно видеть одновременно. |
| `fig:visanet-base-i-ii` | 180.2 x 62.2 | `main-wide` | Здесь критично сравнение двух плоскостей BASE I и BASE II; вертикализация ослабит архитектурный контраст. |
| `fig:banknet-topology` | 145.2 x 84.4 | `main-wide` | параллельные подсистемы, зоны или уровни требуют одновременного обзора по ширине. |
| `fig:opkc-flow` | 165.2 x 61.1 | `main-wide` | Три стадии с прямыми и обратными потоками лучше читаются как широкая фазовая схема. |
| `fig:sbp-scenarios` | 222.8 x 85.1 | `main-wide` | Гибрид матрицы и flow требует одновременного обзора строк, колонок и сценарного хвоста; поле для этого слишком узкое. |
| `fig:compliance-kyb-risk` | 172.0 x 38.3 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:subscriptions-cit-mit` | 198.9 x 127.0 | `main-vertical` | Дерево длинное, с несколькими типами MIT и пояснениями про 3DS/CVV/AVS/NTID; в поле потеряет читаемость. |
| `fig:disputes-lifecycle` | 206.5 x 169.4 | `main-wide` | sequence diagram с несколькими участниками и подписями сообщений не читается в узком поле. |
| `fig:decline-codes` | 200.2 x 44.0 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
| `fig:decline-retry-tree` | 245.4 x 151.9 | `main-vertical` | Важны точные code groups и retry-правила; для маргиналии слишком плотная логика и длинные листья. |
| `fig:alt-taxonomy-matrix` | 223.4 x 40.8 | `main-table` | таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста. |
