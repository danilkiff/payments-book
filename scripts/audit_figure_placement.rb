#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "shellwords"
require "pathname"

ROOT = Pathname.new(__dir__).join("..").expand_path
MANIFEST_PATH = ROOT.join("assets/figures/manifest.yaml")
REPORT_PATH = ROOT.join("assets/figures/placement-audit.md")

MARGIN_WIDTH_MM = 45.0
MARGIN_HEIGHT_MIN_MM = 60.0
MARGIN_HEIGHT_MAX_MM = 80.0
MARGIN_HEIGHT_HARD_MAX_MM = 96.0
PT_TO_MM = 0.352778

VERTICAL_RELAYOUT = {
  "fig:interchange-flow" => "Простой линейный commission-flow из четырёх узлов можно свернуть в узкий top-down стек без потери смысла.",
  "fig:emv-chip-architecture" => "У схемы короткие подписи компонентов и одна локальная идея; её реально перерисовать как компактный вертикальный architectural sketch.",
  "fig:emv-dda-sequence" => "Участников всего двое, а цепочку доверия можно вынести в боковой rail, поэтому narrow vertical layout реалистичен.",
  "fig:emv-cryptogram-decision" => "Это один decision chain; его естественная форма для поля — узкая вертикаль сверху вниз.",
  "fig:contactless-protocol-stack" => "Стек уже концептуально вертикальный; нужен только более узкий набор подписей и более плотная упаковка слоёв.",
  "fig:token-detokenization-flow" => "Сюжет уже доказан в репо как пригодный к marginal flow: основной поток можно сделать вертикальным, а vault вынести sidecar-узлом.",
  "fig:crypto-hsm-flow" => "Это одна авторизационная ось с одним боковым HSM-узлом, хороший кандидат на top-down marginal flow.",
  "fig:crypto-dukpt" => "Деривация DUKPT — по сути одна цепочка сверху вниз; после сокращения подписей она может лечь в узкую вертикаль.",
  "fig:mc-ipm-structure" => "Структура `файл -> запись -> поля` естественно укладывается в короткий вертикальный stack.",
  "fig:mir-unionpay-routing" => "Routing tree компактный по идее и может быть переписан как узкое decision tree сверху вниз.",
  "fig:sbp-architecture" => "Трёхуровневая архитектура уже иерархична; её можно свести к top-down layout с краткими подписями.",
  "fig:pisp-flow" => "Flow можно свернуть в top-down сценарий с одним боковым блоком банка/SCA без потери основной логики.",
  "fig:fraud-hybrid" => "Это pipeline с одной главной осью и парой sidecar-узлов, хороший кандидат для маргинального vertical flow.",
  "fig:recon-exception-waterfall" => "Waterfall по смыслу уже top-down; в узкой вертикали он будет чище, чем в wide-flow.",
  "todo:ch26-payment-gateway:gateway-components" => "Gateway pipeline линейный; при сокращении подписей его можно сделать узкой вертикальной схемой с обратным ответом как side note."
}.freeze

MAIN_TEXT_OVERRIDES = {
  "fig:four-party-model" => "Топология держится на одновременном сравнении пяти равноправных ролей; узкая маргиналия исказит горизонтальные связи.",
  "fig:three-party-model" => "Контраст с четырёхсторонней моделью важен именно как широкая peer-to-peer topology, а не как узкая колонка.",
  "fig:token-tsp-comparison" => "Сравнение трёх TSP построено как параллельные колонки; без полной ширины теряется сама сравнительная идея.",
  "fig:crypto-key-hierarchy" => "Несколько ветвей, примеры PAN и уровни ключей требуют ширины для одновременного сравнения.",
  "fig:3ds-three-domains" => "Смысл схемы держится на параллельном сравнении трёх доменов, а не на одной вертикальной оси.",
  "fig:pci-saq-decision" => "Это разветвлённое decision tree с длинными исходами SAQ; узкое поле здесь не сохранит читаемость.",
  "fig:visanet-base-i-ii" => "Здесь критично сравнение двух плоскостей BASE I и BASE II; вертикализация ослабит архитектурный контраст.",
  "fig:opkc-flow" => "Три стадии с прямыми и обратными потоками лучше читаются как широкая фазовая схема.",
  "fig:sbp-scenarios" => "Гибрид матрицы и flow требует одновременного обзора строк, колонок и сценарного хвоста; поле для этого слишком узкое.",
  "fig:subscriptions-cit-mit" => "Дерево длинное, с несколькими типами MIT и пояснениями про 3DS/CVV/AVS/NTID; в поле потеряет читаемость.",
  "fig:decline-retry-tree" => "Важны точные code groups и retry-правила; для маргиналии слишком плотная логика и длинные листья."
}.freeze

