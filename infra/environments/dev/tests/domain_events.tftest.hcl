mock_provider "aws" {}
run "domain_bus_contract" {
  command = plan
  module { source = "../../modules/domain_events" }
  variables { name_prefix = "docflow-dev" }
  assert {
    condition     = aws_cloudwatch_event_bus.this.name == "docflow-dev-domain" && aws_cloudwatch_event_bus.this.event_source_name == null
    error_message = "Create a dedicated custom domain bus, not a default or partner bus."
  }
}
run "domain_publisher_wiring" {
  command = plan
  override_module {
    target  = module.domain_events
    outputs = { name = "docflow-dev-domain", arn = "arn:aws:events:us-east-1:123456789012:event-bus/docflow-dev-domain" }
  }
  assert {
    condition     = module.outbox_publisher.domain_bus_arn == "arn:aws:events:us-east-1:123456789012:event-bus/docflow-dev-domain" && module.outbox_publisher.outbox_stream_enabled
    error_message = "Publisher must use actual domain module output and enable stream ingestion."
  }
  assert {
    condition     = output.domain_event_bus_name == "docflow-dev-domain" && output.domain_event_bus_arn == module.domain_events.arn
    error_message = "Expose the provisioned bus name and ARN."
  }
}
