#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).join("..").expand_path
manifest = YAML.load_file(ROOT.join("assets/figures/manifest.yaml"))

errors = []
ids = manifest.map { |entry| entry["id"] }
errors << "Expected 42 manifest entries, got #{manifest.size}" unless manifest.size == 42
errors << "Duplicate figure ids detected" unless ids.uniq.size == ids.size

manifest.each do |entry|
  master = ROOT.join(entry.fetch("master_tex"))
  pdf = ROOT.join(entry.fetch("pdf"))
  errors << "Missing source #{master.relative_path_from(ROOT)}" unless master.exist?
  errors << "Missing pdf #{pdf.relative_path_from(ROOT)}" unless pdf.exist?
end

if errors.empty?
  puts "OK: #{manifest.size} manifest entries, all master_tex/pdf files exist."
else
  errors.each { |error| warn error }
  abort "Figure coverage check failed with #{errors.size} issue(s)."
end