def bbox_mm(pdf_path)
  output = `gs -q -sDEVICE=bbox -dBATCH -dNOPAUSE #{Shellwords.escape(pdf_path.to_s)} 2>&1`
  match = output.match(/%%HiResBoundingBox:\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)/)
  raise "Could not determine bounding box for #{pdf_path}" unless match

  x1, y1, x2, y2 = match.captures.map(&:to_f)
  {
    "width" => ((x2 - x1) * PT_TO_MM).round(1),
    "height" => ((y2 - y1) * PT_TO_MM).round(1)
  }
end

def main_text_reason(entry)
  overflow = entry["layout"] == "marginal-vertical" ? "Даже после vertical relayout " : ""
  return MAIN_TEXT_OVERRIDES.fetch(entry["id"]) if MAIN_TEXT_OVERRIDES.key?(entry["id"])

  case entry["kind"]
  when "comparison-table", "hybrid-matrix-flow"
    "#{overflow}таблица или матрица с несколькими колонками и полными заголовками требует ширины основного текста."
  when "sequence"
    "#{overflow}sequence diagram с несколькими участниками и подписями сообщений не читается в узком поле."
  when "timeline"
    "#{overflow}временная ось теряет смысл при сжатии до узкой маргиналии; фазы и подписи нужно видеть одновременно."
  when "decision-tree"
    "#{overflow}ветвление и длина leaf labels не укладываются в 45 мм без потери читаемости."
  when "topology-network"
    "#{overflow}параллельные подсистемы, зоны или уровни требуют одновременного обзора по ширине."
  else
    "#{overflow}число узлов и длина подписей делают схему слишком широкой или высокой для поля; безопаснее держать её в основном тексте."
  end
end

def margin_ok?(entry, dims)
  entry["layout"] == "marginal-vertical" &&
    dims["width"] <= MARGIN_WIDTH_MM &&
    dims["height"] <= MARGIN_HEIGHT_HARD_MAX_MM
end

def recommendation_for(entry, dims)
  if margin_ok?(entry, dims)
    {
      "recommendation" => "margin-ok",
      "target_layout" => "marginal-vertical",
      "reason" => if dims["height"] <= MARGIN_HEIGHT_MAX_MM
                    "Текущий vertical relayout уже помещается в узкую маргиналию и остаётся в типовом диапазоне высоты."
                  else
                    "Текущий vertical relayout уже помещается в узкую маргиналию; высота выше типовых 80 мм, но ещё приемлема для сложной схемы."
                  end
    }
  elsif VERTICAL_RELAYOUT.key?(entry["id"])
    {
      "recommendation" => "vertical-relayout-for-marginalia",
      "target_layout" => "marginal-vertical",
      "reason" => VERTICAL_RELAYOUT.fetch(entry["id"])
    }
  else
    {
      "recommendation" => "main-text",
      "target_layout" => entry["layout"],
      "reason" => main_text_reason(entry)
    }
  end
end

manifest = YAML.load_file(MANIFEST_PATH)

