module "domain_events" {
  source      = "../../modules/domain_events"
  name_prefix = local.name_prefix
}
output "domain_event_bus_name" { value = module.domain_events.name }
output "domain_event_bus_arn" { value = module.domain_events.arn }
