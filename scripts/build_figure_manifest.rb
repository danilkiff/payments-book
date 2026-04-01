#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).join("..").expand_path
MANIFEST_PATH = ROOT.join("assets/figures/manifest.yaml")

HOUSE_STYLE = <<~TEXT.strip
  House style: standalone TikZ/TeX figure for the main text of a serious technical book.
  Use Libertinus Sans, Ink #243042, Soft #F7F9FC, Panel #EEF4FB, AccentA #246BCE, AccentB #C8463A, Muted #5D6B7A.
  Lines must stay thin (0.5-0.65pt), corners slightly rounded (2.5-4pt), background white, at most two accent colors.
  No shadows, gradients, icons, logos, raster assets, decorative effects, or invented facts.
  Respect the exact labels, block order, flow direction, and terminology from the source placeholder.
  Output must be a compileable standalone .tex that produces a vector PDF ready for later embedding.
TEXT

PATTERNS = [
  /\\todo\[inline\]\{Рисунок:/,
  /% TODO: Рисунок:/,
  /% TODO\(figure\):/
].freeze

def chapter_title(lines)
  line = lines.find { |candidate| candidate.start_with?("\\chapter{") }
  return nil unless line

  line.sub(/^\\chapter\{/, "").sub(/\}\s*$/, "")
end

def extract_placeholder(lines, start_index)
  line = lines[start_index]

  if line.include?("\\todo[inline]{Рисунок:")
    block = []
    index = start_index
    brace_balance = 0
    while index < lines.length
      current = lines[index]
      block << current.rstrip
      brace_balance += current.count("{")
      brace_balance -= current.count("}")
      break if brace_balance <= 0

      index += 1
    end
    return block
  end

  block = []
  index = start_index
  while index < lines.length
    current = lines[index]
    break unless current.lstrip.start_with?("%")
    break if index > start_index && current.include?("\\label{fig:")

    block << current.rstrip
    index += 1
  end
  block
end

def clean_placeholder(block)
  block.map do |line|
    stripped = line.sub(/^\s*%+\s?/, "")
    stripped = stripped.sub(/^TODO:\s*Рисунок:\s*/, "")
    stripped = stripped.sub(/^TODO\(figure\):\s*/, "")
    stripped = stripped.sub(/^\\todo\[inline\]\{Рисунок:\s*/, "")
    stripped = stripped.sub(/^Рисунок:\s*/, "")
    stripped = stripped.sub(/\}\s*$/, "")
    stripped.rstrip
  end.join("\n").strip
end

def find_label(lines, start_index)
  ((start_index + 1)...[start_index + 24, lines.length].min).each do |index|
    match = lines[index].match(/\\label\{(fig:[^}]+)\}/)
    return match[1] if match
  end
  nil
end

def infer_kind(text)
  case text
  when /Sequence diagram|sequence diagram|sequence/i
    "sequence"
  when /Decision tree|Дерево|дерево решений|дерево маршрутизации/i
    "decision-tree"
  when /Матрица.*flow|matrix.*flow|матрица.*сценариев/i
    "hybrid-matrix-flow"
  when /Таблица|таблица|Матрица|матрица|comparison/i
    "comparison-table"
  when /шкала|timeline|временн/i
    "timeline"
  when /тополог|архитектур|сетевая диаграмма|stack|стек протоколов|границ CDE|трёхуровневая схема|IPM-файла/i
    "topology-network"
  else
    "flow-wide"
  end
end

def infer_layout(kind, text)
  return "main-table" if kind == "comparison-table"
  return "main-vertical" if kind == "decision-tree"
  return "main-wide" if %w[sequence hybrid-matrix-flow].include?(kind)
  return "main-wide" if text.match?(/Горизонтальн|горизонтальн|слева направо|left-to-right/i)

  if text.match?(/Вертикальн|вертикальн|сверху вниз|vertical/i)
    "main-vertical"
  else
    "main-wide"
  end
end

def figure_slug_for(label, source_tex)
  return label.delete_prefix("fig:") if label
  return "gateway-components" if source_tex.end_with?("ch26-payment-gateway.tex")

  raise "Missing planned figure slug for #{source_tex}"
end

def entry_prompt(kind:, cleaned_text:, planned_label:, source_tex:, layout:)
  <<~TEXT.strip
    Figure ID: #{planned_label}
    Source file: #{source_tex}
    Figure family: #{kind}
    Layout: #{layout}

    Source placeholder:
    #{cleaned_text}

    #{HOUSE_STYLE}
  TEXT
end

entries = []

Dir[ROOT.join("src/parts/**/*.tex").to_s].sort.each do |path|
  relative_path = Pathname.new(path).relative_path_from(ROOT).to_s
  lines = File.readlines(path, chomp: false)
  chapter_slug = File.basename(path, ".tex")
  chapter = chapter_title(lines) || chapter_slug

  lines.each_with_index do |line, index|
    next unless PATTERNS.any? { |pattern| line.match?(pattern) }

    label = find_label(lines, index)
    id = label
    planned_label = label

    if planned_label.nil?
      id = "todo:#{chapter_slug}:gateway-components"
      planned_label = "fig:gateway-components"
    end

    placeholder = extract_placeholder(lines, index)
    cleaned_text = clean_placeholder(placeholder)
    kind = infer_kind(cleaned_text)
    layout = infer_layout(kind, cleaned_text)
    figure_slug = figure_slug_for(label, relative_path)
    asset_base = "assets/figures/#{chapter_slug}/#{figure_slug}"

    entries << {
      "id" => id,
      "planned_label" => planned_label,
      "source_tex" => relative_path,
      "source_locator" => {
        "line" => index + 1,
        "excerpt" => cleaned_text.lines.first.to_s.strip
      },
      "chapter" => chapter,
      "chapter_slug" => chapter_slug,
      "kind" => kind,
      "layout" => layout,
      "asset_base" => asset_base,
      "master_tex" => "#{asset_base}.tex",
      "pdf" => "#{asset_base}.pdf",
      "prompt" => entry_prompt(
        kind: kind,
        cleaned_text: cleaned_text,
        planned_label: planned_label,
        source_tex: relative_path,
        layout: layout
      ),
      "status" => "planned"
    }
  end
end

raise "Expected 42 figure entries, got #{entries.size}" unless entries.size == 42

ids = entries.map { |entry| entry["id"] }
raise "Duplicate figure ids detected" unless ids.uniq.size == ids.size

MANIFEST_PATH.dirname.mkpath
File.write(MANIFEST_PATH, entries.to_yaml(line_width: -1))

puts "Wrote #{entries.size} manifest entries to #{MANIFEST_PATH.relative_path_from(ROOT)}"