if manifest.empty?
  File.write(MANIFEST_PATH, manifest.to_yaml(line_width: -1))
  File.write(REPORT_PATH, <<~TEXT)
    # Figure Placement Audit

    - No active figure placeholders remain.
  TEXT
  puts "Updated #{MANIFEST_PATH.relative_path_from(ROOT)}"
  puts "Wrote #{REPORT_PATH.relative_path_from(ROOT)}"
  exit 0
end

manifest.each do |entry|
  dims = bbox_mm(ROOT.join(entry.fetch("pdf")))
  if VERTICAL_RELAYOUT.key?(entry["id"]) && dims["width"] <= MARGIN_WIDTH_MM
    entry["layout"] = "marginal-vertical"
  end

  recommendation = recommendation_for(entry, dims)

  entry["placement_review"] = {
    "bbox_mm" => dims,
    "marginalia_limits_mm" => {
      "width" => MARGIN_WIDTH_MM,
      "height_min" => MARGIN_HEIGHT_MIN_MM,
      "height_max" => MARGIN_HEIGHT_MAX_MM,
      "height_hard_max" => MARGIN_HEIGHT_HARD_MAX_MM
    },
    "fits_marginalia_now" => margin_ok?(entry, dims),
    "recommendation" => recommendation.fetch("recommendation"),
    "target_layout" => recommendation.fetch("target_layout"),
    "reason" => recommendation.fetch("reason")
  }
end

manifest.sort_by! { |entry| [entry["chapter_slug"], entry["planned_label"]] }

File.write(MANIFEST_PATH, manifest.to_yaml(line_width: -1))

counts = manifest.group_by { |entry| entry.dig("placement_review", "recommendation") }.transform_values(&:count)
smallest_width = manifest.min_by { |entry| entry.dig("placement_review", "bbox_mm", "width") }
widest = manifest.max_by { |entry| entry.dig("placement_review", "bbox_mm", "width") }
tallest = manifest.max_by { |entry| entry.dig("placement_review", "bbox_mm", "height") }

lines = []
lines << "# Figure Placement Audit"
lines << ""
lines << "- Margin target: width <= #{MARGIN_WIDTH_MM} mm, typical height #{MARGIN_HEIGHT_MIN_MM}-#{MARGIN_HEIGHT_MAX_MM} mm."
lines << "- Result now: #{manifest.count { |entry| entry.dig("placement_review", "fits_marginalia_now") }} of #{manifest.size} figures fit marginalia as generated."
lines << "- Smallest current width: `#{smallest_width["id"]}` at #{smallest_width.dig("placement_review", "bbox_mm", "width")} mm."
lines << "- Widest current figure: `#{widest["id"]}` at #{widest.dig("placement_review", "bbox_mm", "width")} mm."
lines << "- Tallest current figure: `#{tallest["id"]}` at #{tallest.dig("placement_review", "bbox_mm", "height")} mm."
lines << ""
lines << "## Summary"
lines << ""
lines << "- `margin-ok`: #{counts.fetch("margin-ok", 0)}"
lines << "- `main-text`: #{counts.fetch("main-text", 0)}"
lines << "- `vertical-relayout-for-marginalia`: #{counts.fetch("vertical-relayout-for-marginalia", 0)}"
lines << ""

[
  "margin-ok",
  "vertical-relayout-for-marginalia",
  "main-text"
].each do |bucket|
  lines << "## #{bucket}"
  lines << ""
  lines << "| id | bbox mm | target | reason |"
  lines << "|---|---:|---|---|"

  manifest.select { |entry| entry.dig("placement_review", "recommendation") == bucket }.each do |entry|
    dims = entry.dig("placement_review", "bbox_mm")
    lines << "| `#{entry["id"]}` | #{dims["width"]} x #{dims["height"]} | `#{entry.dig("placement_review", "target_layout")}` | #{entry.dig("placement_review", "reason")} |"
  end

  lines << ""
end

File.write(REPORT_PATH, lines.join("\n"))

puts "Updated #{MANIFEST_PATH.relative_path_from(ROOT)}"
puts "Wrote #{REPORT_PATH.relative_path_from(ROOT)}"
