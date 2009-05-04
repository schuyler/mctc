from apps.reusable_tables.table import register
from apps.mctc.models.general import Case

from apps.mctc.models.logs import MessageLog, EventLog
from apps.mctc.models.general import Case, Zone, Provider
from apps.mctc.models.reports import ReportMalnutrition, ReportMalaria, ReportDiagnosis

register("case", Case, [
        ["Id", "ref_id", "{{ object.ref_id }}"],
        ["Name", "last_name", "{{ object.first_name }} {{ object.last_name }}"],
        ["Gender", "gender", "{{ object.gender }}"],
		["Age", "age", "{{ object.age }}"],
        ["Provider", "provider", "{{ object.provider.get_name_display }}"],
        ["Zone", "zone", "{{ object.zone }}"],
        ])

register("message", MessageLog, [
        ["About", "mobile", "{{ object.mobile }}"],
        ["Message", "text", "{{ object.text }}"],
        ["Sent by", "sent_by", "{{ object.sent_by }}"],        
        ["Created", "created_at", '{{ object.created_at|date:"d/m/Y" }}'],
        ["Handled", "handled", "{{ object.get_handled_display }}"]
        ])

register("event", EventLog, [
        ["About", "content_object", "{{ object.content_object }}"],
        ["Message", "message", "{{ object.get_message_display }}"],
        ["Created", "entered_at", '{{ object.created_at|date:"d/m/Y" }}'],
        ["Type", "content_type", "{{ object.content_type }}"]
        ])

register("malnutrition", ReportMalnutrition, [
        ["Status", "status", "{{ object.get_status_display }}"],
        ["MUAC", "muac", "{{ object.muac }}"],
        ["Weight", "weight", "{{ object.weight }}"],
        ["Height", "height", "{{ object.height }}"],
        ["Provider", "provider", "{{ object.provider.get_name_display }}"],
        ["Created", "entered_at", '{{ object.entered_at|date:"d/m/Y" }}']
        ])

register("diagnosis", ReportDiagnosis, [
        ["Text", "status", "{{ object.text }}"],
        ["Diagnosis", "muac", "{{ object.get_dictionary.diagnosis }}"],
        ["Labs", "weight", "{{ object.get_dictionary.labs }}"],
        ["Provider", "provider", "{{ object.provider.get_name_display }}"],
        ["Created", "entered_at", '{{ object.entered_at|date:"d/m/Y" }}']
        ])

register("malaria", ReportMalaria, [
        ["Result", "result", "{{ object.result }}"],
        ["Bednet", "bednet", "{{ object.bednet }}"],
        ["Symptoms", "observed", "{{ object.get_dictionary.observed }}"],
        ["Provider", "provider", "{{ object.provider.get_name_display }}"],
        ["Created", "entered_at", '{{ object.entered_at|date:"d/m/Y" }}']
        ])

register("provider", Provider, [
        ["User", "user", "{{ object.user }}"],
		["Role", "role", "{{ object.role}}"],
		["First Name", "first_name", "{{ object.user.first_name }}"],
        ["Mobile", "mobile", "{{ object.mobile }}"],
        ["Role", "diagnosis", "{{ object.role }}"],
        ["Active", "active", "{{ object.get_active_display }}"],
        ["Alerts", "alerts", '{{ object.alerts }}'],
        ["Clinic", "clinic", '{{ object.clinic }}']
        ])