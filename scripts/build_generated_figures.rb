#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "open3"
require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).join("..").expand_path
MANIFEST_PATH = ROOT.join("assets/figures/manifest.yaml")

unless MANIFEST_PATH.exist?
  abort "Manifest not found at #{MANIFEST_PATH}"
end

entries = YAML.load_file(MANIFEST_PATH)
filters = ARGV

selected = entries.select do |entry|
  next true if filters.empty?

  filters.include?(entry["chapter_slug"]) ||
    filters.include?(entry["id"]) ||
    filters.include?(entry["planned_label"])
end

if selected.empty?
  if filters.empty?
    puts "No active figure placeholders remain."
    exit 0
  end

  abort "No manifest entries matched filters: #{filters.join(', ')}"
end

selected.each do |entry|
  master_tex = ROOT.join(entry.fetch("master_tex"))
  expected_pdf = ROOT.join(entry.fetch("pdf"))

  unless master_tex.exist?
    warn "Skipping missing source: #{master_tex.relative_path_from(ROOT)}"
    next
  end

  figure_dir = master_tex.dirname
  build_dir = figure_dir.join("build")
  build_dir.mkpath

  basename = master_tex.basename(".tex").to_s
  command = ["latexmk", "-xelatex", "-silent", "-outdir=build", "#{basename}.tex"]

  stdout, stderr, status = Open3.capture3(*command, chdir: figure_dir.to_s)
  unless status.success?
    warn stdout unless stdout.empty?
    warn stderr unless stderr.empty?
    abort "Failed to build #{master_tex.relative_path_from(ROOT)}"
  end

  built_pdf = build_dir.join("#{basename}.pdf")
  abort "Expected PDF missing after build: #{built_pdf}" unless built_pdf.exist?

  FileUtils.cp(built_pdf, expected_pdf)
  puts "Built #{expected_pdf.relative_path_from(ROOT)}"
end
