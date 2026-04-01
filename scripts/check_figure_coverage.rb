#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "yaml"

ROOT = Pathname.new(__dir__).join("..").expand_path
manifest = YAML.load_file(ROOT.join("assets/figures/manifest.yaml"))

missing_tex = []
missing_pdf = []

manifest.each do |entry|
  tex = ROOT.join(entry.fetch("master_tex"))
  pdf = ROOT.join(entry.fetch("pdf"))
  missing_tex << entry["id"] unless tex.exist?
  missing_pdf << entry["id"] unless pdf.exist?
end

puts "manifest_entries=#{manifest.size}"
puts "missing_tex=#{missing_tex.size}"
missing_tex.each { |id| puts "  TEX #{id}" }
puts "missing_pdf=#{missing_pdf.size}"
missing_pdf.each { |id| puts "  PDF #{id}" }
