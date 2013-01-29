#!/usr/bin/env ruby
# ruby script that converts a nagios status.dat file to domino alerts

require 'nagios_analyzer'
require 'pp'
require 'json'
require 'open-uri'
require 'httparty'
require 'syslog'

# init variables
$status_file = ARGV[0]
$search = ARGV[1]
$my_colo = ARGV[2]

if File.exists? "/opt/domino/raven/raven.conf"
  $raven_config = "/opt/domino/raven/raven.conf"
elsif File.exists? "/usr/local/nagios/etc/raven.conf"
  $raven_config = "/usr/local/nagios/etc/raven.conf"
else
  puts "No raven config"
  exit 1
end 

if File.exists? "/opt/domino/raven/raven"
  $raven_exec = "/opt/domino/raven/raven"
elsif File.exists? "/usr/local/nagios/bin/raven"
  $raven_exec = "/usr/local/nagios/bin/raven"
else
  puts "No raven exec"
  exit 1
end

def log(message)
  Syslog.open($0, Syslog::LOG_PID | Syslog::LOG_CONS) { |s| s.warning message }
  puts message
end

# delete alerts from domino that are no longer in status.dat
puts "Looking for abandoned services/hosts"
puts "Getting domino data"
dom_raw = HTTParty.get("http://domino.ops.brightcove.com/api/alert?limit=0&search=#{$search}").body
dom_data = JSON.parse(dom_raw)

puts "Loading status.dat file"
status = NagiosAnalyzer::Status.new($status_file, :include_ok => true)
dom_data.each do | d | 
  if d['service'] == ''
    t = status.items.detect {|i| ( i[:host_name] == "#{d['host']}.#{$my_colo}" or i[:host_name] == "#{d['host']}" ) and i[:type] == "hoststatus" }
  else
    t = status.items.detect {|i| ( i[:host_name] == "#{d['host']}.#{$my_colo}" or i[:host_name] == "#{d['host']}" ) and i[:service_description] == d['service'] }
  end
  if t.nil? or t.empty?
    if d['service'] == ''
      url = "http://domino.ops.brightcove.com/api/alert?search=colo:#{d['colo']}+host:#{d['host']}+environment:#{d['environment']}"
    else
      url = "http://domino.ops.brightcove.com/api/alert?search=colo:#{d['colo']}+host:#{d['host']}+service:#{d['service']}+environment:#{d['environment']}"
    end
    url = URI.encode(url)
    log("Deleting #{d['colo']} >> #{d['host']} >> #{d['service']}")
    HTTParty.delete(url)
  end 
end

# upload to missing alerts from domino from status
puts "Looking for missing/outdated alerts"
def upDom(entities)
  # reload status.dat and domino data each time to ensure we're working with near "live" data
  puts "Loading domino data"
  dom_raw = HTTParty.get("http://domino.ops.brightcove.com/api/alert?limit=0&search=#{$search}").body
  dom_data = JSON.parse(dom_raw)
  puts "Loading status.dat"
  status = NagiosAnalyzer::Status.new($status_file, :include_ok => true)
  entities.delete_if do | e |
    e = e.hash
    if e[:type] == "hoststatus"
      obj = status.items.detect {|i| i[:host_name] == e[:host_name] and i[:type] == "hoststatus" }
    else
      obj = status.items.detect {|i| i[:host_name] == e[:host_name] and i[:service_description] == e[:service_description] }
    end
    # skip checking this service/host due to the data we have being stale
    if (obj[:next_check] + 10) <= Time.now.to_i
      if obj[:next_check] == 0 or obj[:active_checks_enabled] == 0
        # its a passive check, so i can't know for sure if this data is valid
        true
      else
        false
      end
    else
      # kill domain if exists on host name
      if obj[:host_name].end_with? ".#{$my_colo}"
        obj[:host_name] = obj[:host_name].split(".#{$my_colo}")[0]
      end
      # get tags
      if obj[:_TAGS].nil? or obj[:_TAGS] =~ /;$/
        tags = ''
      else
        tags = obj[:_TAGS].split(';')[-1]
      end
      if obj[:type] == "servicestatus"
        v = "#{$raven_exec} -c #{$raven_config} -H '#{obj[:host_name]}' -v '#{obj[:service_description]}' -s '#{obj[:status]}' -T'nagios,service,#{tags}' << EOF
#{obj[:plugin_output]}
#{obj[:long_plugin_output]}
EOF"
      elsif obj[:type] == "hoststatus"
        obj[:service_description] = ''
        v = "#{$raven_exec} -c #{$raven_config} -H '#{obj[:host_name]}' -v '' -s '#{obj[:status]}' -T 'nagios,host,#{tags}' << EOF
#{obj[:plugin_output]}
#{obj[:long_plugin_output]}
EOF"
      end
      if obj[:type] == "hoststatus"
        t = dom_data.detect {|i| i['host'] == "#{obj[:host_name]}" and i['service'] == "" }
      else
        t = dom_data.detect {|i| i['host'] == "#{obj[:host_name]}" and i['service'] == "#{obj[:service_description]}" }
      end
      if t.nil? or ( obj[:status].downcase != t['status'].downcase and obj[:last_hard_state] == obj[:current_state] )
        log("Adding missing alert") if t.nil?
        log("updating old alert data") if ! t.nil? and obj[:status] != t['status']
        log("Sending alert: #{obj[:host_name]} >> #{obj[:service_description]}")
        v = `#{v}` if ! v.nil?
      end
      true
    end
  end
  return entities
end

# load a list of hosts and services to check
entities = NagiosAnalyzer::Status.new($status_file, :include_ok => true)
entities.scopes << lambda{|s| s.start_with?("hoststatus") or s.start_with?("servicestatus") }
entities.reset_cache!
entities = entities.items.sort_by { |k| k[:next_check] }

while entities.length > 0
  puts "Starting... (#{entities.length} remaining)"
  entities = upDom entities
end

